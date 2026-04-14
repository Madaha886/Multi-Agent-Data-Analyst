from multi_agent_analyst.ui.helpers import (
    load_demo_questions,
    preview_to_dataframe,
    select_demo_presets,
    workflow_graph_dot,
    workflow_sections,
)
from multi_agent_analyst.graph import run_question


def test_load_demo_questions_reads_question_set():
    questions = load_demo_questions()
    assert len(questions) >= 4
    assert "question" in questions[0]


def test_select_demo_presets_returns_curated_examples():
    presets = select_demo_presets(load_demo_questions())
    assert len(presets) == 4
    assert any("month by month" in item["question"] for item in presets)


def test_workflow_graph_dot_contains_full_pipeline():
    dot = workflow_graph_dot(active_step="Planner")
    assert "Question" in dot
    assert "Response Composer" in dot
    assert '"Question" -> "Planner"' in dot


def test_preview_to_dataframe_parses_tabular_output():
    preview = "ship-state  total_amount\nKARNATAKA  100.0\nDELHI  50.0"
    df = preview_to_dataframe(preview)
    assert df is not None
    assert not df.empty


def test_workflow_sections_include_core_artifacts():
    state = run_question(
        "Which product category generates the most total revenue?",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )
    sections = workflow_sections(state)
    assert "Analysis Plan" in sections
    assert "Generated Code" in sections
