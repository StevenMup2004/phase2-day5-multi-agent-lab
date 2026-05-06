# Benchmark Report

Validation timestamp (UTC): `2026-05-06T05:24:18.455567+00:00`

## Objective

Compare `single-agent baseline` vs `multi-agent workflow` for:
- latency
- estimated cost
- output quality
- citation behavior
- runtime reliability

## Evaluation Setup

Environment and runtime assumptions:
- Real provider calls only (OpenAI + Tavily), no mock output path in `src`.
- Tracing enabled with LangSmith (`LANGSMITH_TRACING=true`) for observability.
- Query:
  `Research GraphRAG state-of-the-art and summarize key methods`

Execution flow:
1. Run baseline once using `LLMClient` directly.
2. Run multi-agent once through `Supervisor -> Researcher -> Analyst -> Writer -> Critic`.
3. Collect benchmark metrics via `evaluation/benchmark.py`.
4. Validate trace payload and provider metadata in final `ResearchState`.

## Metric Definitions

- `Latency (s)`: wall-clock execution time per run.
- `Cost (USD)`: summed estimated token cost from LLM calls when token usage exists.
- `Quality (0-10)`: heuristic score from pipeline completeness and error-free execution.
- `Citation coverage`: ratio approximation from citation marker density in final answer.
- `Errors`: number of runtime errors captured in state.

## Results

| Run | Latency (s) | Cost (USD) | Quality | Notes |
|---|---:|---:|---:|---|
| baseline | 11.18 | 0.0004 | 4.0 | errors=0; iterations=0; citation_coverage=0.00 |
| multi-agent | 19.91 | 0.0009 | 10.0 | errors=0; iterations=4; citation_coverage=0.95 |

## Trace and Observability Evidence

- Multi-agent trace events recorded: `8`
- Trace provider set in runtime payload: `['langsmith']`
- All agent-level trace events include `trace_run_id`: `true`

Implication:
- The workflow is traceable end-to-end and each major step can be inspected post-run.

## No-Mock Verification

Static verification:
- Command:
  `rg "mock|fallback|provider unavailable|_mock_search|_fallback_completion" -n src`
- Result: no matches.

Runtime verification:
- Integration tests:
  `pytest -m integration` with `LANGSMITH_TRACING=true` -> `4 passed`.
- Provider assertions in integration tests:
  - Search source provider is `tavily`.
  - LLM output does not contain fallback signature.
  - Workflow output does not contain mock provider sources.

## Analysis

Key findings:
- Baseline is faster and cheaper to execute.
- Multi-agent has better structured output quality and stronger citation behavior.
- Multi-agent introduces added latency due to extra orchestration and multiple model/tool calls.

Trade-off summary:
- Use baseline when speed is top priority and quality requirements are modest.
- Use multi-agent when answer quality, evidence traceability, and analytical depth matter more than latency.

## Limitations

- Current benchmark is single-query, single-run; variance is not captured.
- Quality metric is heuristic and should be complemented by human rubric scoring.
- External API/network conditions can influence latency and occasional reliability.

## Recommended Next Benchmark Iteration

1. Expand to at least 10 diverse queries.
2. Run each query multiple times and report mean/std latency and cost.
3. Add human review rubric with blind scoring.
4. Track failure rate over repeated runs for reliability profiling.
