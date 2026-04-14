"""Final response composer."""

from __future__ import annotations

from typing import Any

from multi_agent_analyst.models import FinalAnswer


def composer_node(state: dict[str, Any]) -> dict[str, Any]:
    report = state["analysis_report"]
    critique = state["critique_feedback"]
    execution = state["execution_result"]

    final = FinalAnswer(
        question=state["question"],
        summary=report.summary,
        key_findings=report.key_findings,
        result_preview=execution.result_preview,
        critique_passed=critique.is_valid,
        critique_issues=critique.issues,
    )
    return {"final_answer": final}
