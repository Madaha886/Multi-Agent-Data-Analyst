"""LangGraph orchestration."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from multi_agent_analyst.agents import (
    analyst_node,
    composer_node,
    critic_node,
    planner_node,
    query_node,
)
from multi_agent_analyst.models import WorkflowState
from multi_agent_analyst.tools import execute_generated_code, load_dataset_bundle


class GraphState(TypedDict, total=False):
    question: str
    dataset_path: str
    schema_path: str
    schema: dict[str, Any]
    analysis_plan: Any
    generated_query: Any
    execution_result: Any
    analysis_report: Any
    critique_feedback: Any
    final_answer: Any
    artifacts: dict[str, Any]


def dataset_loader_node(state: GraphState) -> GraphState:
    bundle = load_dataset_bundle(state["dataset_path"], state["schema_path"])
    return {
        "schema": bundle.schema,
        "artifacts": {
            **state.get("artifacts", {}),
            "dataframe": bundle.dataframe,
            "cleaned_columns": bundle.cleaned_columns,
            "available_columns": list(bundle.dataframe.columns),
        },
    }


def executor_node(state: GraphState) -> GraphState:
    df = state["artifacts"]["dataframe"]
    execution = execute_generated_code(state["generated_query"].code, df)
    return {"execution_result": execution}


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("load_dataset", dataset_loader_node)
    graph.add_node("planner", planner_node)
    graph.add_node("query", query_node)
    graph.add_node("executor", executor_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("critic", critic_node)
    graph.add_node("composer", composer_node)

    graph.add_edge(START, "load_dataset")
    graph.add_edge("load_dataset", "planner")
    graph.add_edge("planner", "query")
    graph.add_edge("query", "executor")
    graph.add_edge("executor", "analyst")
    graph.add_edge("analyst", "critic")
    graph.add_edge("critic", "composer")
    graph.add_edge("composer", END)
    return graph.compile()


def run_question(question: str, dataset_path: str, schema_path: str) -> WorkflowState:
    app = build_graph()
    result = app.invoke(
        {
            "question": question,
            "dataset_path": dataset_path,
            "schema_path": schema_path,
            "artifacts": {},
        }
    )
    artifacts = dict(result.get("artifacts", {}))
    dataframe = artifacts.pop("dataframe", None)
    if dataframe is not None:
        artifacts["dataset_shape"] = list(dataframe.shape)
    result["artifacts"] = artifacts
    return WorkflowState(**result)
