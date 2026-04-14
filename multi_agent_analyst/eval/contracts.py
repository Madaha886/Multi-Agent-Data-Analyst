"""Pydantic contracts for the evaluation pack."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EvalQuestion(BaseModel):
    id: int
    difficulty: str
    technique: str
    question: str
    hint: str | None = None
    columns_used: list[str] = Field(default_factory=list)
    pandas_approach: str | None = None


class EvalQuestionSet(BaseModel):
    title: str
    description: str | None = None
    dataset: str | None = None
    questions: list[EvalQuestion]


class GoldExpectation(BaseModel):
    question_id: int
    expected_task_type: str
    expected_key_columns: list[str]
    expected_operation_pattern: list[str]
    expected_result_kind: Literal["scalar", "pairs", "rows"]
    expected_result_shape: str | None = None
    reference_result: dict[str, Any]
    acceptable_signals: list[str] = Field(default_factory=list)
    allowed_result_aliases: dict[str, list[str]] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class GoldSet(BaseModel):
    benchmark_name: str
    dataset_path: str
    schema_path: str
    expectations: list[GoldExpectation]


class EvalScores(BaseModel):
    execution_success: float
    task_type_match: float
    required_columns_match: float
    operation_intent_match: float
    result_correctness: float
    final_answer_alignment: float
    critique_quality: float
    overall_score: float


class EvalRecord(BaseModel):
    question_id: int
    question: str
    difficulty: str
    technique: str
    expected_task_type: str
    predicted_task_type: str
    task_type_reason: str | None = None
    primary_mismatch_reason: str | None = None
    execution_success: bool
    scores: EvalScores
    issues: list[str] = Field(default_factory=list)
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    normalized_result: dict[str, Any] | None = None
    workflow: dict[str, Any] = Field(default_factory=dict)


class EvalReport(BaseModel):
    benchmark_name: str
    total_questions: int
    average_scores: dict[str, float]
    counts: dict[str, int]
    mismatch_reason_counts: dict[str, int] = Field(default_factory=dict)
    baseline_observations: list[str] = Field(default_factory=list)
    records: list[EvalRecord]
