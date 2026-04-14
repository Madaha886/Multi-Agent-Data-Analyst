"""Deterministic scoring for the evaluation pack."""

from __future__ import annotations

import math
from typing import Any

from .contracts import EvalScores, GoldExpectation

WEIGHTS = {
    "execution_success": 0.10,
    "task_type_match": 0.15,
    "required_columns_match": 0.15,
    "operation_intent_match": 0.15,
    "result_correctness": 0.30,
    "final_answer_alignment": 0.10,
    "critique_quality": 0.05,
}


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_label(value: Any) -> str:
    return str(value).strip().lower()


def _field_aliases(field: str, gold: GoldExpectation) -> set[str]:
    aliases = {field}
    aliases.update(gold.allowed_result_aliases.get(field, []))
    for canonical, alias_values in gold.allowed_result_aliases.items():
        if field in alias_values:
            aliases.add(canonical)
            aliases.update(alias_values)
    return {_normalize_label(item) for item in aliases}


def score_required_columns(predicted: list[str], expected: list[str]) -> float:
    if not expected:
        return 1.0
    predicted_set = {_normalize_label(column) for column in predicted}
    expected_set = {_normalize_label(column) for column in expected}
    return len(predicted_set & expected_set) / len(expected_set)


def score_operation_intent(code: str, expected_ops: list[str]) -> float:
    if not expected_ops:
        return 1.0
    lowered = code.lower()
    matches = 0
    for operation in expected_ops:
        token = operation.lower()
        if token in lowered:
            matches += 1
    return matches / len(expected_ops)


def _compare_numbers(actual: Any, expected: Any, tolerance: float = 0.01) -> float:
    actual_num = _to_float(actual)
    expected_num = _to_float(expected)
    if actual_num is None or expected_num is None:
        return 0.0
    if math.isclose(actual_num, expected_num, rel_tol=1e-4, abs_tol=tolerance):
        return 1.0
    diff = abs(actual_num - expected_num)
    scale = max(abs(expected_num), 1.0)
    return max(0.0, 1.0 - (diff / scale))


def _score_pairs(actual_pairs: list[list[Any]], expected_pairs: list[list[Any]]) -> float:
    if not expected_pairs:
        return 1.0
    total = 0.0
    count = 0
    for idx, expected in enumerate(expected_pairs):
        if idx >= len(actual_pairs):
            count += 1
            continue
        actual = actual_pairs[idx]
        if not actual:
            count += 1
            continue
        label_score = 1.0 if _normalize_label(actual[0]) == _normalize_label(expected[0]) else 0.0
        value_score = 1.0 if len(expected) == 1 else (
            _compare_numbers(actual[1], expected[1]) if _to_float(expected[1]) is not None else (
                1.0 if _normalize_label(actual[1]) == _normalize_label(expected[1]) else 0.0
            )
        )
        total += (label_score + value_score) / 2
        count += 1
    return total / max(count, 1)


def _find_matching_key(actual: dict[str, Any], expected_key: str, gold: GoldExpectation) -> str | None:
    expected_aliases = _field_aliases(expected_key, gold)
    for key in actual:
        if _normalize_label(key) in expected_aliases:
            return key
    return None


def _score_rows(actual_rows: list[dict[str, Any]], expected_rows: list[dict[str, Any]], gold: GoldExpectation) -> float:
    if not expected_rows:
        return 1.0
    total = 0.0
    count = 0
    for idx, expected in enumerate(expected_rows):
        if idx >= len(actual_rows):
            count += 1
            continue
        actual = actual_rows[idx]
        field_scores = []
        for key, expected_value in expected.items():
            actual_key = _find_matching_key(actual, key, gold)
            actual_value = actual.get(actual_key) if actual_key is not None else None
            if _to_float(expected_value) is not None:
                field_scores.append(_compare_numbers(actual_value, expected_value))
            else:
                field_scores.append(1.0 if _normalize_label(actual_value) == _normalize_label(expected_value) else 0.0)
        total += sum(field_scores) / max(len(field_scores), 1)
        count += 1
    return total / max(count, 1)


def score_result_correctness(actual_artifact: dict[str, Any] | None, gold: GoldExpectation) -> float:
    if actual_artifact is None:
        return 0.0

    if gold.expected_result_kind == "scalar":
        if actual_artifact.get("kind") != "scalar":
            return 0.0
        return _compare_numbers(actual_artifact.get("value"), gold.reference_result.get("value"))

    if gold.expected_result_kind == "pairs":
        if actual_artifact.get("kind") == "pairs":
            actual_pairs = actual_artifact.get("pairs", [])
        elif actual_artifact.get("kind") == "rows":
            columns = actual_artifact.get("columns", [])
            records = actual_artifact.get("records", [])
            if len(columns) < 2:
                return 0.0
            actual_pairs = [[record.get(columns[0]), record.get(columns[1])] for record in records]
        else:
            return 0.0
        return _score_pairs(actual_pairs, gold.reference_result.get("pairs", []))

    if gold.expected_result_kind == "rows":
        if actual_artifact.get("kind") != "rows":
            return 0.0
        return _score_rows(actual_artifact.get("records", []), gold.reference_result.get("records", []), gold)

    return 0.0


def score_final_answer_alignment(final_answer: dict[str, Any], gold: GoldExpectation) -> float:
    summary = str(final_answer.get("summary", "")).strip()
    result_preview = str(final_answer.get("result_preview", ""))
    findings_text = " ".join(final_answer.get("key_findings", []))
    combined = f"{summary}\n{result_preview}\n{findings_text}".lower()

    signal_hits = 0
    for signal in gold.acceptable_signals[:3]:
        if signal.lower() in combined:
            signal_hits += 1
    signal_score = signal_hits / max(min(len(gold.acceptable_signals), 3), 1)
    summary_score = 1.0 if summary and "did not complete" not in summary.lower() else 0.0
    return (0.7 * signal_score) + (0.3 * summary_score)


def score_critique_quality(
    critique_feedback: dict[str, Any],
    result_correctness: float,
    execution_success: bool,
) -> float:
    issues = critique_feedback.get("issues", [])
    critique_passed = bool(critique_feedback.get("is_valid"))
    revision_needed = bool(critique_feedback.get("revision_needed"))

    if not execution_success:
        return 1.0 if issues else 0.0
    if result_correctness >= 0.8:
        if critique_passed and not revision_needed:
            return 1.0
        if issues:
            return 0.25
        return 0.0
    if result_correctness < 0.5:
        return 1.0 if issues else 0.0
    return 0.5 if issues else 0.25


def build_scores(
    *,
    execution_success: bool,
    predicted_task_type: str,
    predicted_columns: list[str],
    code: str,
    actual_artifact: dict[str, Any] | None,
    final_answer: dict[str, Any],
    critique_feedback: dict[str, Any],
    gold: GoldExpectation,
) -> EvalScores:
    scores = {
        "execution_success": 1.0 if execution_success else 0.0,
        "required_columns_match": score_required_columns(predicted_columns, gold.expected_key_columns),
        "operation_intent_match": score_operation_intent(code, gold.expected_operation_pattern),
        "result_correctness": score_result_correctness(actual_artifact, gold),
    }
    scores["task_type_match"] = 1.0 if predicted_task_type == gold.expected_task_type else (
        0.5 if scores["result_correctness"] >= 0.8 else 0.0
    )
    scores["final_answer_alignment"] = score_final_answer_alignment(final_answer, gold)
    scores["critique_quality"] = score_critique_quality(
        critique_feedback,
        scores["result_correctness"],
        execution_success,
    )
    overall = sum(scores[name] * weight for name, weight in WEIGHTS.items())
    scores["overall_score"] = round(overall, 4)
    return EvalScores(**scores)
