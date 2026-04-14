"""Streamlit application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from multi_agent_analyst.graph import run_question

from multi_agent_analyst.ui.helpers import (
    DEFAULT_DATASET_PATH,
    DEFAULT_SCHEMA_PATH,
    load_demo_questions,
    preview_to_dataframe,
    select_demo_presets,
    status_badges,
    workflow_graph_dot,
    workflow_sections,
)


def _render_sidebar() -> str:
    st.sidebar.title("Demo Questions")
    questions = load_demo_questions()
    presets = select_demo_presets(questions)
    preset_labels = {item["question"]: item for item in presets}
    selected = st.sidebar.radio(
        "Preset examples",
        options=["Custom question", *preset_labels.keys()],
        index=0,
    )
    if selected == "Custom question":
        return ""
    preset = preset_labels[selected]
    st.sidebar.caption(f"{preset['technique']} | {preset['difficulty']}")
    st.sidebar.write(preset.get("hint", ""))
    return preset["question"]


def _render_status_cards(state) -> None:
    badges = status_badges(state)
    cols = st.columns(len(badges))
    for idx, (label, value) in enumerate(badges.items()):
        cols[idx].metric(label, value)


def _render_results(state) -> None:
    st.subheader("Answer")
    st.info(state.final_answer.summary)
    _render_status_cards(state)

    preview_df = preview_to_dataframe(state.final_answer.result_preview)
    if preview_df is not None:
        st.subheader("Result Preview")
        st.dataframe(preview_df, use_container_width=True)
    else:
        st.subheader("Result Preview")
        st.code(state.final_answer.result_preview or "No preview available.", language="text")

    st.subheader("Workflow Artifacts")
    tabs = st.tabs(list(workflow_sections(state).keys()))
    for tab, (title, content) in zip(tabs, workflow_sections(state).items(), strict=True):
        with tab:
            if title == "Generated Code":
                st.code(content, language="python")
            else:
                st.code(content, language="json")


def build_app() -> None:
    st.set_page_config(
        page_title="Multi-Agent Data Analyst Assistant",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Multi-Agent Data Analyst Assistant")
    st.write(
        "Explore the full analytics workflow from natural-language question to plan, code, result, critique, and final answer."
    )

    preset_question = _render_sidebar()

    left, right = st.columns([1.2, 1.0], gap="large")
    with left:
        st.subheader("Ask a Question")
        default_question = preset_question or "Which product category generates the most total revenue?"
        question = st.text_area("Question", value=default_question, height=110)
        run_clicked = st.button("Run analysis", type="primary")

        st.caption(f"Dataset: {DEFAULT_DATASET_PATH}")
        st.caption(f"Schema: {DEFAULT_SCHEMA_PATH}")

    with right:
        st.subheader("Workflow Diagram")
        st.graphviz_chart(workflow_graph_dot(active_step="Response Composer"), use_container_width=True)

    if run_clicked:
        with st.spinner("Running the pipeline..."):
            state = run_question(
                question=question,
                dataset_path=DEFAULT_DATASET_PATH,
                schema_path=DEFAULT_SCHEMA_PATH,
            )
        _render_results(state)
    else:
        st.subheader("Demo Flow")
        st.write(
            "Choose a preset from the sidebar or type your own question, then run the analysis to see every stage of the pipeline."
        )


def main() -> None:
    build_app()


if __name__ == "__main__":
    main()
