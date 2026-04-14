"""Dataset loading and schema normalization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(slots=True)
class DatasetBundle:
    dataframe: pd.DataFrame
    schema: dict[str, Any]
    cleaned_columns: dict[str, str]


def load_dataset_bundle(dataset_path: str, schema_path: str) -> DatasetBundle:
    dataset_file = Path(dataset_path)
    schema_file = Path(schema_path)

    with schema_file.open(encoding="utf-8") as handle:
        schema = json.load(handle)

    df = pd.read_csv(dataset_file, low_memory=False)
    original_columns = list(df.columns)
    cleaned = [column.strip() if isinstance(column, str) else column for column in original_columns]
    rename_map = {
        original: normalized
        for original, normalized in zip(original_columns, cleaned, strict=True)
        if original != normalized
    }
    if rename_map:
        df = df.rename(columns=rename_map)

    unnamed_columns = [column for column in df.columns if isinstance(column, str) and column.startswith("Unnamed:")]
    if unnamed_columns:
        df = df.drop(columns=unnamed_columns)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], format="%m-%d-%y", errors="coerce")

    cleaned_columns = {
        original: normalized
        for original, normalized in zip(original_columns, cleaned, strict=True)
    }

    if "properties" in schema and "Sales Channel " in schema["properties"]:
        schema["properties"]["Sales Channel"] = schema["properties"].pop("Sales Channel ")

    return DatasetBundle(dataframe=df, schema=schema, cleaned_columns=cleaned_columns)
