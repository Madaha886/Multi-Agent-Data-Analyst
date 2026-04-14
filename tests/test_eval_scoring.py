from multi_agent_analyst.eval.contracts import GoldExpectation
from multi_agent_analyst.eval.scoring import (
    build_scores,
    score_operation_intent,
    score_required_columns,
    score_result_correctness,
)


def test_score_required_columns_partial_match():
    score = score_required_columns(["Amount", "ship-state"], ["Amount", "Category"])
    assert score == 0.5


def test_score_operation_intent_matches_expected_tokens():
    score = score_operation_intent("df.groupby('Category')['Amount'].sum().sort_values()", ["groupby", "sum", "sort_values"])
    assert score == 1.0


def test_score_result_correctness_for_scalar_with_tolerance():
    gold = GoldExpectation(
        question_id=1,
        expected_task_type="aggregation",
        expected_key_columns=["Status"],
        expected_operation_pattern=[],
        expected_result_kind="scalar",
        reference_result={"value": 14.213607288234154},
    )
    score = score_result_correctness({"kind": "scalar", "value": 14.2136073}, gold)
    assert score == 1.0


def test_score_result_correctness_for_pairs_ranking():
    gold = GoldExpectation(
        question_id=4,
        expected_task_type="ranking",
        expected_key_columns=["ship-state", "Order ID"],
        expected_operation_pattern=["groupby", "count"],
        expected_result_kind="pairs",
        reference_result={"pairs": [["MAHARASHTRA", 22260], ["KARNATAKA", 17326]]},
    )
    score = score_result_correctness(
        {"kind": "pairs", "pairs": [["MAHARASHTRA", 22260], ["KARNATAKA", 17326]]},
        gold,
    )
    assert score == 1.0


def test_score_result_correctness_allows_alias_columns_for_rows():
    gold = GoldExpectation(
        question_id=1,
        expected_task_type="ranking",
        expected_key_columns=["Category", "Amount"],
        expected_operation_pattern=["groupby", "sum"],
        expected_result_kind="rows",
        reference_result={"records": [{"Category": "Set", "Amount": 100.0}]},
        allowed_result_aliases={"Amount": ["total_amount"]},
    )
    score = score_result_correctness(
        {"kind": "rows", "records": [{"Category": "Set", "total_amount": 100.0}]},
        gold,
    )
    assert score == 1.0


def test_build_scores_returns_weighted_overall_score():
    gold = GoldExpectation(
        question_id=7,
        expected_task_type="comparison",
        expected_key_columns=["B2B", "Amount"],
        expected_operation_pattern=["groupby", "mean"],
        expected_result_kind="pairs",
        reference_result={"pairs": [["False", 648.1918072579506], ["True", 701.3295255041519]]},
        acceptable_signals=["True", "False"],
    )
    scores = build_scores(
        execution_success=True,
        predicted_task_type="comparison",
        predicted_columns=["B2B", "Amount"],
        code="result = df.groupby('B2B')['Amount'].mean()",
        actual_artifact={"kind": "pairs", "pairs": [["False", 648.1918072579506], ["True", 701.3295255041519]]},
        final_answer={"summary": "Comparison complete.", "result_preview": "False 648.19 True 701.33", "key_findings": []},
        critique_feedback={"is_valid": True, "issues": [], "revision_needed": False},
        gold=gold,
    )
    assert scores.overall_score > 0.9
