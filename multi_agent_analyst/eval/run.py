"""CLI and orchestration for evaluation runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from multi_agent_analyst.graph import run_question
from multi_agent_analyst.tools.dataset import load_dataset_bundle
from multi_agent_analyst.tools.executor import execute_generated_code_with_result

from .contracts import EvalRecord
from .loader import load_gold_set, load_question_set
from .normalize import normalize_result
from .reporting import build_report, write_report_files
from .scoring import build_scores


def evaluate_question_set(
    *,
    questions_path: str,
    gold_path: str,
    dataset_path: str,
    schema_path: str,
    output_dir: str,
):
    question_set = load_question_set(questions_path)
    gold_set = load_gold_set(gold_path)
    gold_by_id = {expectation.question_id: expectation for expectation in gold_set.expectations}
    dataset_bundle = load_dataset_bundle(dataset_path, schema_path)

    records: list[EvalRecord] = []
    for question in question_set.questions:
        if question.id not in gold_by_id:
            raise ValueError(f"Missing gold expectation for question ID {question.id}")

        gold = gold_by_id[question.id]
        state = run_question(question.question, dataset_path, schema_path)
        execution_result, raw_result = execute_generated_code_with_result(
            state.generated_query.code,
            dataset_bundle.dataframe,
        )
        normalized_result = normalize_result(raw_result) if execution_result.execution_success else None
        workflow = state.model_dump(mode="json", by_alias=True)
        scores = build_scores(
            execution_success=execution_result.execution_success,
            predicted_task_type=state.analysis_plan.task_type,
            predicted_columns=state.analysis_plan.required_columns,
            code=state.generated_query.code,
            actual_artifact=normalized_result,
            final_answer=workflow["final_answer"],
            critique_feedback=workflow["critique_feedback"],
            gold=gold,
        )

        issues = []
        if scores.task_type_match < 1.0:
            issues.append(f"Expected task type `{gold.expected_task_type}` but got `{state.analysis_plan.task_type}`.")
        if scores.required_columns_match < 1.0:
            issues.append("Required columns did not fully match the gold expectation.")
        if scores.result_correctness < 0.8:
            issues.append("Result correctness fell below the benchmark threshold.")
        if workflow["final_answer"]["critique_passed"] is False:
            issues.append("The final answer did not pass critique.")

        if not execution_result.execution_success:
            primary_mismatch_reason = "execution_failure"
        elif scores.result_correctness < 0.8:
            if scores.required_columns_match < 1.0:
                primary_mismatch_reason = "wrong_metric_or_columns"
            elif scores.operation_intent_match < 1.0:
                primary_mismatch_reason = "wrong_operation_pattern"
            else:
                primary_mismatch_reason = "result_incorrect"
        elif scores.task_type_match < 1.0:
            primary_mismatch_reason = "taxonomy_mismatch"
        elif workflow["final_answer"]["critique_passed"] is False:
            primary_mismatch_reason = "overly_strict_critique"
        else:
            primary_mismatch_reason = "none"

        task_type_reason = (
            f"Expected `{gold.expected_task_type}` and predicted `{state.analysis_plan.task_type}`."
        )

        records.append(
            EvalRecord(
                question_id=question.id,
                question=question.question,
                difficulty=question.difficulty,
                technique=question.technique,
                expected_task_type=gold.expected_task_type,
                predicted_task_type=state.analysis_plan.task_type,
                task_type_reason=task_type_reason,
                primary_mismatch_reason=primary_mismatch_reason,
                execution_success=execution_result.execution_success,
                scores=scores,
                issues=issues,
                normalized_result=normalized_result,
                workflow=workflow,
            )
        )

    report = build_report(records, gold_set.benchmark_name)
    artifact_paths = write_report_files(report, output_dir)

    for record in report.records:
        record.artifact_paths.update(artifact_paths)

    report = build_report(report.records, gold_set.benchmark_name)
    write_report_files(report, output_dir)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the evaluation pack for the bundled question set.")
    parser.add_argument("--questions", default="dataset/questions.json")
    parser.add_argument("--gold", default="dataset/eval_gold.json")
    parser.add_argument("--dataset", default="dataset/Amazon Sale Report.csv")
    parser.add_argument("--schema", default="dataset/schema.json")
    parser.add_argument("--output-dir", default=str(Path("artifacts") / "eval_smoke"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = evaluate_question_set(
        questions_path=args.questions,
        gold_path=args.gold,
        dataset_path=args.dataset,
        schema_path=args.schema,
        output_dir=args.output_dir,
    )
    print(json.dumps(report.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
