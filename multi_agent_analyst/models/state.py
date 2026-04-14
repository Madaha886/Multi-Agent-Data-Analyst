"""Shared workflow state."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    AnalysisPlan,
    AnalysisReport,
    CritiqueFeedback,
    ExecutionResult,
    FinalAnswer,
    GeneratedQuery,
)


class WorkflowState(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str
    dataset_path: str
    schema_path: str
    dataset_schema: dict[str, Any] = Field(default_factory=dict, alias="schema")
    analysis_plan: AnalysisPlan | None = None
    generated_query: GeneratedQuery | None = None
    execution_result: ExecutionResult | None = None
    analysis_report: AnalysisReport | None = None
    critique_feedback: CritiqueFeedback | None = None
    final_answer: FinalAnswer | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
