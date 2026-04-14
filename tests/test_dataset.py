from pathlib import Path

from multi_agent_analyst.tools.dataset import load_dataset_bundle


def test_dataset_loader_normalizes_headers_and_date():
    bundle = load_dataset_bundle("dataset/Amazon Sale Report.csv", "dataset/schema.json")

    assert "Sales Channel" in bundle.dataframe.columns
    assert "Sales Channel " not in bundle.dataframe.columns
    assert "Unnamed: 22" not in bundle.dataframe.columns
    assert str(bundle.dataframe["Date"].dtype).startswith("datetime64")
    assert bundle.cleaned_columns["Sales Channel "] == "Sales Channel"


def test_dataset_loader_exposes_schema():
    bundle = load_dataset_bundle("dataset/Amazon Sale Report.csv", "dataset/schema.json")

    assert bundle.schema["title"] == "AmazonSaleReport"
    assert "Amount" in bundle.schema["properties"]
    assert "Sales Channel" in bundle.schema["properties"]
