"""Helpers for the Streamlit demo layer."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from multi_agent_analyst.models import WorkflowState

DEFAULT_QUESTIONS_PATH = Path("dataset/questions.json")
DEFAULT_DATASET_PATH = str(Path("dataset") / "Amazon Sale Report.csv")
DEFAULT_SCHEMA_PATH = str(Path("dataset") / "schema.json")

WORKFLOW_STEPS = [
    "Question",
    "Planner",
    "Query Generator",
    "Safe Executor",
    "Analyst",
    "Critic",
    "Response Composer",
]


def load_demo_questions(path: str = str(DEFAULT_QUESTIONS_PATH)) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["questions"]


def select_demo_presets(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preferred_ids = [1, 2, 6, 3]
    by_id = {item["id"]: item for item in questions}
    return [by_id[qid] for qid in preferred_ids if qid in by_id]


def workflow_graph_dot(active_step: str | None = None) -> str:
    lines = [
        "digraph Workflow {",
        "rankdir=LR;",
        'node [shape=box style="rounded,filled" fontname="Helvetica" color="#1f2937" fillcolor="#f3f4f6"];',
        'edge [color="#6b7280"];',
    ]
    for step in WORKFLOW_STEPS:
        fill = "#dbeafe" if step == active_step else "#f3f4f6"
        lines.append(f'"{step}" [fillcolor="{fill}"];')
    for left, right in zip(WORKFLOW_STEPS, WORKFLOW_STEPS[1:]):
        lines.append(f'"{left}" -> "{right}";')
    lines.append("}")
    return "\n".join(lines)


def status_badges(state: WorkflowState) -> dict[str, str]:
    return {
        "Task Type": state.analysis_plan.task_type if state.analysis_plan else "unknown",
        "Execution": "passed" if state.execution_result and state.execution_result.execution_success else "failed",
        "Critique": "passed" if state.final_answer and state.final_answer.critique_passed else "needs review",
    }


def preview_to_dataframe(result_preview: str) -> pd.DataFrame | None:
    text = result_preview.strip()
    if not text or "\n" not in text:
        return None
    try:
        return pd.read_fwf(StringIO(text))
    except Exception:  # noqa: BLE001
        return None


def workflow_sections(state: WorkflowState) -> dict[str, str]:
    return {
        "Analysis Plan": state.analysis_plan.model_dump_json(indent=2) if state.analysis_plan else "{}",
        "Generated Code": state.generated_query.code if state.generated_query else "",
        "Execution Result": state.execution_result.model_dump_json(indent=2) if state.execution_result else "{}",
        "Analysis Report": state.analysis_report.model_dump_json(indent=2) if state.analysis_report else "{}",
        "Critique": state.critique_feedback.model_dump_json(indent=2) if state.critique_feedback else "{}",
        "Final Answer": state.final_answer.model_dump_json(indent=2) if state.final_answer else "{}",
    }
