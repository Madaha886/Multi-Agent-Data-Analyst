# Multi-Agent Data Analyst Assistant

A LangGraph-orchestrated multi-agent analytics prototype that turns a natural-language business question into a reproducible pandas workflow over a CSV dataset. It is built as an interview-ready, local-first project with transparent intermediate artifacts instead of a black-box answer.

The current v1 implementation is deterministic and schema-grounded: it plans the analysis, generates pandas code, executes it safely against the dataset, interprets the output, and critiques whether the result really answers the question.

## Why This Project

- Natural-language analytics over a structured CSV dataset
- Multi-agent pipeline with clear responsibilities
- Safe pandas execution boundary instead of free-form code running unchecked
- Structured critique and traceability through plan, code, result preview, and final answer

## Architecture

Pipeline:

`Question -> Planner -> Query Generator -> Safe Executor -> Analyst -> Critic -> Response Composer`

- `Planner`: classifies the question and builds a structured analysis plan using the dataset schema.
- `Query Generator`: translates that plan into deterministic pandas code.
- `Safe Executor`: runs the generated code against a preloaded DataFrame with restricted execution rules.
- `Analyst`: summarizes the execution result in plain English.
- `Critic`: checks whether the answer is supported by the plan and execution output.
- `Response Composer`: packages the final answer plus intermediate artifacts.

## Current Implementation

This repository is a multi-agent analytics prototype, not a production platform.

- v1 is local and deterministic.
- The current reasoning path is schema-grounded and rule-based.
- The architecture is intentionally shaped so real LLM-backed agents can be plugged in later without rewriting the workflow.

That means the project is AI-oriented and agentic in structure, but today it prioritizes transparent, testable behavior over live model integrations.

## Supported Questions

The bundled Amazon sales dataset supports these v1 question types:

- Aggregation: `What is total revenue by state?`
- Ranking: `What are the top 5 categories by revenue?`
- Comparison: `Compare average sales across customer segments.`
- Trend: `How did monthly revenue change over time?`

The current implementation maps business concepts to the closest available dataset fields:

- revenue or sales -> `Amount`
- geography or region -> `ship-state` or `ship-city`
- product grouping -> `Category`, `SKU`, `Style`, or `ASIN`
- customer segment -> `B2B`

## Dataset

The project ships with a retail/e-commerce CSV dataset in `dataset/`:

- Amazon India sales data
- roughly 128k rows
- date range from March to June 2022
- schema metadata in `dataset/schema.json`

During loading, the app:

- trims header whitespace
- normalizes `Sales Channel ` to `Sales Channel`
- drops the trailing unnamed column
- parses `Date` into datetime

## Limitations

- Single CSV dataset only
- No forecasting, anomaly detection, or advanced statistical analysis
- No multi-dataset joins
- No autonomous retry/self-correction loop in v1
- No hosted API, web UI, or deployment surface yet
- Execution restrictions are meant for a local prototype, not production-grade sandboxing

## Quick Start

Launch the Streamlit UI:

```bash
python -m venv .venv
source .venv/bin/activate
.venv/bin/pip install -r requirements.txt
streamlit run multi_agent_analyst/ui/app.py
```

The UI gives you:

- a free-text question box
- clickable preset demo questions from `dataset/questions.json`
- a workflow diagram for the full pipeline
- structured output panels for plan, code, execution result, critique, and final answer

## UI Demo

The Streamlit demo is now the primary way to explore the project.

- Use preset examples for ranking, trend, comparison, and rate questions
- Run the real pipeline against the bundled dataset
- Inspect every stage of the workflow in one place

Screenshot placeholder:

`Add a Streamlit screenshot here before publishing to GitHub.`

## Developer Commands

```bash
.venv/bin/python -m multi_agent_analyst.app.cli --question "What is total revenue by state?"
```

Get the full workflow state as JSON:

```bash
.venv/bin/python -m multi_agent_analyst.app.cli \
  --question "What is total revenue by state?" \
  --json
```

## Example Output

Sample command:

```bash
.venv/bin/python -m multi_agent_analyst.app.cli --question "What is total revenue by state?"
```

The CLI returns:

- the structured analysis plan
- the generated pandas code
- an execution result preview
- an analysis report
- critique feedback
- the final answer payload

Short excerpt from a real run:

```text
== Analysis Plan ==
{
  "task_type": "aggregation",
  "required_columns": ["Amount", "ship-state"],
  "expected_operations": ["groupby", "sum"]
}

== Generated Code ==
working_df = df.copy()
working_df = working_df[working_df['Amount'].notna()]
result = (working_df.groupby('ship-state', as_index=False)['Amount'].sum()
    .rename(columns={'Amount': 'total_amount'})
    .sort_values('total_amount', ascending=False))

== Execution Result ==
MAHARASHTRA   13335534.14
KARNATAKA     10481114.37
TELANGANA      6916615.65
```

## Workflow Diagram

The UI renders this pipeline directly:

`Question -> Planner -> Query Generator -> Safe Executor -> Analyst -> Critic -> Response Composer`

## Testing

Run the test suite with:

```bash
.venv/bin/pytest -q
```

The test coverage includes:

- dataset loading and normalization
- Pydantic contract validation
- executor safety and error handling
- agent contract behavior
- end-to-end smoke tests for supported and unsupported questions
- UI helper smoke tests

## Project Structure

```text
multi_agent_analyst/
dataset/
tests/
```

## Roadmap

- Plug in a real LLM backend for planner/query/analyst/critic stages
- Add richer routing and retry logic
- Support more datasets and connectors
- Add richer UI polish and deployment options

## Publishing Note

This repository currently does not include a license file. If you plan to publish it publicly on GitHub, add an explicit license before inviting reuse or contributions.
