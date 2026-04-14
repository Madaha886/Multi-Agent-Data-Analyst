import pytest
from pydantic import ValidationError

from multi_agent_analyst.models import (
    AnalysisPlan,
    AnalysisReport,
    CritiqueFeedback,
    ExecutionResult,
    FinalAnswer,
    GeneratedQuery,
)


def test_contract_models_accept_valid_payloads():
    AnalysisPlan(task_type="aggregation")
    GeneratedQuery(code="result = 1")
    ExecutionResult(execution_success=True, result_preview="1")
    AnalysisReport(summary="ok")
    CritiqueFeedback(is_valid=True, revision_needed=False, confidence_notes="high")
    FinalAnswer(
        question="q",
        summary="s",
        key_findings=[],
        result_preview="1",
        critique_passed=True,
        critique_issues=[],
    )


def test_analysis_plan_rejects_invalid_task_type():
    with pytest.raises(ValidationError):
        AnalysisPlan(task_type="forecast")
