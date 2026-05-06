# Failure Mode And Fix

Observed failure mode:
- Transient provider/network failures (for example TLS handshake timeout from
  Tavily) can fail a retrieval step and break the whole workflow.

Current fix in this repo:
- Keep pipeline real-provider only (no mock fallback output).
- Add bounded retry with exponential backoff for Tavily HTTP requests in
  `SearchClient` (`3` attempts).
- Keep fail-fast error propagation (`AgentExecutionError`) so failures are
  explicit and observable.
- Add LangSmith tracing spans for workflow, agents, and services to diagnose
  where failure happened and what inputs/outputs were involved.

Why this fix:
- Preserves correctness (no fabricated response).
- Improves reliability against temporary network issues.
- Keeps postmortem/debug quality high through real traces.
