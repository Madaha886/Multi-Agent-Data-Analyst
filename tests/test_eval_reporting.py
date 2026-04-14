from pathlib import Path

from multi_agent_analyst.eval.contracts import EvalRecord, EvalScores
from multi_agent_analyst.eval.reporting import build_report, write_report_files


def test_report_writer_creates_json_and_markdown(tmp_path: Path):
    record = EvalRecord(
        question_id=1,
        question="What is total revenue by state?",
        difficulty="beginner",
        technique="groupby",
        expected_task_type="aggregation",
        predicted_task_type="aggregation",
        task_type_reason="Expected aggregation and predicted aggregation.",
        primary_mismatch_reason="none",
        execution_success=True,
        scores=EvalScores(
            execution_success=1.0,
            task_type_match=1.0,
            required_columns_match=1.0,
            operation_intent_match=1.0,
            result_correctness=1.0,
            final_answer_alignment=1.0,
            critique_quality=0.25,
            overall_score=0.9625,
        ),
        issues=[],
        workflow={"final_answer": {"critique_passed": False}},
    )
    report = build_report([record], "Test Benchmark")
    paths = write_report_files(report, str(tmp_path))

    assert Path(paths["json_report"]).exists()
    assert Path(paths["markdown_report"]).exists()
    markdown = Path(paths["markdown_report"]).read_text(encoding="utf-8")
    assert "Baseline Observations" in markdown
    assert "Failure Mode Summary" in markdown
