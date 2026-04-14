import json
from pathlib import Path

import pytest

from multi_agent_analyst.eval.run import evaluate_question_set


def test_evaluate_question_set_creates_reports(tmp_path: Path):
    report = evaluate_question_set(
        questions_path="dataset/questions.json",
        gold_path="dataset/eval_gold.json",
        dataset_path="dataset/Amazon Sale Report.csv",
        schema_path="dataset/schema.json",
        output_dir=str(tmp_path),
    )

    assert report.total_questions == 10
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "report.md").exists()
    payload = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert payload["total_questions"] == 10
    assert "average_scores" in payload
    assert payload["counts"]["execution_success"] == 10
    assert payload["counts"]["task_type_match"] >= 9
    assert payload["counts"]["high_result_correctness"] >= 8
    assert payload["counts"]["critique_passed"] >= 8


def test_evaluate_question_set_raises_for_missing_gold(tmp_path: Path):
    broken_gold = tmp_path / "broken_gold.json"
    broken_gold.write_text(
        json.dumps(
            {
                "benchmark_name": "Broken",
                "dataset_path": "dataset/Amazon Sale Report.csv",
                "schema_path": "dataset/schema.json",
                "expectations": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        evaluate_question_set(
            questions_path="dataset/questions.json",
            gold_path=str(broken_gold),
            dataset_path="dataset/Amazon Sale Report.csv",
            schema_path="dataset/schema.json",
            output_dir=str(tmp_path / "out"),
        )
