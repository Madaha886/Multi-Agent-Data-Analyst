import pandas as pd

from multi_agent_analyst.tools.executor import execute_generated_code


def test_executor_supports_dataframe_result():
    df = pd.DataFrame({"Amount": [10, 20], "Category": ["A", "B"]})
    result = execute_generated_code("result = df.groupby('Category', as_index=False)['Amount'].sum()", df)

    assert result.execution_success is True
    assert "Category" in result.result_preview
    assert result.result_shape == "(2, 2)"


def test_executor_supports_scalar_result():
    df = pd.DataFrame({"Amount": [10, 20]})
    result = execute_generated_code("result = df['Amount'].sum()", df)

    assert result.execution_success is True
    assert result.result_preview == "30"


def test_executor_captures_runtime_errors():
    df = pd.DataFrame({"Amount": [10, 20]})
    result = execute_generated_code("result = df['Missing'].sum()", df)

    assert result.execution_success is False
    assert "Missing" in result.execution_error


def test_executor_blocks_unsafe_code():
    df = pd.DataFrame({"Amount": [10, 20]})
    result = execute_generated_code("import os\nresult = 1", df)

    assert result.execution_success is False
    assert "Imports are not allowed" in result.execution_error
