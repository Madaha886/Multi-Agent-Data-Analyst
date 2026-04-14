"""Analyst agent implementation."""

from __future__ import annotations

from typing import Any

from multi_agent_analyst.models import AnalysisReport


def analyst_node(state: dict[str, Any]) -> dict[str, Any]:
    execution = state["execution_result"]
    plan = state["analysis_plan"]

    if not execution.execution_success:
        report = AnalysisReport(
            summary="The analysis did not complete successfully, so no supported answer can be given.",
            key_findings=[],
            limitations=[execution.execution_error or "Unknown execution failure."],
        )
        return {"analysis_report": report}

    summary = f"The analysis completed for a {plan.task_type} question."
    if plan.task_type == "unsupported":
        summary = "The request is outside the supported v1 scope."

    findings = [f"Result preview:\n{execution.result_preview}"]
    if execution.result_shape:
        findings.append(f"Result shape: {execution.result_shape}")

    limitations: list[str] = []
    if plan.task_type == "unsupported":
        limitations.append("v1 only supports single aggregation, comparison, ranking, or trend questions.")
    if state["generated_query"].assumptions:
        limitations.extend(state["generated_query"].assumptions)

    report = AnalysisReport(summary=summary, key_findings=findings, limitations=limitations)
    return {"analysis_report": report}
