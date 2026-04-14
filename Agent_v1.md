# Architecture_Plan_v1.md

## Project Title
Multi-Agent Data Analyst Assistant

## Project Objective
Build a multi-agent AI system that answers business-style analytics questions over a structured dataset.  
The system should take a natural-language question, generate a clear analysis plan, produce executable pandas-based analysis code, interpret the results, and validate whether the answer actually matches the original question.

This is **Version 1**, so the focus is on:
- correctness
- modular architecture
- clear agent responsibilities
- structured outputs
- maintainable code

This version is **not** intended to be a full production platform. It is a clean, interview-ready prototype that demonstrates:
- agent orchestration
- LLM-based reasoning
- structured state passing
- data analysis automation
- validation and critique

---

## Core Use Case
A user asks a question for example:
- "Which region generated the highest total revenue?"
- "What are the top 5 products by sales?"
- "How did monthly revenue change over time?"
- "Compare average order value across customer segments."

The system should:
1. understand the question,
2. identify the required analytical steps,
3. generate pandas code to answer it,
4. run the analysis on a CSV dataset,
5. summarize the result in plain English,
6. validate whether the answer is logically supported by the analysis output.

---

## Version 1 Scope

### In Scope
- CSV-based dataset analysis
- pandas-based code generation and execution
- one-dataset workflow
- multi-agent pipeline using LangGraph
- structured agent outputs using Pydantic
- support for common business analysis question types
- result interpretation in clear natural language
- critique/validation of generated answer

### Out of Scope
- SQL database support
- dashboard generation
- memory across conversations
- autonomous self-improvement
- forecasting and predictive modeling
- anomaly detection
- multi-dataset joins
- external API tools
- autonomous retries and complex loopbacks
- deployment infrastructure beyond local runnable prototype

---

## Target User
The target user is a junior analyst, data practitioner, or hiring manager evaluating a system that can transform natural-language business questions into reproducible analytical workflows.

---

## Primary Design Principles
1. **Simple before advanced**  
   Prefer a minimal, reliable pipeline over an ambitious but unstable system.

2. **Structured state passing**  
   Each agent must return machine-readable outputs, not vague free-form text.

3. **Agent specialization**  
   Each agent has one clear responsibility.

4. **Deterministic execution boundary**  
   LLMs may plan and generate code, but actual analysis results must come from executing code on the dataset.

5. **Explainability**  
   The system should expose intermediate artifacts:
   - plan
   - generated code
   - result preview
   - final answer
   - critique notes

6. **Extensibility**  
   The architecture should allow future expansion to SQL, retries, visualization, or API deployment without major refactoring.

---

## Supported Question Types
Version 1 should support only these four categories:

1. **Aggregation**
   - Example: "What is total revenue by region?"

2. **Comparison**
   - Example: "Compare average sales across customer segments."

3. **Ranking**
   - Example: "What are the top 5 products by revenue?"

4. **Trend Analysis**
   - Example: "How did monthly sales change over time?"

### Explicitly Unsupported in v1
- causal inference
- forecasting
- recommendation systems
- anomaly detection
- advanced statistics
- ambiguous multi-part exploratory requests

---

## Dataset Assumptions
The system will initially operate on a single structured CSV dataset in an e-commerce or retail analytics domain.

### Example expected columns
These may vary by dataset, but the system should assume similar fields:
- `order_id`
- `order_date`
- `region`
- `country`
- `customer_segment`
- `product_name`
- `category`
- `quantity`
- `unit_price`
- `sales`
- `profit`

### Dataset Rules
- data is tabular and reasonably clean
- column names are known in advance
- schema is loaded before analysis
- no missing critical file path
- dataset fits in memory for pandas

---

## High-Level System Architecture

### Pipeline
`User Question -> Planner Agent -> Query Agent -> Code Executor -> Analyst Agent -> Critic Agent -> Final Response`

### Agent Flow Summary
- **Planner Agent** converts the user question into a structured analysis plan
- **Query Agent** translates the plan into executable pandas code
- **Code Executor** runs the code safely on the dataset and captures outputs
- **Analyst Agent** interprets the execution result in human-readable terms
- **Critic Agent** checks alignment between the original question, analysis logic, and final interpretation
- **Final Response Composer** packages all artifacts into the system output

---

Initial v1 Routing

Use a linear workflow with no complex branching.

Allowed Conditional Logic

Only one simple condition is allowed:
	if code execution fails, continue to critic and finalizer with failure metadata instead of crashing

No Retry Loop in v1

Do not implement automatic regeneration or self-correction loops yet.

⸻

Dataset Loading and Schema Handling

Dataset Loader Responsibilities
	•	load CSV from path
	•	validate file exists
	•	create DataFrame
	•	extract schema metadata
	•	provide simple column type summary

Schema Representation

Use a dictionary like:

{
    "columns": {
        "order_date": "datetime_candidate",
        "sales": "float",
        "region": "string"
    }
}

Schema Use

The Planner and Query Agent should use schema information to avoid inventing columns.

⸻

Execution Safety Rules

Codex must implement a restricted execution strategy for generated code.

Allowed imports in execution sandbox
	•	pandas
	•	numpy

Disallowed
	•	os
	•	sys
	•	subprocess
	•	pathlib writes
	•	open
	•	network libraries
	•	arbitrary imports

Execution policy
	•	code is executed against an already loaded df
	•	final answer depends on result
	•	execution errors must be captured and stored

This is not full sandbox security, but it should be sufficient for local prototype boundaries.

⸻

Logging Requirements

The system should include structured logging for:
	•	incoming user question
	•	planner output
	•	generated code
	•	execution success/failure
	•	analyst output
	•	critic output

Logs should support debugging and demo visibility.

⸻

Error Handling Strategy

Possible failure points
	•	missing dataset
	•	invalid schema
	•	invented columns
	•	broken generated code
	•	empty result
	•	unsupported question type

Required behavior
	•	fail gracefully
	•	record error in error_log
	•	continue pipeline when possible
	•	return a transparent failure explanation instead of silent breakdown

⸻

Final Response Contract

The final system output should include:
	•	original question
	•	short answer summary
	•	key findings
	•	result preview
	•	whether critique passed
	•	critique issues if any

Example output shape

{
  "question": "What were total sales by region?",
  "summary": "The West region generated the highest total sales, followed by the East region.",
  "key_findings": [
    "West had the highest aggregate sales",
    "South had the lowest total sales"
  ],
  "result_preview": "region | sales\nWest | 125000\nEast | 111200\nSouth | 87600",
  "critique_passed": true,
  "critique_issues": []
}


⸻

Development Priorities for Codex

Phase 1

Build core models and shared state:
	•	Pydantic models
	•	graph state structure
	•	config and logging

Phase 2

Build utilities:
	•	dataset loader
	•	schema extractor
	•	safe code executor

Phase 3

Build agents:
	•	planner
	•	query agent
	•	analyst
	•	critic

Phase 4

Build LangGraph workflow:
	•	sequential node chaining
	•	state updates
	•	final output assembly

Phase 5

Add basic local entrypoint:
	•	load dataset
	•	accept question from CLI or simple script input
	•	run workflow
	•	print final structured output

Phase 6

Add tests:
	•	planner output structure
	•	query result variable contract
	•	executor failure handling
	•	end-to-end happy path workflow

⸻

Success Criteria for Version 1

The project is considered successful if it can:
	1.	answer at least a small set of predefined analytics questions correctly,
	2.	generate executable pandas code for supported question types,
	3.	produce a readable business-style answer,
	4.	expose intermediate reasoning artifacts,
	5.	identify invalid or weak answers through critique,
	6.	run locally with clear setup steps.

⸻

Non-Goals

This project is not trying to prove:
	•	state-of-the-art reasoning
	•	secure production sandboxing
	•	enterprise-grade deployment
	•	perfect general-purpose autonomous analysis

It is a clean, well-structured demonstration project for portfolio and resume purposes.

⸻

Instructions for Codex

When implementing this architecture, Codex should:
	1.	prioritize clean modular code over premature optimization
	2.	keep all agent outputs structured with Pydantic
	3.	avoid scope creep outside this document
	4.	implement the workflow in a way that is easy to debug
	5.	prefer explicitness over abstraction-heavy patterns
	6.	keep prompts in separate files where reasonable
	7.	make the system runnable locally with minimal setup
	8.	write code that is understandable in an interview setting
	9.	ensure every step leaves visible artifacts for inspection
	10.	treat this document as the authoritative v1 scope reference