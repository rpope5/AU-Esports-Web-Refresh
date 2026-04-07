"""
Offline analysis starter for recruit ranking export data.

This script is intentionally offline-only and does not modify production scoring.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


POSITIVE_TRIAGE_STATUSES = {"ACCEPTED", "WATCHLIST", "TRYOUT"}
POSITIVE_ACCEPTED_ONLY_STATUSES = {"ACCEPTED"}
KNOWN_STATUSES = {
    "NEW",
    "REVIEWED",
    "CONTACTED",
    "TRYOUT",
    "WATCHLIST",
    "ACCEPTED",
    "REJECTED",
}
DEFAULT_THRESHOLDS = [50.0, 60.0, 70.0, 80.0, 90.0]


@dataclass
class ParsedRow:
    application_id: int
    game_slug: str
    review_status: str
    score: float | None
    scored_at: str | None
    submitted_at: str | None
    label_reason: str | None
    normalized_features: dict[str, Any]
    raw: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline recruit ranking/training analysis using admin export JSON."
    )
    parser.add_argument("--input-file", type=Path)
    parser.add_argument("--api-base-url", type=str)
    parser.add_argument(
        "--token",
        type=str,
        default=os.getenv("AU_ADMIN_TOKEN"),
        help="Admin bearer token (or set AU_ADMIN_TOKEN env var).",
    )
    parser.add_argument("--game-slug", type=str, default=None)
    parser.add_argument("--status", type=str, default=None)
    parser.add_argument("--submitted-from", type=str, default=None)
    parser.add_argument("--submitted-to", type=str, default=None)
    parser.add_argument("--limit", type=int, default=2000)
    parser.add_argument(
        "--target-mode",
        choices=["triage_positive", "accepted_only"],
        default="triage_positive",
    )
    parser.add_argument("--run-logistic", action="store_true")
    parser.add_argument("--min-game-sample", type=int, default=5)
    parser.add_argument("--norm-min-coverage", type=float, default=0.3)
    parser.add_argument("--max-norm-features", type=int, default=10)
    parser.add_argument("--weak-game-count", type=int, default=3)
    parser.add_argument("--output-json", type=Path, default=None)
    return parser.parse_args()


def fetch_export_from_api(args: argparse.Namespace) -> dict[str, Any]:
    if not args.api_base_url:
        raise ValueError("Missing --api-base-url when --input-file is not provided.")
    if not args.token:
        raise ValueError("Missing admin token. Pass --token or set AU_ADMIN_TOKEN.")

    query = {"limit": args.limit}
    if args.game_slug:
        query["game_slug"] = args.game_slug
    if args.status:
        query["status"] = args.status
    if args.submitted_from:
        query["submitted_from"] = args.submitted_from
    if args.submitted_to:
        query["submitted_to"] = args.submitted_to

    base = args.api_base_url.rstrip("/")
    url = f"{base}/api/v1/admin/recruits/export/training?{urlencode(query)}"
    req = Request(
        url,
        headers={"Authorization": f"Bearer {args.token}", "Accept": "application/json"},
        method="GET",
    )
    with urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def load_export_data(args: argparse.Namespace) -> dict[str, Any]:
    if args.input_file:
        with args.input_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    return fetch_export_from_api(args)


def to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def parse_rows(payload: dict[str, Any]) -> list[ParsedRow]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Invalid export format: expected top-level 'rows' list.")

    parsed: list[ParsedRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        application_id = row.get("application_id")
        game_slug = row.get("game_slug")
        if not isinstance(application_id, int) or not isinstance(game_slug, str):
            continue

        review_status = row.get("review_status")
        if not isinstance(review_status, str):
            review_status = "NEW"
        review_status = review_status.upper()
        if review_status not in KNOWN_STATUSES:
            review_status = "NEW"

        score = to_float(row.get("score"))
        normalized = row.get("normalized_features_json")
        if not isinstance(normalized, dict):
            normalized = {}

        parsed.append(
            ParsedRow(
                application_id=application_id,
                game_slug=game_slug,
                review_status=review_status,
                score=score,
                scored_at=row.get("scored_at"),
                submitted_at=row.get("submitted_at"),
                label_reason=row.get("label_reason"),
                normalized_features=normalized,
                raw=row,
            )
        )
    return parsed


def pct(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return (part / total) * 100.0


def quantile(sorted_values: list[float], q: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return sorted_values[low]
    frac = pos - low
    return sorted_values[low] * (1 - frac) + sorted_values[high] * frac


def summarize_score_distribution(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "min": None, "max": None, "p25": None, "p75": None}
    sorted_values = sorted(values)
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), 4),
        "median": round(statistics.median(values), 4),
        "min": round(sorted_values[0], 4),
        "max": round(sorted_values[-1], 4),
        "p25": round(quantile(sorted_values, 0.25) or 0.0, 4),
        "p75": round(quantile(sorted_values, 0.75) or 0.0, 4),
    }


def summarize_numeric(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "std": None}
    std = statistics.pstdev(values) if len(values) > 1 else 0.0
    return {"n": len(values), "mean": round(statistics.fmean(values), 4), "median": round(statistics.median(values), 4), "std": round(std, 4)}


def target_value(status: str, mode: str) -> int:
    if mode == "accepted_only":
        return 1 if status in POSITIVE_ACCEPTED_ONLY_STATUSES else 0
    return 1 if status in POSITIVE_TRIAGE_STATUSES else 0


def auc_from_scores(y_true: list[int], y_score: list[float]) -> float | None:
    if len(y_true) != len(y_score) or not y_true:
        return None
    pos = sum(1 for y in y_true if y == 1)
    neg = len(y_true) - pos
    if pos == 0 or neg == 0:
        return None
    pairs = sorted(zip(y_score, y_true), key=lambda x: x[0])
    rank_sum_pos = 0.0
    i = 0
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + j + 1) / 2.0
        for k in range(i, j):
            if pairs[k][1] == 1:
                rank_sum_pos += avg_rank
        i = j
    auc = (rank_sum_pos - (pos * (pos + 1) / 2.0)) / (pos * neg)
    return round(auc, 4)


def threshold_metrics(y_true: list[int], y_score: list[float], threshold: float) -> dict[str, float | int]:
    tp = fp = tn = fn = 0
    for y, s in zip(y_true, y_score):
        pred = 1 if s >= threshold else 0
        if pred == 1 and y == 1:
            tp += 1
        elif pred == 1 and y == 0:
            fp += 1
        elif pred == 0 and y == 0:
            tn += 1
        else:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    hit_rate = (tp + fp) / len(y_true) if y_true else 0.0
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "hit_rate_pct": round(hit_rate * 100.0, 2),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
    }


def compare_rules_score(rows: list[ParsedRow], mode: str) -> dict[str, Any]:
    labeled_rows = [r for r in rows if isinstance(r.score, float)]
    y_true = [target_value(r.review_status, mode) for r in labeled_rows]
    y_score = [r.score for r in labeled_rows if r.score is not None]
    positives = sum(y_true)
    negatives = len(y_true) - positives
    pos_scores = [s for y, s in zip(y_true, y_score) if y == 1]
    neg_scores = [s for y, s in zip(y_true, y_score) if y == 0]

    return {
        "target_mode": mode,
        "rows_with_score": len(labeled_rows),
        "positives": positives,
        "negatives": negatives,
        "positive_rate_pct": round(pct(positives, len(y_true)), 2) if y_true else 0.0,
        "positive_score_summary": summarize_score_distribution(pos_scores),
        "negative_score_summary": summarize_score_distribution(neg_scores),
        "score_auc_vs_target": auc_from_scores(y_true, y_score),
        "threshold_table": [threshold_metrics(y_true, y_score, t) for t in DEFAULT_THRESHOLDS],
    }


def label_distribution_by_game(rows: list[ParsedRow]) -> dict[str, Any]:
    by_game: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_game[row.game_slug][row.review_status] += 1

    result: dict[str, Any] = {}
    for game, counter in sorted(by_game.items()):
        total = sum(counter.values())
        result[game] = {
            "total": total,
            "status_counts": dict(counter),
            "status_pct": {status: round(pct(count, total), 2) for status, count in counter.items()},
        }
    return result


def score_distribution_by_status(rows: list[ParsedRow]) -> dict[str, Any]:
    by_status: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.score is not None:
            by_status[row.review_status].append(row.score)

    result: dict[str, Any] = {}
    for status in sorted(KNOWN_STATUSES):
        result[status] = summarize_score_distribution(by_status.get(status, []))
    return result


def per_game_triage_evaluation(rows: list[ParsedRow], min_game_sample: int, weak_game_count: int) -> dict[str, Any]:
    by_game_rows: dict[str, list[ParsedRow]] = defaultdict(list)
    for row in rows:
        if row.score is not None:
            by_game_rows[row.game_slug].append(row)

    by_game: dict[str, Any] = {}
    auc_candidates: list[tuple[str, float, int]] = []

    for game, game_rows in sorted(by_game_rows.items()):
        y_true = [target_value(r.review_status, "triage_positive") for r in game_rows]
        y_score = [float(r.score) for r in game_rows if r.score is not None]
        positives = sum(y_true)
        negatives = len(y_true) - positives
        score_auc = auc_from_scores(y_true, y_score)
        score_distribution = summarize_score_distribution(y_score)
        threshold_table = [threshold_metrics(y_true, y_score, t) for t in DEFAULT_THRESHOLDS]

        auc_is_comparable = len(game_rows) >= min_game_sample and positives > 0 and negatives > 0 and score_auc is not None
        if auc_is_comparable:
            auc_candidates.append((game, score_auc, len(game_rows)))

        by_game[game] = {
            "sample_size": len(game_rows),
            "positives": positives,
            "negatives": negatives,
            "positive_rate_pct": round(pct(positives, len(game_rows)), 2),
            "triage_positive_auc": score_auc,
            "auc_comparable": auc_is_comparable,
            "score_distribution": score_distribution,
            "threshold_hit_rates": threshold_table,
        }

    auc_candidates.sort(key=lambda item: item[1], reverse=True)
    strongest = [{"game": game, "auc": auc, "sample_size": n} for game, auc, n in auc_candidates[:3]]
    weakest = [
        {"game": game, "auc": auc, "sample_size": n}
        for game, auc, n in sorted(auc_candidates, key=lambda item: item[1])[:weak_game_count]
    ]

    return {
        "min_game_sample_for_comparable_auc": min_game_sample,
        "by_game": by_game,
        "strongest_games_by_auc": strongest,
        "weakest_games_by_auc": weakest,
    }


def extract_component_contributions(row: ParsedRow) -> dict[str, float]:
    explanation = row.raw.get("explanation_json")
    if not isinstance(explanation, dict):
        return {}
    components = explanation.get("components")
    if not isinstance(components, dict):
        return {}

    out: dict[str, float] = {}
    for name, payload in components.items():
        if not isinstance(payload, dict):
            continue
        contribution = to_float(payload.get("contribution"))
        if contribution is None:
            continue
        out[str(name)] = contribution
    return out


def row_numeric_normalized_features(row: ParsedRow) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, value in row.normalized_features.items():
        numeric = to_float(value)
        if numeric is not None:
            out[str(key)] = numeric
    return out


def compute_group_separation(pos_rows: list[ParsedRow], neg_rows: list[ParsedRow], extractor: callable, label: str) -> list[dict[str, Any]]:
    pos_values: dict[str, list[float]] = defaultdict(list)
    neg_values: dict[str, list[float]] = defaultdict(list)

    for row in pos_rows:
        for key, value in extractor(row).items():
            pos_values[key].append(value)
    for row in neg_rows:
        for key, value in extractor(row).items():
            neg_values[key].append(value)

    all_keys = set(pos_values.keys()) | set(neg_values.keys())
    output: list[dict[str, Any]] = []
    for key in all_keys:
        pos = pos_values.get(key, [])
        neg = neg_values.get(key, [])
        pos_summary = summarize_numeric(pos)
        neg_summary = summarize_numeric(neg)
        pos_mean = pos_summary["mean"]
        neg_mean = neg_summary["mean"]

        if pos_mean is None or neg_mean is None:
            delta = None
        else:
            delta = round(float(pos_mean) - float(neg_mean), 4)

        pos_std = float(pos_summary["std"]) if pos_summary["std"] is not None else 0.0
        neg_std = float(neg_summary["std"]) if neg_summary["std"] is not None else 0.0
        pooled_std = math.sqrt((pos_std**2 + neg_std**2) / 2.0) if (pos_std or neg_std) else 0.0
        effect_size = round(delta / pooled_std, 4) if delta is not None and pooled_std > 0 else None

        signal = "insufficient"
        if delta is not None:
            abs_delta = abs(delta)
            abs_effect = abs(effect_size) if effect_size is not None else 0.0
            if abs_delta >= 5.0 and abs_effect >= 0.5:
                signal = "strong"
            elif abs_delta < 2.0 or abs_effect < 0.2:
                signal = "weak"
            else:
                signal = "moderate"

        inconsistent = False
        if delta is not None and effect_size is not None:
            inconsistent = abs(delta) >= 2.0 and abs(effect_size) < 0.3 and (pos_std + neg_std) > 8.0

        output.append(
            {
                label: key,
                "positive_summary": pos_summary,
                "negative_summary": neg_summary,
                "delta_positive_minus_negative": delta,
                "effect_size": effect_size,
                "signal": signal,
                "inconsistent": inconsistent,
            }
        )

    output.sort(
        key=lambda row: abs(row["delta_positive_minus_negative"]) if row["delta_positive_minus_negative"] is not None else -1.0,
        reverse=True,
    )
    return output


def top_mean_items(rows: list[ParsedRow], extractor: callable, label: str, top_n: int = 6) -> list[dict[str, Any]]:
    values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for key, val in extractor(row).items():
            values[key].append(val)

    ranked: list[dict[str, Any]] = []
    for key, vals in values.items():
        summary = summarize_numeric(vals)
        if summary["mean"] is None:
            continue
        ranked.append({label: key, "mean": summary["mean"], "median": summary["median"], "std": summary["std"], "n": summary["n"]})
    ranked.sort(key=lambda row: row["mean"], reverse=True)
    return ranked[:top_n]


def status_component_means(rows: list[ParsedRow]) -> dict[str, dict[str, float]]:
    by_status_component: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for comp, contrib in extract_component_contributions(row).items():
            by_status_component[row.review_status][comp].append(contrib)

    result: dict[str, dict[str, float]] = {}
    for status, comp_map in by_status_component.items():
        means: dict[str, float] = {}
        for comp, vals in comp_map.items():
            if vals:
                means[comp] = round(statistics.fmean(vals), 4)
        result[status] = dict(sorted(means.items(), key=lambda kv: kv[0]))
    return result


def diagnose_game(rows: list[ParsedRow], game_slug: str) -> dict[str, Any]:
    game_rows = [r for r in rows if r.game_slug == game_slug and r.score is not None]
    positive_rows = [r for r in game_rows if target_value(r.review_status, "triage_positive") == 1]
    negative_rows = [r for r in game_rows if target_value(r.review_status, "triage_positive") == 0]
    rejected_rows = [r for r in game_rows if r.review_status == "REJECTED"]

    component_sep = compute_group_separation(positive_rows, negative_rows, extract_component_contributions, "component")
    feature_sep = compute_group_separation(positive_rows, negative_rows, row_numeric_normalized_features, "feature")

    useful_components = [row for row in component_sep if row["signal"] == "strong"][:5]
    weak_components = [row for row in component_sep if row["signal"] == "weak"][:5]
    inconsistent_components = [row for row in component_sep if row["inconsistent"]][:5]
    components_favoring_negative = [
        row for row in component_sep if row["delta_positive_minus_negative"] is not None and row["delta_positive_minus_negative"] < 0
    ][:5]

    useful_features = [row for row in feature_sep if row["signal"] == "strong"][:5]
    weak_features = [row for row in feature_sep if row["signal"] == "weak"][:5]

    return {
        "game": game_slug,
        "sample_size": len(game_rows),
        "positive_sample_size": len(positive_rows),
        "negative_sample_size": len(negative_rows),
        "rejected_sample_size": len(rejected_rows),
        "average_component_contribution_by_status": status_component_means(game_rows),
        "top_components_for_triage_positive": top_mean_items(positive_rows, extract_component_contributions, "component"),
        "top_components_for_rejected": top_mean_items(rejected_rows, extract_component_contributions, "component"),
        "component_distribution_positive_vs_negative": component_sep,
        "normalized_feature_distribution_positive_vs_negative": feature_sep,
        "most_useful_components": useful_components,
        "least_useful_components": weak_components,
        "inconsistent_components": inconsistent_components,
        "components_favoring_negative": components_favoring_negative,
        "most_useful_normalized_features": useful_features,
        "least_useful_normalized_features": weak_features,
    }


def weak_game_diagnostics(rows: list[ParsedRow], per_game_eval: dict[str, Any]) -> dict[str, Any]:
    weakest = per_game_eval.get("weakest_games_by_auc", [])
    weak_game_slugs = [row["game"] for row in weakest if isinstance(row, dict) and "game" in row]
    diagnostics = {game: diagnose_game(rows, game) for game in weak_game_slugs}
    return {
        "positive_definition": sorted(POSITIVE_TRIAGE_STATUSES),
        "negative_definition": "all non-triage-positive statuses",
        "rejected_focus": "REJECTED-only subgroup used for top rejected-component summaries",
        "games": weak_game_slugs,
        "by_game": diagnostics,
    }


def select_numeric_normalized_feature_keys(rows: list[ParsedRow], min_coverage_ratio: float, max_features: int) -> list[dict[str, Any]]:
    total_rows = len(rows)
    numeric_counts: Counter[str] = Counter()
    numeric_values: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        for key, value in row.normalized_features.items():
            numeric = to_float(value)
            if numeric is None:
                continue
            numeric_counts[key] += 1
            numeric_values[key].append(numeric)

    candidates: list[dict[str, Any]] = []
    for key, count in numeric_counts.items():
        coverage = (count / total_rows) if total_rows else 0.0
        if coverage < min_coverage_ratio:
            continue
        vals = numeric_values[key]
        variance = statistics.pvariance(vals) if len(vals) > 1 else 0.0
        candidates.append({"key": key, "count": count, "coverage_ratio": round(coverage, 4), "variance": round(float(variance), 6)})

    candidates.sort(key=lambda row: (row["count"], row["variance"], row["key"]), reverse=True)
    return candidates[:max_features]


def run_optional_logistic(rows: list[ParsedRow], mode: str, args: argparse.Namespace) -> dict[str, Any]:
    try:
        from sklearn.feature_extraction import DictVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import confusion_matrix, precision_score, recall_score, roc_auc_score
        from sklearn.model_selection import train_test_split
    except ImportError:
        return {"ran": False, "reason": "scikit-learn not installed. Install it in the analysis environment to enable this step."}

    labeled_rows = [r for r in rows if r.score is not None]
    if len(labeled_rows) < 30:
        return {"ran": False, "reason": "Not enough rows with score for a stable train/test split (need ~30+)."}

    feature_candidates = select_numeric_normalized_feature_keys(
        labeled_rows, min_coverage_ratio=args.norm_min_coverage, max_features=args.max_norm_features
    )
    selected_keys = [row["key"] for row in feature_candidates]

    X_dict: list[dict[str, Any]] = []
    y: list[int] = []
    for row in labeled_rows:
        feature_row: dict[str, Any] = {"score": float(row.score), "game_slug": row.game_slug}
        for key in selected_keys:
            value = to_float(row.normalized_features.get(key))
            if value is not None:
                feature_row[f"norm__{key}"] = value
        X_dict.append(feature_row)
        y.append(target_value(row.review_status, mode))

    positives = sum(y)
    negatives = len(y) - positives
    if positives == 0 or negatives == 0:
        return {"ran": False, "reason": "Only one class present for selected target mode."}

    stratify_target = y if positives >= 2 and negatives >= 2 else None
    X_train_dict, X_test_dict, y_train, y_test = train_test_split(
        X_dict, y, test_size=0.3, random_state=42, stratify=stratify_target
    )

    vectorizer = DictVectorizer(sparse=True)
    X_train = vectorizer.fit_transform(X_train_dict)
    X_test = vectorizer.transform(X_test_dict)

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()
    auc = roc_auc_score(y_test, proba) if len(set(y_test)) == 2 else None

    feature_names = vectorizer.get_feature_names_out()
    coefs = model.coef_[0]
    weighted_features = sorted(zip(feature_names, coefs), key=lambda item: item[1], reverse=True)
    top_positive = [{"feature": f, "coef": round(float(c), 6)} for f, c in weighted_features[:8]]
    top_negative = [{"feature": f, "coef": round(float(c), 6)} for f, c in weighted_features[-8:]]

    return {
        "ran": True,
        "target_mode": mode,
        "feature_set": {
            "core": ["score", "game_slug"],
            "selected_normalized_numeric_features": selected_keys,
            "selection_meta": feature_candidates,
            "encoding": "DictVectorizer one-hot encodes categorical features and keeps numeric features as-is.",
        },
        "split_strategy": {
            "method": "random_train_test_split",
            "test_size": 0.3,
            "random_state": 42,
            "stratified": stratify_target is not None,
            "limitation": "Single random split can be noisy on small datasets; use repeated CV once data grows.",
        },
        "class_balance": {
            "total_rows": len(y),
            "positives": positives,
            "negatives": negatives,
            "positive_rate_pct": round(pct(positives, len(y)), 2),
        },
        "metrics": {
            "test_auc": round(float(auc), 4) if auc is not None else None,
            "test_precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
            "test_recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        },
        "model_details": {
            "model_type": "LogisticRegression",
            "class_weight": "balanced",
            "intercept": round(float(model.intercept_[0]), 6),
            "top_positive_coefficients": top_positive,
            "top_negative_coefficients": top_negative,
        },
    }


def build_report(rows: list[ParsedRow], args: argparse.Namespace) -> dict[str, Any]:
    by_game = label_distribution_by_game(rows)
    by_status_score = score_distribution_by_status(rows)
    rules_triage = compare_rules_score(rows, "triage_positive")
    rules_accepted = compare_rules_score(rows, "accepted_only")
    per_game_triage = per_game_triage_evaluation(rows, args.min_game_sample, args.weak_game_count)
    weak_diagnostics = weak_game_diagnostics(rows, per_game_triage)

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "row_count": len(rows),
        "assumptions": [
            "Export contains current ranking snapshot only (is_current=true) by default.",
            "Review status is treated as current point-in-time label, not a full history.",
            "Timestamps may be naive UTC; normalize timezone in downstream analysis pipelines.",
            "Class imbalance is expected, especially for ACCEPTED-only targets.",
            "Per-game variation is likely significant; evaluate per-game before global model use.",
            "Per-game AUC on modest samples is directional, not final.",
            "Weak-game diagnostics compare triage-positive vs non-triage-positive outcomes.",
        ],
        "label_distribution_by_game": by_game,
        "score_distribution_by_review_status": by_status_score,
        "rules_score_vs_outcomes": {
            "triage_positive_target": rules_triage,
            "accepted_only_target": rules_accepted,
        },
        "per_game_triage_evaluation": per_game_triage,
        "weak_game_diagnostics": weak_diagnostics,
        "interpretation_guidance": {
            "triage_auc_good_threshold": ">= 0.75 usually indicates useful triage ordering signal.",
            "triage_auc_caution_threshold": "< 0.65 indicates weak ranking signal; inspect game-specific rules/features.",
            "component_signal_guide": "Strong signal = high mean gap plus reasonable effect size; weak signal = low gap/effect.",
        },
    }

    if args.run_logistic:
        report["logistic_experiment"] = run_optional_logistic(rows, args.target_mode, args)

    return report


def print_summary(report: dict[str, Any]) -> None:
    print("\n=== Recruit Offline Analysis Summary ===")
    print(f"Rows analyzed: {report['row_count']}")

    print("\nLabel distribution by game:")
    for game, stats in report["label_distribution_by_game"].items():
        print(f"- {game}: total={stats['total']} status_counts={stats['status_counts']}")

    print("\nScore distribution by review status (mean/median/n):")
    by_status = report["score_distribution_by_review_status"]
    for status in sorted(by_status.keys()):
        stats = by_status[status]
        print(f"- {status}: mean={stats['mean']} median={stats['median']} n={stats['n']}")

    print("\nRules score vs outcome targets:")
    for name, section in report["rules_score_vs_outcomes"].items():
        print(
            f"- {name}: auc={section['score_auc_vs_target']} "
            f"positive_rate_pct={section['positive_rate_pct']} "
            f"rows_with_score={section['rows_with_score']}"
        )

    print("\nPer-game triage-positive evaluation (sample, AUC):")
    per_game = report["per_game_triage_evaluation"]["by_game"]
    for game, section in per_game.items():
        print(
            f"- {game}: sample={section['sample_size']} "
            f"auc={section['triage_positive_auc']} "
            f"positive_rate_pct={section['positive_rate_pct']}"
        )

    strongest = report["per_game_triage_evaluation"]["strongest_games_by_auc"]
    weakest = report["per_game_triage_evaluation"]["weakest_games_by_auc"]
    if strongest:
        print("\nStrongest games by triage AUC:")
        for row in strongest:
            print(f"- {row['game']}: auc={row['auc']} sample={row['sample_size']}")
    if weakest:
        print("\nWeakest games by triage AUC:")
        for row in weakest:
            print(f"- {row['game']}: auc={row['auc']} sample={row['sample_size']}")

    diagnostics = report.get("weak_game_diagnostics", {})
    weak_games = diagnostics.get("games", [])
    by_game_diag = diagnostics.get("by_game", {})
    if weak_games:
        print("\nWeak-game component/feature diagnostics:")
        for game in weak_games:
            diag = by_game_diag.get(game, {})
            useful = diag.get("most_useful_components", [])
            weak = diag.get("least_useful_components", [])
            inconsistent = diag.get("inconsistent_components", [])
            useful_features = diag.get("most_useful_normalized_features", [])

            useful_names = [row.get("component") for row in useful[:3]]
            weak_names = [row.get("component") for row in weak[:3]]
            incons_names = [row.get("component") for row in inconsistent[:3]]
            feature_names = [row.get("feature") for row in useful_features[:3]]

            print(
                f"- {game}: "
                f"useful_components={useful_names if useful_names else []} "
                f"weak_components={weak_names if weak_names else []} "
                f"inconsistent_components={incons_names if incons_names else []} "
                f"useful_normalized_features={feature_names if feature_names else []}"
            )

    if "logistic_experiment" in report:
        logistic = report["logistic_experiment"]
        if logistic.get("ran"):
            m = logistic["metrics"]
            cm = m["confusion_matrix"]
            print(
                "\nLogistic experiment (offline): "
                f"auc={m['test_auc']} precision={m['test_precision']} recall={m['test_recall']} "
                f"cm=[tn={cm['tn']}, fp={cm['fp']}, fn={cm['fn']}, tp={cm['tp']}]"
            )
        else:
            print(f"\nLogistic experiment skipped: {logistic.get('reason')}")


def main() -> int:
    args = parse_args()

    if not args.input_file and not args.api_base_url:
        print("Provide either --input-file or --api-base-url.", file=sys.stderr)
        return 2

    payload = load_export_data(args)
    rows = parse_rows(payload)
    report = build_report(rows, args)
    print_summary(report)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with args.output_json.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nWrote report JSON to: {args.output_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
