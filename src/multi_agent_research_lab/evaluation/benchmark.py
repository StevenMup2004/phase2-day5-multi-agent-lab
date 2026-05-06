"""Benchmark skeleton for single-agent vs multi-agent."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return a lightweight metric object."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    estimated_cost = _extract_cost(state)
    quality = _heuristic_quality_score(state)
    citation_coverage = _citation_coverage(state)
    notes = (
        f"errors={len(state.errors)}; "
        f"iterations={state.iteration}; "
        f"citation_coverage={citation_coverage:.2f}"
    )
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=estimated_cost,
        quality_score=quality,
        notes=notes,
    )
    return state, metrics


def _extract_cost(state: ResearchState) -> float | None:
    costs: list[float] = []
    for item in state.agent_results:
        cost = item.metadata.get("cost_usd")
        if isinstance(cost, (int, float)):
            costs.append(float(cost))
    if costs:
        return sum(costs)

    # Baseline runs may store cost in trace payload instead of agent_results.
    trace_costs: list[float] = []
    for event in state.trace:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        cost = payload.get("cost_usd")
        if isinstance(cost, (int, float)):
            trace_costs.append(float(cost))
    if trace_costs:
        return sum(trace_costs)
    return None


def _heuristic_quality_score(state: ResearchState) -> float:
    score = 2.0
    if state.sources:
        score += 2.0
    if state.research_notes:
        score += 2.0
    if state.analysis_notes:
        score += 2.0
    if state.final_answer:
        score += 2.0
    if state.errors:
        score -= min(2.0, 0.5 * len(state.errors))
    return max(0.0, min(10.0, score))


def _citation_coverage(state: ResearchState) -> float:
    answer = state.final_answer or ""
    if not answer:
        return 0.0
    citations = answer.count("[")
    if citations == 0:
        return 0.0
    claim_like_lines = [line for line in answer.splitlines() if line.strip()]
    if not claim_like_lines:
        return 0.0
    return min(1.0, citations / len(claim_like_lines))
