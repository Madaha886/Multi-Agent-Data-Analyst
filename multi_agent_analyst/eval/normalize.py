"""Normalization helpers for evaluation comparison."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _to_json_value(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.Period):
        return str(value)
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:  # noqa: BLE001
            return str(value)
    return value


def normalize_result(value: Any) -> dict[str, Any]:
    if isinstance(value, pd.DataFrame):
        records = []
        for record in value.to_dict(orient="records"):
            records.append({key: _to_json_value(item) for key, item in record.items()})
        return {
            "kind": "rows",
            "columns": [str(column) for column in value.columns],
            "row_count": int(len(value)),
            "records": records,
        }

    if isinstance(value, pd.Series):
        return {
            "kind": "pairs",
            "row_count": int(len(value)),
            "pairs": [[str(index), _to_json_value(item)] for index, item in value.items()],
        }

    return {
        "kind": "scalar",
        "value": _to_json_value(value),
    }
