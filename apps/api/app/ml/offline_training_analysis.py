"""
Offline analysis starter for recruit ranking export data.

This script is intentionally offline-only and does not modify production scoring.

Input options:
1) Load JSON from local file created from /api/v1/admin/recruits/export/training
2) Fetch directly from admin export endpoint with bearer auth

Core outputs:
- Label distribution by game
- Score distribution by review status
- Rules score vs coach outcome comparison for two binary target definitions
- Optional score-only logistic regression baseline (if scikit-learn is installed)
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


@dataclass
class ParsedRow:
    application_id: int
    game_slug: str
    review_status: str
    score: float | None
    scored_at: str | None
    submitted_at: str | None
    label_reason: str | None
    raw: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline recruit ranking/training analysis using admin export JSON."
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        help="Path to saved export JSON (same shape as /admin/recruits/export/training).",
    )
    parser.add_argument(
        "--api-base-url",
        type=str,
        help="API base URL (example: http://localhost:8000).",
    )
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
        help="Binary target definition used for optional logistic baseline.",
    )
    parser.add_argument(
        "--run-logistic",
        action="store_true",
        help="Run optional score-only logistic regression baseline if sklearn is available.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to write analysis summary JSON.",
    )
    return parser.parse_args()


def fetch_export_from_api(args: argparse.Namespace) -> dict[str, Any]:
    if not args.api_base_url:
        raise ValueError("Missing --api-base-url when --input-file is not provided.")
    if not args.token:
        raise ValueError("Missing admin token. Pass --token or set AU_ADMIN_TOKEN.")

    query = {
        "limit": args.limit,
    }
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
        headers={
            "Authorization": f"Bearer {args.token}",
            "Accept": "application/json",
        },
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

        score = row.get("score")
        if not isinstance(score, (int, float)):
            score = None
        else:
            score = float(score)

        parsed.append(
            ParsedRow(
                application_id=application_id,
                game_slug=game_slug,
                review_status=review_status,
                score=score,
                scored_at=row.get("scored_at"),
                submitted_at=row.get("submitted_at"),
                label_reason=row.get("label_reason"),
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
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "p25": None,
            "p75": None,
        }
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
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
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

    thresholds = [50.0, 60.0, 70.0, 80.0, 90.0]

    return {
        "target_mode": mode,
        "rows_with_score": len(labeled_rows),
        "positives": positives,
        "negatives": negatives,
        "positive_rate_pct": round(pct(positives, len(y_true)), 2) if y_true else 0.0,
        "positive_score_summary": summarize_score_distribution(pos_scores),
        "negative_score_summary": summarize_score_distribution(neg_scores),
        "score_auc_vs_target": auc_from_scores(y_true, y_score),
        "threshold_table": [threshold_metrics(y_true, y_score, t) for t in thresholds],
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
            "status_pct": {
                status: round(pct(count, total), 2) for status, count in counter.items()
            },
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


def run_optional_logistic(rows: list[ParsedRow], mode: str) -> dict[str, Any]:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )
        from sklearn.model_selection import train_test_split
    except ImportError:
        return {
            "ran": False,
            "reason": "scikit-learn not installed. Install it in the analysis environment to enable this step.",
        }

    labeled_rows = [r for r in rows if r.score is not None]
    if len(labeled_rows) < 30:
        return {
            "ran": False,
            "reason": "Not enough rows with score for a stable train/test split (need ~30+).",
        }

    X = [[float(r.score)] for r in labeled_rows]
    y = [target_value(r.review_status, mode) for r in labeled_rows]
    positives = sum(y)
    negatives = len(y) - positives
    if positives == 0 or negatives == 0:
        return {
            "ran": False,
            "reason": "Only one class present for selected target mode.",
        }

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    return {
        "ran": True,
        "target_mode": mode,
        "feature_set": ["score_only"],
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "test_auc": round(float(roc_auc_score(y_test, proba)), 4),
        "test_accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "test_precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "test_recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "coef_score": round(float(model.coef_[0][0]), 6),
        "intercept": round(float(model.intercept_[0]), 6),
    }


def build_report(rows: list[ParsedRow], args: argparse.Namespace) -> dict[str, Any]:
    by_game = label_distribution_by_game(rows)
    by_status_score = score_distribution_by_status(rows)
    rules_triage = compare_rules_score(rows, "triage_positive")
    rules_accepted = compare_rules_score(rows, "accepted_only")

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "row_count": len(rows),
        "assumptions": [
            "Export contains current ranking snapshot only (is_current=true) by default.",
            "Review status is treated as current point-in-time label, not a full history.",
            "Timestamps may be naive UTC; normalize timezone in downstream analysis pipelines.",
            "Class imbalance is expected, especially for ACCEPTED-only targets.",
            "Per-game variation is likely significant; evaluate per-game before global model use.",
        ],
        "label_distribution_by_game": by_game,
        "score_distribution_by_review_status": by_status_score,
        "rules_score_vs_outcomes": {
            "triage_positive_target": rules_triage,
            "accepted_only_target": rules_accepted,
        },
    }

    if args.run_logistic:
        report["logistic_baseline"] = run_optional_logistic(rows, args.target_mode)

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
        print(
            f"- {status}: mean={stats['mean']} median={stats['median']} n={stats['n']}"
        )

    print("\nRules score vs outcome targets:")
    for name, section in report["rules_score_vs_outcomes"].items():
        print(
            f"- {name}: auc={section['score_auc_vs_target']} "
            f"positive_rate_pct={section['positive_rate_pct']} "
            f"rows_with_score={section['rows_with_score']}"
        )

    if "logistic_baseline" in report:
        logistic = report["logistic_baseline"]
        if logistic.get("ran"):
            print(
                "\nLogistic baseline (score-only): "
                f"test_auc={logistic['test_auc']} "
                f"accuracy={logistic['test_accuracy']} "
                f"precision={logistic['test_precision']} "
                f"recall={logistic['test_recall']}"
            )
        else:
            print(f"\nLogistic baseline skipped: {logistic.get('reason')}")


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
