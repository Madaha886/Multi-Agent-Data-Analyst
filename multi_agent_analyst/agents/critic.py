"""Critic agent implementation."""

from __future__ import annotations

from typing import Any

from multi_agent_analyst.models import CritiqueFeedback


def critic_node(state: dict[str, Any]) -> dict[str, Any]:
    plan = state["analysis_plan"]
    query = state["generated_query"]
    execution = state["execution_result"]
    question = state["question"].lower()

    issues: list[str] = []
    if plan.task_type == "unsupported":
        issues.append("The request is outside the supported v1 scope.")
    if not execution.execution_success:
        issues.append(f"Execution failed: {execution.execution_error}")
    if execution.execution_success and not execution.result_preview.strip():
        issues.append("Execution succeeded but produced an empty preview.")
    if plan.task_type != "unsupported" and "result =" not in query.code:
        issues.append("Generated code does not assign a final `result` value.")
    if plan.task_type == "trend" and plan.time_grain != "month":
        issues.append("Trend analysis did not preserve the expected monthly time grain.")
    if "day of the week" in question and "day_of_week" not in plan.derived_columns:
        issues.append("The plan did not model the required day-of-week derived column.")
    if "month by month" in question and "month" not in plan.derived_columns:
        issues.append("The plan did not model the required month derived column.")
    if "promotion" in question and "promotion_used" not in plan.derived_columns:
        issues.append("The plan did not derive promotion usage from `promotion-ids`.")
    if "cancel" in question and plan.metric != "cancel_rate" and "cancelled" in question:
        issues.append("The plan did not use a cancellation-rate metric for a cancellation-rate question.")
    if "number of orders" in question and plan.metric not in {"count_orders", "count_rows"}:
        issues.append("The plan did not use an order-count metric for an order-count question.")
    if "size sells best within each product category" in question and plan.metric != "top_within_group":
        issues.append("The plan did not use a within-group best-size analysis.")

    critique = CritiqueFeedback(
        is_valid=not issues,
        issues=issues,
        revision_needed=bool(issues),
        confidence_notes=(
            "High confidence when execution succeeds and the request maps cleanly to the known schema."
            if not issues
            else "Confidence is reduced because the result depends on limitations or execution issues."
        ),
    )
    return {"critique_feedback": critique}
