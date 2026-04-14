from multi_agent_analyst.graph import run_question


def test_end_to_end_aggregation_question():
    state = run_question(
        "What is total revenue by state?",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )

    assert state.execution_result is not None
    assert state.execution_result.execution_success is True
    assert "ship-state" in state.execution_result.result_preview
    assert state.final_answer is not None


def test_end_to_end_ranking_question():
    state = run_question(
        "What are the top 5 products by sales?",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )

    assert state.analysis_plan.task_type == "ranking"
    assert state.execution_result.execution_success is True


def test_end_to_end_comparison_question():
    state = run_question(
        "Compare average sales across customer segments.",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )

    assert state.analysis_plan.task_type == "comparison"
    assert state.execution_result.execution_success is True


def test_end_to_end_trend_question():
    state = run_question(
        "How did monthly revenue change over time?",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )

    assert state.analysis_plan.task_type == "trend"
    assert state.execution_result.execution_success is True


def test_end_to_end_monthly_order_count_question():
    state = run_question(
        "How does the number of orders change month by month?",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )

    assert state.analysis_plan.metric == "count_orders"
    assert state.execution_result.execution_success is True
    assert "2022-04" in state.execution_result.result_preview


def test_end_to_end_weekday_revenue_question():
    state = run_question(
        "Which day of the week sees the highest total sales revenue?",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )

    assert state.analysis_plan.derived_columns == ["day_of_week"]
    assert state.execution_result.execution_success is True
    assert "Sunday" in state.execution_result.result_preview


def test_negative_unsupported_question():
    state = run_question(
        "Forecast next month's revenue.",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )

    assert state.analysis_plan.task_type == "unsupported"
    assert state.critique_feedback.revision_needed is True


def test_negative_ambiguous_multi_part_question():
    state = run_question(
        "What is total revenue by state and compare average sales across segments?",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )

    assert state.analysis_plan.task_type == "unsupported"


def test_negative_missing_column_concept():
    state = run_question(
        "Compare average sales across loyalty tiers.",
        "dataset/Amazon Sale Report.csv",
        "dataset/schema.json",
    )

    assert state.analysis_plan.task_type == "unsupported"
    assert state.critique_feedback.revision_needed is True
