"""CLI for the multi-agent analytics assistant."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from multi_agent_analyst.graph import run_question


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the multi-agent data analyst assistant.")
    parser.add_argument("--question", required=True, help="Analytics question to answer.")
    parser.add_argument(
        "--dataset",
        default=str(Path("dataset") / "Amazon Sale Report.csv"),
        help="Path to the CSV dataset.",
    )
    parser.add_argument(
        "--schema",
        default=str(Path("dataset") / "schema.json"),
        help="Path to the dataset schema JSON file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full workflow state as JSON instead of a pretty console layout.",
    )
    return parser


def _print_pretty(state) -> None:
    print("== Analysis Plan ==")
    print(state.analysis_plan.model_dump_json(indent=2))
    print("\n== Generated Code ==")
    print(state.generated_query.code)
    print("\n== Execution Result ==")
    print(state.execution_result.model_dump_json(indent=2))
    print("\n== Analysis Report ==")
    print(state.analysis_report.model_dump_json(indent=2))
    print("\n== Critique ==")
    print(state.critique_feedback.model_dump_json(indent=2))
    print("\n== Final Answer ==")
    print(state.final_answer.model_dump_json(indent=2))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    state = run_question(args.question, args.dataset, args.schema)
    if args.json:
        print(json.dumps(state.model_dump(mode="json", by_alias=True), indent=2, default=str))
        return
    _print_pretty(state)


if __name__ == "__main__":
    main()
