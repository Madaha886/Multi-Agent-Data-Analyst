"""Pydantic models for agent contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AnalysisPlan(BaseModel):
    task_type: Literal["aggregation", "comparison", "ranking", "trend", "unsupported"]
    sub_questions: list[str] = Field(default_factory=list)
    required_columns: list[str] = Field(default_factory=list)
    expected_operations: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    grouping: list[str] = Field(default_factory=list)
    metric: str | None = None
    derived_columns: list[str] = Field(default_factory=list)
    ranking_limit: int | None = None
    time_grain: str | None = None


class GeneratedQuery(BaseModel):
    code: str
    assumptions: list[str] = Field(default_factory=list)
    selected_columns: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    execution_success: bool
    result_preview: str
    result_shape: str | None = None
    execution_error: str | None = None
    stdout_logs: str | None = None


class AnalysisReport(BaseModel):
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CritiqueFeedback(BaseModel):
    is_valid: bool
    issues: list[str] = Field(default_factory=list)
    revision_needed: bool
    confidence_notes: str


class FinalAnswer(BaseModel):
    question: str
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    result_preview: str
    critique_passed: bool
    critique_issues: list[str] = Field(default_factory=list)
