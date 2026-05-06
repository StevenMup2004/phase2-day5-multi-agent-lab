# Failure Mode And Fix

## Context

This lab enforces a strict real-provider pipeline:
- OpenAI for generation
- Tavily for search
- LangSmith for tracing

No mock response path is allowed in runtime code.

## Failure Modes Observed or Anticipated

1. Provider network/transient transport failures
- Example symptoms:
  - TLS handshake timeout
  - socket connection errors
  - temporary DNS/route issues
- Typical impact:
  - Search or generation step fails
  - Workflow terminates before producing final answer

2. Provider authentication/configuration errors
- Example symptoms:
  - Missing/invalid API key
  - unauthorized response from tracing endpoint
- Typical impact:
  - Immediate failure at provider call boundary
  - No successful output artifact for that run

3. Dependency/runtime mismatch
- Example symptoms:
  - missing `langgraph` package
  - provider SDK import failure
- Typical impact:
  - workflow cannot initialize/run

## Root Causes

- External dependency on network and third-party API availability.
- Sensitive runtime coupling to environment configuration (`.env`).
- Multi-agent orchestration has more call boundaries than baseline, so more
  potential failure points.

## Current Mitigations Implemented

1. Strict fail-fast behavior
- All critical provider failures raise `AgentExecutionError`.
- No fallback text generation and no mock source substitution.

2. Bounded retry on Tavily transport path
- Search request retry policy:
  - attempts: `3`
  - wait: exponential backoff
- Goal:
  - absorb transient network instability while preserving real-provider output.

3. End-to-end tracing instrumentation
- LangSmith spans are added for:
  - workflow
  - agents
  - services (LLM/search)
- State trace payload includes:
  - `trace_provider`
  - `trace_run_id`
  - span duration
- Benefit:
  - exact failing step can be identified quickly.

4. Integration tests against real providers
- Assertions validate:
  - Tavily provider metadata
  - no fallback signature in LLM output
  - no mock source provider in final workflow output
  - LangSmith trace IDs present when tracing is enabled

## Why This Strategy

- Correctness first:
  - never fabricate results during provider outages.
- Operational clarity:
  - failures are explicit and actionable.
- Observability:
  - root-cause analysis is practical through trace IDs and span hierarchy.

## Residual Risks

- Persistent upstream outage still causes hard failure.
- API latency spikes can increase timeout probability.
- Invalid keys or endpoint misconfiguration remain user-setup risks.

## Runbook for On-Call Debugging

1. Confirm environment
- Validate:
  - `OPENAI_API_KEY`
  - `TAVILY_API_KEY`
  - `LANGSMITH_TRACING` and `LANGSMITH_API_KEY` (if tracing expected)

2. Reproduce with integration tests
- Run:
  - `pytest -m integration`
- Check which provider test fails first.

3. Inspect trace evidence
- Open LangSmith project and locate run via `trace_run_id`.
- Identify failing span (`service.search.tavily` or `service.llm.complete`).

4. Determine action
- Transient network failure:
  - retry execution.
- Auth/config failure:
  - rotate/fix key and re-run.
- Dependency failure:
  - reinstall required extras and re-run.

## Next Hardening Steps

1. Add request correlation IDs in logs and benchmark artifacts.
2. Add provider-specific timeout config in `.env`.
3. Add circuit-breaker policy for repeated provider outages.
4. Add multi-run failure-rate reporting in benchmark output.
