"""Generate deterministic gold expectations from the bundled dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .contracts import GoldExpectation, GoldSet


def _load_df(dataset_path: str) -> pd.DataFrame:
    df = pd.read_csv(dataset_path, low_memory=False)
    df.columns = [column.strip() for column in df.columns]
    unnamed = [column for column in df.columns if column.startswith("Unnamed:")]
    if unnamed:
        df = df.drop(columns=unnamed)
    df["Date"] = pd.to_datetime(df["Date"], format="%m-%d-%y", errors="coerce")
    return df


def build_gold_set(dataset_path: str, schema_path: str) -> GoldSet:
    df = _load_df(dataset_path)
    promotion_df = df.copy()
    promotion_df["promotion_used"] = promotion_df["promotion-ids"].notna()

    category_best_size = pd.crosstab(
        df["Category"],
        df["Size"],
        values=df["Qty"],
        aggfunc="sum",
    ).fillna(0).idxmax(axis=1)

    expectations = [
        GoldExpectation(
            question_id=1,
            expected_task_type="ranking",
            expected_key_columns=["Category", "Amount"],
            expected_operation_pattern=["groupby", "sum", "sort_values"],
            expected_result_kind="rows",
            expected_result_shape="(5, 2)",
            reference_result={
                "columns": ["Category", "Amount"],
                "records": df.groupby("Category", as_index=False)["Amount"]
                .sum()
                .sort_values("Amount", ascending=False)
                .head(5)
                .to_dict(orient="records"),
            },
            acceptable_signals=["Set", "kurta", "Western Dress"],
        ),
        GoldExpectation(
            question_id=2,
            expected_task_type="trend",
            expected_key_columns=["Date", "Order ID"],
            expected_operation_pattern=["groupby", "count", "to_period"],
            expected_result_kind="pairs",
            expected_result_shape="(4,)",
            reference_result={
                "pairs": [[str(period), int(count)] for period, count in df.groupby(df["Date"].dt.to_period("M"))["Order ID"].count().sort_index().items()]
            },
            acceptable_signals=["2022-04", "2022-05", "2022-06"],
        ),
        GoldExpectation(
            question_id=3,
            expected_task_type="aggregation",
            expected_key_columns=["Status"],
            expected_operation_pattern=["cancelled", "len", "percentage"],
            expected_result_kind="scalar",
            expected_result_shape=None,
            reference_result={
                "value": float((df["Status"] == "Cancelled").sum() / len(df) * 100)
            },
            acceptable_signals=["Cancelled"],
        ),
        GoldExpectation(
            question_id=4,
            expected_task_type="ranking",
            expected_key_columns=["ship-state", "Order ID"],
            expected_operation_pattern=["groupby", "count", "head"],
            expected_result_kind="pairs",
            expected_result_shape="(5,)",
            reference_result={
                "pairs": [[str(state), int(count)] for state, count in df.groupby("ship-state")["Order ID"].count().sort_values(ascending=False).head(5).items()]
            },
            acceptable_signals=["MAHARASHTRA", "KARNATAKA", "TAMIL NADU"],
        ),
        GoldExpectation(
            question_id=5,
            expected_task_type="ranking",
            expected_key_columns=["Size", "Qty"],
            expected_operation_pattern=["groupby", "sum", "sort_values"],
            expected_result_kind="pairs",
            expected_result_shape="(5,)",
            reference_result={
                "pairs": [[str(size), int(qty)] for size, qty in df.groupby("Size")["Qty"].sum().sort_values(ascending=False).head(5).items()]
            },
            acceptable_signals=["M", "L", "XL"],
        ),
        GoldExpectation(
            question_id=6,
            expected_task_type="comparison",
            expected_key_columns=["Fulfilment", "Status"],
            expected_operation_pattern=["groupby", "cancelled", "percentage"],
            expected_result_kind="pairs",
            expected_result_shape="(2,)",
            reference_result={
                "pairs": [[str(name), float(value)] for name, value in df.groupby("Fulfilment").apply(lambda group: (group["Status"] == "Cancelled").sum() / len(group) * 100, include_groups=False).items()]
            },
            acceptable_signals=["Amazon", "Merchant"],
        ),
        GoldExpectation(
            question_id=7,
            expected_task_type="comparison",
            expected_key_columns=["B2B", "Amount"],
            expected_operation_pattern=["groupby", "mean"],
            expected_result_kind="pairs",
            expected_result_shape="(2,)",
            reference_result={
                "pairs": [[str(name), float(value)] for name, value in df.groupby("B2B")["Amount"].mean().items()]
            },
            acceptable_signals=["True", "False"],
        ),
        GoldExpectation(
            question_id=8,
            expected_task_type="ranking",
            expected_key_columns=["Category", "Size", "Qty"],
            expected_operation_pattern=["crosstab", "aggfunc", "idxmax"],
            expected_result_kind="pairs",
            expected_result_shape="(9,)",
            reference_result={
                "pairs": [[str(category), str(size)] for category, size in category_best_size.items()]
            },
            acceptable_signals=["Set", "kurta", "L", "M"],
        ),
        GoldExpectation(
            question_id=9,
            expected_task_type="comparison",
            expected_key_columns=["promotion-ids", "Amount"],
            expected_operation_pattern=["notna", "groupby", "mean"],
            expected_result_kind="pairs",
            expected_result_shape="(2,)",
            reference_result={
                "pairs": [[str(name), float(value)] for name, value in promotion_df.groupby("promotion_used")["Amount"].mean().items()]
            },
            acceptable_signals=["True", "False"],
        ),
        GoldExpectation(
            question_id=10,
            expected_task_type="ranking",
            expected_key_columns=["Date", "Amount"],
            expected_operation_pattern=["day_name", "groupby", "sum", "sort_values"],
            expected_result_kind="pairs",
            expected_result_shape="(7,)",
            reference_result={
                "pairs": [[str(day), float(value)] for day, value in df.groupby(df["Date"].dt.day_name())["Amount"].sum().sort_values(ascending=False).items()]
            },
            acceptable_signals=["Sunday", "Tuesday", "Saturday"],
        ),
    ]

    return GoldSet(
        benchmark_name="Amazon Sale Report Question Benchmark",
        dataset_path=dataset_path,
        schema_path=schema_path,
        expectations=expectations,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate deterministic gold expectations for the evaluation pack.")
    parser.add_argument("--dataset", default="dataset/Amazon Sale Report.csv")
    parser.add_argument("--schema", default="dataset/schema.json")
    parser.add_argument("--output", default="dataset/eval_gold.json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    gold_set = build_gold_set(args.dataset, args.schema)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(gold_set.model_dump(mode="json"), handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
