"""Report writers for evaluation runs."""

from __future__ import annotations

import json
from pathlib import Path

from .contracts import EvalRecord, EvalReport


def build_report(records: list[EvalRecord], benchmark_name: str) -> EvalReport:
    total = len(records)
    average_scores = {}
    if records:
        score_keys = records[0].scores.model_dump().keys()
        for key in score_keys:
            average_scores[key] = round(
                sum(record.scores.model_dump()[key] for record in records) / total,
                4,
            )

    execution_success_count = sum(1 for record in records if record.execution_success)
    task_type_match_count = sum(1 for record in records if record.scores.task_type_match == 1.0)
    critique_pass_count = sum(
        1
        for record in records
        if record.workflow.get("final_answer", {}).get("critique_passed") is True
    )
    high_correctness_count = sum(1 for record in records if record.scores.result_correctness >= 0.8)
    mismatch_reason_counts: dict[str, int] = {}
    for record in records:
        reason = record.primary_mismatch_reason or "none"
        mismatch_reason_counts[reason] = mismatch_reason_counts.get(reason, 0) + 1

    baseline_observations = [
        f"{execution_success_count}/{total} questions executed successfully.",
        f"{task_type_match_count}/{total} questions matched the expected task type.",
        f"{critique_pass_count}/{total} questions passed critique.",
        f"{high_correctness_count}/{total} questions achieved high result correctness (>= 0.8).",
    ]

    return EvalReport(
        benchmark_name=benchmark_name,
        total_questions=total,
        average_scores=average_scores,
        counts={
            "execution_success": execution_success_count,
            "task_type_match": task_type_match_count,
            "critique_passed": critique_pass_count,
            "high_result_correctness": high_correctness_count,
        },
        mismatch_reason_counts=mismatch_reason_counts,
        baseline_observations=baseline_observations,
        records=records,
    )


def write_report_files(report: EvalReport, output_dir: str) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    questions_dir = output_path / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)

    json_report_path = output_path / "report.json"
    markdown_report_path = output_path / "report.md"

    with json_report_path.open("w", encoding="utf-8") as handle:
        json.dump(report.model_dump(mode="json"), handle, indent=2)
        handle.write("\n")

    with markdown_report_path.open("w", encoding="utf-8") as handle:
        handle.write(f"# {report.benchmark_name}\n\n")
        handle.write(f"- Total questions: {report.total_questions}\n")
        for name, value in report.average_scores.items():
            handle.write(f"- Average {name}: {value:.4f}\n")
        handle.write("\n## Baseline Observations\n\n")
        for line in report.baseline_observations:
            handle.write(f"- {line}\n")
        handle.write("\n## Failure Mode Summary\n\n")
        for reason, count in sorted(report.mismatch_reason_counts.items()):
            handle.write(f"- {reason}: {count}\n")
        handle.write("\n## Per Question Results\n\n")
        handle.write("| ID | Technique | Expected | Predicted | Overall | Result | Reason |\n")
        handle.write("| --- | --- | --- | --- | ---: | ---: | --- |\n")
        for record in report.records:
            reason_text = record.primary_mismatch_reason or ""
            handle.write(
                f"| {record.question_id} | {record.technique} | {record.expected_task_type} | "
                f"{record.predicted_task_type} | {record.scores.overall_score:.4f} | "
                f"{record.scores.result_correctness:.4f} | {reason_text} |\n"
            )

    artifact_paths = {
        "json_report": str(json_report_path),
        "markdown_report": str(markdown_report_path),
    }

    for record in report.records:
        question_path = questions_dir / f"question_{record.question_id}.json"
        with question_path.open("w", encoding="utf-8") as handle:
            json.dump(record.model_dump(mode="json"), handle, indent=2)
            handle.write("\n")
        record.artifact_paths["question_json"] = str(question_path)

    with json_report_path.open("w", encoding="utf-8") as handle:
        json.dump(report.model_dump(mode="json"), handle, indent=2)
        handle.write("\n")

    return artifact_paths
