# Design Template

## Problem

Build a research assistant that accepts complex technical questions, gathers
supporting sources, analyzes strengths and weaknesses of claims, and writes a
final answer with source references.

## Why multi-agent?

Single-agent outputs are often fast but shallow. A multi-agent workflow gives:
- Clear role separation (retrieve, analyze, write).
- Better observability and debugging from intermediate outputs.
- Better guardrail enforcement through routing and stop conditions.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Route next step and stop criteria | Shared state | Next route in `route_history` | Wrong route loops or early stop |
| Researcher | Collect candidate sources and notes | User query | `sources`, `research_notes` | Irrelevant or low-quality sources |
| Analyst | Extract claims and uncertainty | Query + research notes | `analysis_notes` | Overconfident analysis |
| Writer | Synthesize final answer with references | Query + notes + sources | `final_answer` | Missing citations or weak structure |
| Critic (optional) | Validate citation markers | Final answer | Critic finding in `agent_results` | False confidence from weak checks |

## Shared state

- `request`: user query and constraints.
- `iteration`, `route_history`: loop control and debugging.
- `sources`, `research_notes`, `analysis_notes`, `final_answer`: staged outputs.
- `agent_results`: compact per-agent artifacts for benchmarking.
- `trace`: step-level events for observability.
- `errors`: non-fatal failures and fallback notices.

## Routing policy

Flow:
`supervisor -> researcher -> supervisor -> analyst -> supervisor -> writer -> critic -> supervisor -> done`

Rules:
- If no research notes or sources: route to `researcher`.
- If no analysis notes: route to `analyst`.
- If no final answer: route to `writer`.
- If final answer exists or max iterations reached: route to `done`.

## Guardrails

- Max iterations: `MAX_ITERATIONS` from `.env` (default `6`).
- Timeout: provider/search request timeout with fast fallback.
- Retry: provider SDK retry behavior.
- Fallback: deterministic local response for LLM and mock search sources.
- Validation: Pydantic schemas for state and outputs.

## Benchmark plan

Queries:
- `Research GraphRAG state-of-the-art and summarize key methods`
- `Compare multi-agent orchestration frameworks for enterprise use`

Metrics:
- Latency (seconds)
- Estimated cost (if token usage available)
- Heuristic quality score (0-10)
- Citation coverage (approx)
- Failure count

Expected outcome:
- Baseline is faster.
- Multi-agent is slower but higher quality and better citation behavior.
