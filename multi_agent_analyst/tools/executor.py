"""Safe execution boundary for generated pandas code."""

from __future__ import annotations

import ast
import builtins
import contextlib
import io
from typing import Any

import pandas as pd

from multi_agent_analyst.models import ExecutionResult

FORBIDDEN_CALLS = {"__import__", "eval", "exec", "open", "compile", "input", "breakpoint"}
FORBIDDEN_NAMES = {
    "os",
    "sys",
    "subprocess",
    "pathlib",
    "socket",
    "requests",
    "shutil",
    "importlib",
}
FORBIDDEN_ATTRIBUTES = {"system", "popen", "remove", "unlink", "rmdir"}


class UnsafeCodeError(ValueError):
    """Raised when generated code violates the safe executor policy."""


def _validate_ast(code: str) -> None:
    tree = ast.parse(code, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise UnsafeCodeError("Imports are not allowed in generated code.")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                raise UnsafeCodeError(f"Call to forbidden function: {node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_ATTRIBUTES:
                raise UnsafeCodeError(f"Call to forbidden attribute: {node.func.attr}")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise UnsafeCodeError(f"Forbidden name referenced: {node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise UnsafeCodeError("Dunder attribute access is not allowed.")


def _preview_result(result: Any) -> tuple[str, str | None]:
    if isinstance(result, pd.DataFrame):
        return result.head(10).to_string(index=False), str(result.shape)
    if isinstance(result, pd.Series):
        preview = result.head(10).to_string()
        return preview, str(result.shape)
    return str(result), None


def execute_generated_code_with_result(code: str, df: pd.DataFrame) -> tuple[ExecutionResult, Any | None]:
    try:
        _validate_ast(code)
    except UnsafeCodeError as exc:
        return (
            ExecutionResult(
                execution_success=False,
                result_preview="",
                result_shape=None,
                execution_error=str(exc),
                stdout_logs=None,
            ),
            None,
        )

    stdout_buffer = io.StringIO()
    namespace = {
        "__builtins__": {
            "len": builtins.len,
            "min": builtins.min,
            "max": builtins.max,
            "sum": builtins.sum,
            "sorted": builtins.sorted,
            "round": builtins.round,
            "list": builtins.list,
            "dict": builtins.dict,
            "set": builtins.set,
            "tuple": builtins.tuple,
            "print": builtins.print,
            "str": builtins.str,
            "int": builtins.int,
            "float": builtins.float,
            "bool": builtins.bool,
        },
        "pd": pd,
        "df": df.copy(),
    }

    try:
        with contextlib.redirect_stdout(stdout_buffer):
            exec(compile(code, "<generated-query>", "exec"), namespace, namespace)
        if "result" not in namespace:
            raise ValueError("Generated code did not assign a `result` variable.")
        raw_result = namespace["result"]
        preview, shape = _preview_result(raw_result)
        return (
            ExecutionResult(
                execution_success=True,
                result_preview=preview,
                result_shape=shape,
                execution_error=None,
                stdout_logs=stdout_buffer.getvalue() or None,
            ),
            raw_result,
        )
    except Exception as exc:  # noqa: BLE001
        return (
            ExecutionResult(
                execution_success=False,
                result_preview="",
                result_shape=None,
                execution_error=f"{type(exc).__name__}: {exc}",
                stdout_logs=stdout_buffer.getvalue() or None,
            ),
            None,
        )


def execute_generated_code(code: str, df: pd.DataFrame) -> ExecutionResult:
    execution_result, _ = execute_generated_code_with_result(code, df)
    return execution_result
