"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import flush_traces, trace_span
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline placeholder."""

    _init()
    try:
        request = ResearchQuery(query=query)
        state = ResearchState(request=request)
        prompt = (
            f"User query: {query}\n\n"
            "Produce a concise research-style response in 3 sections:\n"
            "1) Key findings\n2) Caveats\n3) Next steps"
        )
        with trace_span(
            "cli.baseline",
            {"query": query},
            run_type="chain",
            tags=["cli", "baseline"],
        ) as span:
            response = LLMClient().complete(
                system_prompt="You are a single-agent research assistant.",
                user_prompt=prompt,
            )
            state.final_answer = response.content
            span["outputs"] = {"has_answer": bool(state.final_answer)}
        console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))
    finally:
        flush_traces()


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    try:
        state = ResearchState(request=ResearchQuery(query=query))
        workflow = MultiAgentWorkflow()
        try:
            result = workflow.run(state)
        except StudentTodoError as exc:
            console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
            raise typer.Exit(code=2) from exc
        console.print(result.model_dump_json(indent=2, ensure_ascii=True))
    finally:
        flush_traces()


@app.command("benchmark")
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run quick baseline vs multi-agent benchmark."""

    _init()

    try:
        def _run_baseline(q: str) -> ResearchState:
            state = ResearchState(request=ResearchQuery(query=q))
            response = LLMClient().complete(
                system_prompt="You are a single-agent research assistant.",
                user_prompt=q,
            )
            state.final_answer = response.content
            return state

        def _run_multi(q: str) -> ResearchState:
            return MultiAgentWorkflow().run(ResearchState(request=ResearchQuery(query=q)))

        baseline_state, baseline_metrics = run_benchmark("baseline", query, _run_baseline)
        multi_state, multi_metrics = run_benchmark("multi-agent", query, _run_multi)
        console.print(Panel.fit(baseline_state.final_answer or "", title="Baseline"))
        console.print(Panel.fit(multi_state.final_answer or "", title="Multi-Agent"))
        console.print(
            Panel.fit(
                f"baseline latency: {baseline_metrics.latency_seconds:.2f}s\n"
                f"multi-agent latency: {multi_metrics.latency_seconds:.2f}s",
                title="Benchmark Summary",
            )
        )
    finally:
        flush_traces()


if __name__ == "__main__":
    app()
