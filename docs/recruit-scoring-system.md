# Recruit Scoring, Coach Triage, and Offline ML Comparison

## 1. Project Overview
This capstone work implemented an explainable recruit ranking and coach triage system for the AU Esports recruiting workflow.

The core problem was operational, not novelty-driven:
- Coaches needed faster triage across multiple games with different profile fields.
- Manual review lacked consistent prioritization.
- The platform needed decision support that is transparent enough for coaches to trust.

Project goal:
- Build a practical, explainable scoring system integrated into recruit submission and admin review.
- Add a structured coach review workflow to capture outcomes.
- Use those outcomes for offline model evaluation without forcing ML into production early.

## 2. Initial Design Strategy
The implementation followed a staged plan:

1. Phase 1: explainable rules-based scoring
- Per-game weighted scoring with component-level explanations.
- Score breakdown visible in admin views.

2. Phase 2: structured coach review workflow
- Standard status labels and review metadata for operational triage and future learning signals.

3. Phase 3: offline ML evaluation
- Export current ranking + review state for offline analysis.
- Compare simple ML baselines against rules score before any production ML decision.

Why rules first:
- Immediate coach usability and transparency.
- Faster implementation with low operational risk.
- Better baseline quality before collecting enough labeled data for robust ML.

## 3. System Architecture
### Implemented modules (current repository state)
- Frontend (Next.js):
  - [apps/web/app/recruit/page.tsx](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/web/app/recruit/page.tsx)
  - [apps/web/app/admin/recruits/_components/RecruitGameListPage.tsx](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/web/app/admin/recruits/_components/RecruitGameListPage.tsx)
  - [apps/web/app/admin/recruits/[id]/page.tsx](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/web/app/admin/recruits/[id]/page.tsx)
  - [apps/web/app/admin/recruits/_components/scoreBands.ts](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/web/app/admin/recruits/_components/scoreBands.ts)
- Backend (FastAPI):
  - [apps/api/app/v1/endpoints/recruits_public.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/v1/endpoints/recruits_public.py)
  - [apps/api/app/v1/endpoints/recruits_admin.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/v1/endpoints/recruits_admin.py)
- Scoring services:
  - [apps/api/app/services/scoring/base.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/services/scoring/base.py)
  - [apps/api/app/services/scoring/registry.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/services/scoring/registry.py)
  - Per-game modules in [apps/api/app/services/scoring](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/services/scoring)
  - Canonical result contract: [apps/api/app/services/scoring/contracts.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/services/scoring/contracts.py)
- Models / schemas / migrations:
  - [apps/api/app/models/recruit.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/models/recruit.py)
  - [apps/api/app/schemas/recruit.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/schemas/recruit.py)
  - [apps/api/app/schemas/admin.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/schemas/admin.py)
  - [apps/api/alembic/versions/fcab3fb0cada_fresh_schema.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/alembic/versions/fcab3fb0cada_fresh_schema.py)
  - [apps/api/alembic/versions/9f2e6c1b7a4c_add_ranking_metadata.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/alembic/versions/9f2e6c1b7a4c_add_ranking_metadata.py)
  - [apps/api/alembic/versions/4a8c2d3f5b71_add_recruit_review_label_metadata.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/alembic/versions/4a8c2d3f5b71_add_recruit_review_label_metadata.py)
  - [apps/api/alembic/versions/072837d9b7e8_new_admin_ui_changes.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/alembic/versions/072837d9b7e8_new_admin_ui_changes.py)
- Offline analysis:
  - [apps/api/app/ml/offline_training_analysis.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/ml/offline_training_analysis.py)

### End-to-end data flow
`recruit form` -> `POST /api/v1/recruit/apply` -> `score_application(game_slug, payload)` -> `game scorer module` -> `RecruitApplication + RecruitAvailability + RecruitGameProfile + RecruitRanking` (single transaction in route) -> `admin list/detail endpoints` -> `coach review status/notes updates` -> `GET /api/v1/admin/recruits/export/training` -> `offline_training_analysis.py`.

## 4. Major Implementation Steps Completed
| Step | What changed | Key modules/files | Risk/problem solved |
|---|---|---|---|
| 1. Repo analysis and mapping | Recruit architecture was mapped end-to-end before feature work. | Frontend admin/recruit pages, FastAPI endpoints, models, migrations | Reduced implementation guesswork and hidden coupling risk. |
| 2. Mario Kart validation alignment | Game-specific required field mismatch was corrected (Mario Kart and Smash exceptions). | [apps/api/app/schemas/recruit.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/schemas/recruit.py), [apps/web/app/recruit/page.tsx](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/web/app/recruit/page.tsx) | Prevented valid Mario Kart submissions from being rejected or forced through wrong fields. |
| 3. Alembic source-of-truth protection | Runtime `create_all` became opt-in via `AUTO_CREATE_TABLES`. | [apps/api/app/main.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/main.py), Alembic config/files | Reduced schema drift risk between runtime table creation and migration history. |
| 4. Centralized scoring dispatch | Route-level per-game branching removed; scorer selection centralized by slug. | [apps/api/app/services/scoring/base.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/services/scoring/base.py), [apps/api/app/services/scoring/registry.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/services/scoring/registry.py), [apps/api/app/v1/endpoints/recruits_public.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/v1/endpoints/recruits_public.py) | Eliminated duplicated scoring dispatch logic and reduced routing complexity. |
| 5. Canonical scoring contract | Unified `ScoringResult` contract introduced for all scorers. | [apps/api/app/services/scoring/contracts.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/services/scoring/contracts.py), scorer modules | Prevented schema drift across scorer outputs and simplified downstream persistence/rendering. |
| 6. Scorer standardization | Per-game modules now natively return consistent explanation structure. | [apps/api/app/services/scoring](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/services/scoring) | Reduced adapter complexity and enabled shared UI rendering. |
| 7. Ranking metadata persistence | Ranking records store raw inputs, normalized features, method, version, current flag, and scoring time. | [apps/api/app/models/recruit.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/models/recruit.py), [apps/api/alembic/versions/9f2e6c1b7a4c_add_ranking_metadata.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/alembic/versions/9f2e6c1b7a4c_add_ranking_metadata.py) | Enabled explainability, rescoring support, and offline feature analysis. |
| 8. Admin explainability UI | Score, method/version/time, component breakdown, and feature/input sections added to admin views. | [apps/web/app/admin/recruits/[id]/page.tsx](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/web/app/admin/recruits/[id]/page.tsx), [apps/web/app/admin/recruits/_components/RecruitGameListPage.tsx](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/web/app/admin/recruits/_components/RecruitGameListPage.tsx) | Turned score from opaque value into actionable explanation. |
| 9. Transaction hardening | Submission path wrapped app+availability+profile+ranking persistence in one transaction. | [apps/api/app/v1/endpoints/recruits_public.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/v1/endpoints/recruits_public.py) | Reduced partial-write risk when later writes fail. |
| 10. Structured review workflow | Formal statuses and review metadata (`labeled_at`, `label_reason`, reviewer attribution) added. | [apps/api/app/models/recruit.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/models/recruit.py), [apps/api/alembic/versions/4a8c2d3f5b71_add_recruit_review_label_metadata.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/alembic/versions/4a8c2d3f5b71_add_recruit_review_label_metadata.py), [apps/api/app/v1/endpoints/recruits_admin.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/v1/endpoints/recruits_admin.py) | Replaced ad-hoc review state with auditable triage workflow data. |
| 11. Triage list enhancements | Status filters and review metadata surfaced at list level. | [apps/web/app/admin/recruits/_components/RecruitGameListPage.tsx](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/web/app/admin/recruits/_components/RecruitGameListPage.tsx) | Improved throughput by reducing required detail-page opens during triage. |
| 12. Training/export endpoint | Admin-only export for scoring + review snapshots added. | [apps/api/app/v1/endpoints/recruits_admin.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/v1/endpoints/recruits_admin.py), [apps/api/app/schemas/admin.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/schemas/admin.py) | Enabled reproducible offline dataset creation without touching production scoring. |
| 13. Offline analysis starter | Script added for label/score distributions and baseline score diagnostics. | [apps/api/app/ml/offline_training_analysis.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/ml/offline_training_analysis.py) | Created evidence loop for tuning decisions instead of intuition-only changes. |
| 14. Threshold policy and score bands | Global + Smash score-band policy formalized from offline analysis. | [apps/web/app/admin/recruits/_components/scoreBands.ts](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/web/app/admin/recruits/_components/scoreBands.ts), [docs/recruit-triage-playbook.md](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/docs/recruit-triage-playbook.md) | Standardized coach triage interpretation and reduced inconsistent manual cutoff use. |
| 15. Offline ML comparison extension | Logistic comparison vs rules baseline on same split added (optional gradient boosting path). | [apps/api/app/ml/offline_training_analysis.py](C:/Users/rpope/Documents/GitHub/AU-Esports-Web-Refresh/apps/api/app/ml/offline_training_analysis.py) | Allowed honest assessment of ML value before considering any production ML path. |

## 5. Scoring Design (Production)
### Production scorer type
- Rules-based, per-game weighted scoring.
- Explainable by design.
- No production ML inference path.

### Canonical scoring payload
Current storage/use focuses on:
- `score`
- `explanation_json`
- `raw_inputs_json`
- `normalized_features_json`
- `scoring_method`
- `model_version`
- `scored_at`
- `is_current`

### Why explainability mattered
- Coaches can inspect not only rank order but causal components.
- Admin pages render weighted breakdown and top contributors.
- Supports auditability and post-hoc tuning by game.

### Triage score bands (presentation layer)
Global default:
- `>= 80`: High priority
- `70-79`: Review soon
- `< 70`: Low priority / backlog
- `>= 90`: optional Very high confidence shortlist

Smash special case:
- `>= 60`: High priority
- `50-59`: Review soon
- `< 50`: Low priority / backlog

Important interpretation:
- These bands are decision-support for review order.
- They are not automatic accept/reject decisions.

## 6. Coach/Admin Workflow
### Admin list workflow
- Sort by score/time/name, filter by min score and review status.
- Shows score, top reasons preview, status, labeled timestamp, reviewer display.
- Shows score-band label for triage.

### Admin detail workflow
- Full profile + availability + score metadata + weighted breakdown.
- Inputs and normalized features shown for explainability.
- Structured review actions:
  - status update
  - optional `label_reason`
  - reviewer attribution
  - `labeled_at` tracking
  - notes editing workflow

This converted scoring from a raw number into an operational review process.

## 7. Testing and Validation Performed
Validation was implementation-focused and offline-analysis-focused. No claim of full production-grade ML validation is made.

1. Submission/scoring flow validation
- Verified scorer dispatch path across supported games.
- Verified canonical scoring output persists through submission route.

2. Form/backend validation alignment
- Confirmed Mario Kart + Smash handling for profile requiredness mismatch risk.

3. Transaction safety validation
- Submission route now wraps related inserts in a transaction boundary.
- Goal verified: avoid leaving partial recruit data if ranking/profile persistence fails.

4. Ranking metadata and admin endpoint validation
- Verified list/detail endpoints surface current ranking metadata needed for explainable UI.

5. Review workflow validation
- Verified structured statuses and metadata persistence (`labeled_at`, `label_reason`, reviewer attribution, notes).

6. Triage UI validation
- Verified list/detail rendering of score bands, reasons, and coach guidance text.
- Verified Smash-specific thresholds applied in UI helper logic.

7. Export pipeline validation
- Verified admin-only training export returns current ranking + current review shape for offline dataset creation.

8. Offline analysis validation
- Verified script outputs label distributions, score distributions, per-game AUCs, threshold tables, weak-game diagnostics.
- Verified logistic comparison path is offline-only and does not affect live app behavior.

## 8. Offline Analysis Results (Accepted)
All findings below are offline analysis results, not production A/B outcomes.

### Core finding
- The rules score provided a useful triage signal.

Concrete snapshots from accepted analysis runs:
- 62-row run:
  - `triage_positive` AUC: `0.8686`
  - `accepted_only` AUC: `0.6474`
- 212-row run:
  - `triage_positive` AUC: `0.7591`
  - `accepted_only` AUC: `0.8248`
  - logistic experiment (offline): AUC `0.6818` (below rules triage baseline on that dataset snapshot)
- 412-row pre-tuning diagnostic run:
  - global `triage_positive` AUC: `0.7345`
  - weak games included Fortnite (`0.6533`), Valorant (`0.7115`), Rocket League (`0.7213`)

Additional accepted outcomes:
- Weak-game diagnostics were used to drive targeted tuning (weight-focused, explainable).
- Later accepted passes retained updates for Fortnite, Valorant, and Rocket League.
- Follow-up accepted runs reported better weak-game separation than the immediate pre-tuning snapshot.

Conservative note:
- Exact final post-pass AUC values for every accepted tuning iteration are not fully committed in repository artifacts; project decisions referenced accepted offline report outputs at execution time.

## 9. Tuning Process and Outcomes
Tuning method:
- Diagnose weak games by component contribution and feature separation.
- Apply small, weight-only changes first.
- Re-evaluate on same offline pipeline.
- Keep strong games frozen unless evidence supports change.

Observed/accepted direction of changes:
- Fortnite: meaningful improvement from weak baseline after targeted weighting.
- Valorant: modest improvement.
- Rocket League: modest improvement.
- Smash: initially weak in one cycle, later improved to acceptable and then frozen.
- Overwatch: highlighted limits in feature definition quality rather than pure weight imbalance.

Why this mattered:
- Tuning remained explainable and game-specific.
- Avoided speculative "AI tuning" without evidence.

## 10. ML Comparison (Offline Only)
### Scope
- ML work stayed offline.
- No model inference path was deployed to backend/frontend/DB production workflows.

### Implemented comparison design
- Primary target: `triage_positive` (`WATCHLIST`, `TRYOUT`, `ACCEPTED` vs rest).
- Secondary reference target: `accepted_only` (class-imbalance-limited).
- Main model: Logistic Regression (interpretable coefficients).
- Optional secondary model path: Gradient Boosting (if enabled and environment supports it).

### Result and interpretation
- Latest validated same-split comparison outcome: logistic regression underperformed the tuned rules baseline for the primary triage target.
- Accepted project conclusion: logistic regression did not produce a strong enough advantage over the tuned rules baseline to justify replacing production rules.
- In validated comparisons, logistic underperformed or only marginally improved depending on snapshot; rule-based interpretation policy was maintained.
- Per project rule: small ML gains do not justify increased complexity over explainable rules in this phase.

Conservative note:
- The code includes an optional gradient boosting experiment path, but validated project decisions were based primarily on the logistic-vs-rules comparison.

Likely causes:
- Limited dataset size.
- Label noise / point-in-time labels.
- Features partially derived from existing rule logic.
- Strong domain knowledge already encoded in per-game rules.

Production decision:
- Keep rules-based scoring as default.
- Keep ML as a future extension path only.

## 11. Final Conclusions
This project successfully delivered a full decision-support system without forcing premature ML:
- Explainable per-game scoring integrated into live submission and admin review.
- Structured coach workflow with auditable statuses and metadata.
- Offline export + analysis loop enabling evidence-driven iteration.
- Practical score-band triage guidance embedded directly in coach/admin UI.

Most important capstone result:
- A well-engineered, explainable rules system can outperform or match early ML baselines under realistic data constraints, while being easier to trust and maintain.

## 12. Future Work
Practical next steps:
- Increase label quality/quantity and broaden outcome capture.
- Add review-history/audit trail (status transitions over time).
- Expand game-specific feature depth where diagnostics show weak signal.
- Run repeated-split/cross-validation ML comparisons as data grows.
- Reconsider production ML only when:
  - data volume and consistency improve,
  - gains are stable and meaningful,
  - explainability/operational controls remain acceptable.

## 13. Appendix: Milestone Timeline (Summary)
1. Architecture and data-flow mapping.
2. Validation alignment (including Mario Kart handling).
3. Scoring centralization and canonical contract.
4. Standardized scorer outputs.
5. Ranking metadata persistence.
6. Admin explainability UI.
7. Transaction hardening for submission.
8. Structured review workflow rollout.
9. Triage list enhancements.
10. Admin export for offline datasets.
11. Offline analysis + diagnostics.
12. Weak-game tuning passes.
13. Threshold policy and triage playbook integration.
14. Offline ML comparison and production decision to keep rules-based scoring.
