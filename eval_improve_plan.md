# Evaluation Recovery Plan

## Summary
Improve the benchmark score by fixing the highest-impact mismatch between the current pipeline and the 10-question evaluation set. The core problem is not execution reliability; it is semantic coverage. The system currently executes all questions but answers many of them with the wrong analytical pattern, then the critic and evaluator penalize those mismatches correctly.

The fastest path is to upgrade the planner and query generator to support the actual question shapes in `dataset/questions.json`, then relax the critic so it flags real mismatches rather than every harmless assumption, and finally tune the evaluator to distinguish “exactly wrong” from “numerically right but phrased differently.”

## Key Changes
- Expand planner intent detection to cover the benchmark’s real techniques, not just broad task labels:
  - recognize `count`, `percentage/rate`, `time_series_count`, `time_series_sum`, `comparison_rate`, `comparison_mean`, and `within_group_best`
  - stop defaulting to `Amount` for questions that are really about `Order ID`, `Status`, `Qty`, `promotion-ids`, or derived date parts
  - detect derived dimensions explicitly: `month`, `day_of_week`, `promotion_used`, `cancelled_flag`
- Strengthen question-to-column grounding in the planner:
  - “number of orders” -> `Order ID` or row count, not `Amount`
  - “cancelled percentage/rate” -> `Status`
  - “shipping fulfilled by Amazon vs merchant” -> `Fulfilment` + `Status`
  - “promotion applied” -> `promotion-ids`
  - “day of week” -> derived from `Date`
  - “size sells best within each category” -> `Category` + `Size` + `Qty`
- Refactor query generation from one generic grouped-`Amount` template into question-shape-specific templates:
  - revenue/category ranking
  - monthly order count
  - cancellation percentage scalar
  - top-N order-count ranking by state
  - popularity by size using `Qty`
  - cancellation-rate comparison by `Fulfilment`
  - mean `Amount` comparison by `B2B`
  - per-category best size via crosstab/pivot + `idxmax`
  - promotion-vs-no-promotion average `Amount`
  - weekday revenue ranking from `Date.dt.day_name()`
- Introduce planner metadata needed by the query generator:
  - metric kind such as `sum_amount`, `mean_amount`, `count_orders`, `count_rows`, `cancel_rate`, `top_within_group`
  - optional derived columns list such as `month`, `day_of_week`, `promotion_used`, `is_cancelled`
  - optional ranking limit
- Update the critic so it evaluates meaningful risk instead of blanket-failing most runs:
  - do not fail solely because the query used reasonable dataset mappings like `Amount` for revenue
  - flag assumptions only when they materially change semantics or when a required derived feature was missing
  - compare question intent against chosen metric/grouping/derived columns
  - allow valid answers that use equivalent representations, such as renamed measure columns
- Tighten evaluator fairness without weakening correctness:
  - keep exact correctness as the top-weighted metric
  - allow column-name aliases in result comparison, for example `Amount` vs `total_amount` or `average_amount`
  - treat task taxonomy mismatch less harshly when the result is semantically correct
  - separate “semantic correctness” from “taxonomy correctness” in reporting so the report explains failures better
- Add benchmark diagnostics to make failures actionable:
  - include expected vs predicted analytical pattern
  - include expected vs predicted columns
  - include a “primary mismatch reason” field per question
  - include grouped summary by failure mode such as `wrong_metric`, `wrong_grouping`, `missing_derived_column`, `overly_strict_critique`
- Keep all new artifacts inside the repo:
  - default evaluation output should move to something like `artifacts/eval_smoke/`
  - docs/examples should stop using `/tmp`

## Public Interfaces / Contracts
- Extend `AnalysisPlan` with fields needed for correct execution:
  - `metric: str | None`
  - `derived_columns: list[str]`
  - `ranking_limit: int | None`
- Keep the existing CLI entry points, but update the evaluation docs/examples to use repo-local output directories only.
- Preserve the current evaluation result schema, but add optional per-question diagnostics:
  - `expected_task_type`
  - `task_type_reason`
  - `primary_mismatch_reason`
- Update `dataset/eval_gold.json` only if needed to add alias metadata for acceptable output column names; do not change the reference answers themselves.

## Test Plan
- Add planner regression tests for all 10 benchmark questions:
  - expected task pattern
  - expected key columns
  - expected derived columns
  - expected metric
- Add query-generator regression tests for the missing shapes:
  - cancellation percentage
  - monthly order count
  - weekday revenue ranking
  - promotion comparison
  - best size within category
- Add end-to-end benchmark assertions:
  - all 10 questions still execute successfully
  - task-type match improves materially from the current 5/10 baseline
  - high result-correctness count improves materially from the current 0/10 baseline
  - critique passes for at least the clearly supported questions
- Add evaluator tests for fairer comparison:
  - alias-tolerant column comparison
  - rows-to-pairs equivalence
  - scalar percentage tolerance
  - ranking comparisons with equivalent value labels
- Add critic tests:
  - reasonable dataset mappings do not automatically fail critique
  - genuinely wrong metric/grouping still fails critique

## Assumptions And Defaults
- The goal is to raise benchmark quality on the existing 10-question pack, not redesign the whole architecture.
- Priority order is:
  1. planner/query semantic coverage
  2. critic realism
  3. evaluator calibration
- The benchmark should remain strict enough to catch wrong answers; we are improving correctness first, not hiding failures.
- Repo-local artifact output is the new default for all evaluation examples and smoke runs.
