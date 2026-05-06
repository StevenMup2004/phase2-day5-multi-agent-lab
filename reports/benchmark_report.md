# Benchmark Report

Validation run timestamp (UTC): `2026-05-06T05:00:47.889534+00:00`

Query used:
`Research GraphRAG state-of-the-art and summarize key methods`

| Run | Latency (s) | Cost (USD) | Quality | Notes |
|---|---:|---:|---:|---|
| baseline | 13.32 |  | 4.0 | errors=0; iterations=0; citation_coverage=0.00 |
| multi-agent | 22.68 | 0.0008 | 10.0 | errors=0; iterations=4; citation_coverage=0.67 |

## Summary

- Fastest run: `baseline` (13.32s)
- Highest quality score: `multi-agent` (10.0)
- Multi-agent trace events: `8`
- Multi-agent trace provider set: `["langsmith"]`
- Multi-agent trace run IDs present on all agent events: `true`

## No-Mock Validation

- Static scan on runtime code found no mock/fallback content path:
  `rg "mock|fallback|provider unavailable|_mock_search|_fallback_completion" -n src`
  returned no matches.
- Real-provider integration tests passed:
  `pytest -m integration` with `LANGSMITH_TRACING=true` -> `4 passed`.
- Real workflow execution check:
  `multi_has_mock_provider=False` on source metadata.
