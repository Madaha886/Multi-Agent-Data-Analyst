from multi_agent_analyst.agents.analyst import analyst_node
from multi_agent_analyst.agents.critic import critic_node
from multi_agent_analyst.agents.planner import planner_node
from multi_agent_analyst.agents.query_agent import query_node
from multi_agent_analyst.models import ExecutionResult


def test_planner_returns_supported_task_type():
    state = {
        "question": "What are the top 5 categories by revenue?",
        "schema": {"properties": {"Amount": {}, "Category": {}, "ship-state": {}, "Date": {}}},
        "artifacts": {"available_columns": ["Amount", "Category", "ship-state", "Date"]},
    }
    result = planner_node(state)

    assert result["analysis_plan"].task_type == "ranking"
    assert "Category" in result["analysis_plan"].grouping
    assert result["analysis_plan"].metric == "sum_amount"


def test_query_generator_assigns_result():
    state = {
        "question": "Compare average sales across customer segments.",
        "analysis_plan": planner_node(
            {
                "question": "Compare average sales across customer segments.",
                "schema": {"properties": {"Amount": {}, "B2B": {}, "ship-state": {}}},
                "artifacts": {"available_columns": ["Amount", "B2B", "ship-state"]},
            }
        )["analysis_plan"],
    }
    result = query_node(state)

    assert "result =" in result["generated_query"].code
    assert "mean" in result["generated_query"].code


def test_analyst_and_critic_return_structured_outputs():
    state = {
        "question": "What is total revenue by state?",
        "analysis_plan": planner_node(
            {
                "question": "What is total revenue by state?",
                "schema": {"properties": {"Amount": {}, "ship-state": {}}},
                "artifacts": {"available_columns": ["Amount", "ship-state"]},
            }
        )["analysis_plan"],
        "generated_query": query_node(
            {
                "question": "What is total revenue by state?",
                "analysis_plan": planner_node(
                    {
                        "question": "What is total revenue by state?",
                        "schema": {"properties": {"Amount": {}, "ship-state": {}}},
                        "artifacts": {"available_columns": ["Amount", "ship-state"]},
                    }
                )["analysis_plan"],
            }
        )["generated_query"],
        "execution_result": ExecutionResult(
            execution_success=True,
            result_preview="ship-state  total_amount\nKARNATAKA        100.0",
            result_shape="(1, 2)",
        ),
    }

    analysis = analyst_node(state)
    critique = critic_node({**state, **analysis})

    assert analysis["analysis_report"].summary
    assert isinstance(critique["critique_feedback"].issues, list)


def test_planner_covers_benchmark_patterns():
    cases = [
        ("How does the number of orders change month by month?", "trend", "count_orders", ["month"]),
        ("What percentage of all orders were cancelled?", "aggregation", "cancel_rate", ["is_cancelled"]),
        ("Does Amazon-fulfilled shipping have a lower cancellation rate than merchant-fulfilled?", "comparison", "cancel_rate", ["is_cancelled"]),
        ("Which size sells best within each product category?", "ranking", "top_within_group", []),
        ("Do orders with a promotion applied have a higher or lower average order value?", "comparison", "mean_amount", ["promotion_used"]),
        ("Which day of the week sees the highest total sales revenue?", "ranking", "sum_amount", ["day_of_week"]),
    ]
    schema = {
        "properties": {
            "Amount": {},
            "Category": {},
            "Date": {},
            "Order ID": {},
            "Status": {},
            "ship-state": {},
            "Size": {},
            "Qty": {},
            "Fulfilment": {},
            "B2B": {},
            "promotion-ids": {},
        }
    }
    artifacts = {"available_columns": list(schema["properties"].keys())}
    for question, task_type, metric, derived in cases:
        result = planner_node({"question": question, "schema": schema, "artifacts": artifacts})
        assert result["analysis_plan"].task_type == task_type
        assert result["analysis_plan"].metric == metric
        assert result["analysis_plan"].derived_columns == derived
