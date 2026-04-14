"""Query generation agent."""

from __future__ import annotations

from typing import Any

from multi_agent_analyst.models import AnalysisPlan, GeneratedQuery


def _build_code(plan: AnalysisPlan, question: str) -> GeneratedQuery:
    assumptions: list[str] = []
    selected_columns = list(plan.required_columns)

    if plan.task_type == "unsupported":
        code = (
            "result = 'Unsupported request for v1. Please ask a single aggregation, "
            "comparison, ranking, or trend question grounded in the dataset schema.'"
        )
        assumptions.append("The request falls outside the supported v1 question types.")
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    metric = plan.metric

    if plan.filters and any("proxy" in item.lower() for item in plan.filters):
        assumptions.extend(plan.filters)

    if metric == "sum_amount" and plan.grouping == ["Category"]:
        code = "\n".join(
            [
                "working_df = df.copy()",
                "working_df = working_df[working_df['Amount'].notna()]",
                "result = (working_df.groupby('Category', as_index=False)['Amount'].sum()",
                "    .rename(columns={'Amount': 'total_amount'})",
                "    .sort_values('total_amount', ascending=False))",
            ]
        )
        if plan.ranking_limit:
            code += f"\nresult = result.head({plan.ranking_limit})"
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "count_orders" and plan.derived_columns == ["month"]:
        code = "\n".join(
            [
                "working_df = df.copy()",
                "working_df = working_df[working_df['Date'].notna()]",
                "result = working_df.groupby(working_df['Date'].dt.to_period('M'))['Order ID'].count().sort_index()",
            ]
        )
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "cancel_rate" and plan.grouping == []:
        code = "result = (df['Status'] == 'Cancelled').sum() / len(df) * 100"
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "count_orders" and plan.grouping == ["ship-state"]:
        code = "\n".join(
            [
                "working_df = df.copy()",
                "result = working_df.groupby('ship-state')['Order ID'].count().sort_values(ascending=False)",
            ]
        )
        if plan.ranking_limit:
            code += f"\nresult = result.head({plan.ranking_limit})"
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "sum_qty" and plan.grouping == ["Size"]:
        code = "\n".join(
            [
                "working_df = df.copy()",
                "result = working_df.groupby('Size')['Qty'].sum().sort_values(ascending=False)",
            ]
        )
        if plan.ranking_limit:
            code += f"\nresult = result.head({plan.ranking_limit})"
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "cancel_rate" and plan.grouping == ["Fulfilment"]:
        code = "\n".join(
            [
                "working_df = df.copy()",
                "result = working_df.groupby('Fulfilment').apply(",
                "    lambda group: (group['Status'] == 'Cancelled').sum() / len(group) * 100,",
                "    include_groups=False,",
                ")",
            ]
        )
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "mean_amount" and plan.grouping == ["B2B"]:
        code = "result = df.groupby('B2B')['Amount'].mean()"
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "top_within_group":
        code = "\n".join(
            [
                "working_df = df.copy()",
                "pivot = pd.crosstab(working_df['Category'], working_df['Size'], values=working_df['Qty'], aggfunc='sum').fillna(0)",
                "result = pivot.idxmax(axis=1)",
            ]
        )
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "mean_amount" and plan.derived_columns == ["promotion_used"]:
        code = "\n".join(
            [
                "working_df = df.copy()",
                "working_df['promotion_used'] = working_df['promotion-ids'].notna()",
                "result = working_df.groupby('promotion_used')['Amount'].mean()",
            ]
        )
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "sum_amount" and plan.derived_columns == ["day_of_week"]:
        code = "\n".join(
            [
                "working_df = df.copy()",
                "working_df = working_df[working_df['Date'].notna()]",
                "working_df = working_df[working_df['Amount'].notna()]",
                "result = working_df.groupby(working_df['Date'].dt.day_name())['Amount'].sum().sort_values(ascending=False)",
            ]
        )
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "sum_amount" and plan.derived_columns == ["month"]:
        code = "\n".join(
            [
                "working_df = df.copy()",
                "working_df = working_df[working_df['Amount'].notna()]",
                "working_df = working_df[working_df['Date'].notna()]",
                "result = working_df.groupby(working_df['Date'].dt.to_period('M'))['Amount'].sum().sort_index()",
            ]
        )
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    grouping = plan.grouping[0] if plan.grouping else None
    if metric == "mean_amount" and grouping:
        code = (
            f"result = df.groupby('{grouping}', as_index=False)['Amount'].mean()"
            "\nresult = result.rename(columns={'Amount': 'average_amount'})"
        )
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    if metric == "sum_amount" and grouping:
        code = (
            f"result = df.groupby('{grouping}', as_index=False)['Amount'].sum()"
            "\nresult = result.rename(columns={'Amount': 'total_amount'})"
            "\nresult = result.sort_values(result.columns[-1], ascending=False)"
        )
        if plan.ranking_limit:
            code += f"\nresult = result.head({plan.ranking_limit})"
        return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)

    code = "result = 'Unsupported request for current query templates.'"
    assumptions.append("The request did not match a supported query template.")
    return GeneratedQuery(code=code, assumptions=assumptions, selected_columns=selected_columns)


def query_node(state: dict[str, Any]) -> dict[str, Any]:
    plan = state["analysis_plan"]
    query = _build_code(plan, state["question"])
    return {"generated_query": query}
