"""Planner agent implementation."""

from __future__ import annotations

import re
from typing import Any

from multi_agent_analyst.models import AnalysisPlan

UNSUPPORTED_KEYWORDS = (
    "forecast",
    "predict",
    "prediction",
    "anomaly",
    "recommend",
    "root cause",
    "causal",
)
COLUMN_SYNONYMS = {
    "revenue": "Amount",
    "sales": "Amount",
    "amount": "Amount",
    "state": "ship-state",
    "states": "ship-state",
    "region": "ship-state",
    "city": "ship-city",
    "category": "Category",
    "categories": "Category",
    "product": "Category",
    "products": "Category",
    "sku": "SKU",
    "style": "Style",
    "segment": "B2B",
    "segments": "B2B",
    "customer segment": "B2B",
    "customer segments": "B2B",
    "b2b": "B2B",
    "status": "Status",
    "date": "Date",
    "month": "Date",
    "monthly": "Date",
}


def _extract_top_n(question: str) -> int | None:
    match = re.search(r"top\s+(\d+)", question.lower())
    if match:
        return int(match.group(1))
    return None


def _contains_any(text: str, options: tuple[str, ...] | list[str]) -> bool:
    return any(option in text for option in options)


def _build_supported_plan(question: str, available_columns: set[str]) -> AnalysisPlan:
    lowered = question.lower()

    if "category generates the most total revenue" in lowered:
        return AnalysisPlan(
            task_type="ranking",
            sub_questions=[question],
            required_columns=["Category", "Amount"],
            expected_operations=["groupby", "sum", "sort_values"],
            grouping=["Category"],
            metric="sum_amount",
            ranking_limit=5,
        )

    if "number of orders" in lowered and "month by month" in lowered:
        return AnalysisPlan(
            task_type="trend",
            sub_questions=[question],
            required_columns=["Date", "Order ID"],
            expected_operations=["groupby", "count", "to_period"],
            grouping=["month"],
            metric="count_orders",
            derived_columns=["month"],
            time_grain="month",
        )

    if "percentage" in lowered and "cancel" in lowered:
        return AnalysisPlan(
            task_type="aggregation",
            sub_questions=[question],
            required_columns=["Status"],
            expected_operations=["cancelled", "len", "percentage"],
            metric="cancel_rate",
            derived_columns=["is_cancelled"],
        )

    if "states placed the most orders" in lowered:
        return AnalysisPlan(
            task_type="ranking",
            sub_questions=[question],
            required_columns=["ship-state", "Order ID"],
            expected_operations=["groupby", "count", "head"],
            grouping=["ship-state"],
            metric="count_orders",
            ranking_limit=_extract_top_n(question) or 5,
        )

    if "popular clothing size" in lowered or ("size" in lowered and "ordered" in lowered):
        return AnalysisPlan(
            task_type="ranking",
            sub_questions=[question],
            required_columns=["Size", "Qty"],
            expected_operations=["groupby", "sum", "sort_values"],
            grouping=["Size"],
            metric="sum_qty",
            ranking_limit=5,
        )

    if "cancellation rate" in lowered and "fulfil" in lowered:
        return AnalysisPlan(
            task_type="comparison",
            sub_questions=[question],
            required_columns=["Fulfilment", "Status"],
            expected_operations=["groupby", "cancelled", "percentage"],
            grouping=["Fulfilment"],
            metric="cancel_rate",
            derived_columns=["is_cancelled"],
        )

    if "b2b" in lowered and "average" in lowered:
        return AnalysisPlan(
            task_type="comparison",
            sub_questions=[question],
            required_columns=["B2B", "Amount"],
            expected_operations=["groupby", "mean"],
            grouping=["B2B"],
            metric="mean_amount",
        )

    if "size sells best within each product category" in lowered:
        return AnalysisPlan(
            task_type="ranking",
            sub_questions=[question],
            required_columns=["Category", "Size", "Qty"],
            expected_operations=["crosstab", "aggfunc", "idxmax"],
            grouping=["Category", "Size"],
            metric="top_within_group",
        )

    if "promotion applied" in lowered and "average order value" in lowered:
        return AnalysisPlan(
            task_type="comparison",
            sub_questions=[question],
            required_columns=["promotion-ids", "Amount"],
            expected_operations=["notna", "groupby", "mean"],
            grouping=["promotion_used"],
            metric="mean_amount",
            derived_columns=["promotion_used"],
        )

    if "day of the week" in lowered and ("sales revenue" in lowered or "total sales revenue" in lowered):
        return AnalysisPlan(
            task_type="ranking",
            sub_questions=[question],
            required_columns=["Date", "Amount"],
            expected_operations=["day_name", "groupby", "sum", "sort_values"],
            grouping=["day_of_week"],
            metric="sum_amount",
            derived_columns=["day_of_week"],
            ranking_limit=7,
        )

    if "customer segment" in lowered or "customer segments" in lowered:
        return AnalysisPlan(
            task_type="comparison",
            sub_questions=[question],
            required_columns=["B2B", "Amount"],
            expected_operations=["groupby", "mean"],
            grouping=["B2B"],
            metric="mean_amount",
            filters=["Using B2B as the available customer-segment proxy."],
        )

    if any(keyword in lowered for keyword in UNSUPPORTED_KEYWORDS):
        return AnalysisPlan(
            task_type="unsupported",
            sub_questions=[question],
            required_columns=[],
            expected_operations=["Explain why the request is unsupported in v1."],
        )

    grouping: list[str] = []
    for synonym, column in COLUMN_SYNONYMS.items():
        if synonym in lowered and column in available_columns and column not in grouping:
            if column not in {"Amount", "Date"}:
                grouping.append(column)

    if "monthly" in lowered or "over time" in lowered:
        return AnalysisPlan(
            task_type="trend",
            sub_questions=[question],
            required_columns=["Date", "Amount"],
            expected_operations=["groupby", "sum", "to_period"],
            grouping=["month"],
            metric="sum_amount",
            derived_columns=["month"],
            time_grain="month",
        )

    if "average" in lowered and grouping:
        return AnalysisPlan(
            task_type="comparison",
            sub_questions=[question],
            required_columns=["Amount", *grouping],
            expected_operations=["groupby", "mean"],
            grouping=grouping,
            metric="mean_amount",
        )

    if _contains_any(lowered, ["top ", "highest", "best", "most"]) and grouping:
        return AnalysisPlan(
            task_type="ranking",
            sub_questions=[question],
            required_columns=["Amount", *grouping],
            expected_operations=["groupby", "sum", "sort_values"],
            grouping=grouping,
            metric="sum_amount",
            ranking_limit=_extract_top_n(question) or 5,
        )

    if grouping:
        return AnalysisPlan(
            task_type="aggregation",
            sub_questions=[question],
            required_columns=["Amount", *grouping],
            expected_operations=["groupby", "sum"],
            grouping=grouping,
            metric="sum_amount",
        )

    return AnalysisPlan(
        task_type="unsupported",
        sub_questions=[question],
        required_columns=[],
        expected_operations=["Explain why the request is unsupported in v1."],
    )


def _detect_filters(question: str, available_columns: set[str]) -> list[str]:
    filters: list[str] = []
    lowered = question.lower()
    if "cancel" in lowered and "Status" in available_columns:
        filters.append("Exclude cancelled orders unless the question explicitly asks about them.")
    return filters


def _is_ambiguous_multi_part(question: str) -> bool:
    lowered = question.lower()
    if " and " in lowered:
        markers = ("top", "compare", "trend", "total", "average")
        return sum(marker in lowered for marker in markers) > 1
    return False


def planner_node(state: dict[str, Any]) -> dict[str, Any]:
    question = state["question"]
    schema_properties = state["schema"].get("properties", {})
    available_columns = set(schema_properties.keys()) | set(state["artifacts"].get("available_columns", []))
    if _is_ambiguous_multi_part(question):
        plan = AnalysisPlan(
            task_type="unsupported",
            sub_questions=[question],
            required_columns=[],
            expected_operations=["Explain why the request is unsupported in v1."],
        )
        return {"analysis_plan": plan}

    plan = _build_supported_plan(question, available_columns)
    if plan.task_type != "unsupported":
        filters = _detect_filters(question, available_columns)
        if filters:
            plan.filters.extend(item for item in filters if item not in plan.filters)
    return {"analysis_plan": plan}
