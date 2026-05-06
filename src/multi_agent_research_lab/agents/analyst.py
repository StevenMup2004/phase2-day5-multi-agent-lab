"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        with trace_span(
            "agent.analyst",
            {"query": state.request.query},
            run_type="chain",
            tags=["agent", "analyst"],
        ) as span:
            prompt = (
                f"User query:\n{state.request.query}\n\n"
                f"Research notes:\n{state.research_notes or 'No notes'}\n\n"
                "Produce:\n"
                "1) 3-5 key claims\n"
                "2) Contradictions / uncertainty\n"
                "3) Missing evidence to verify"
            )
            response = self.llm_client.complete(
                system_prompt="You are a careful research analyst.",
                user_prompt=prompt,
            )
            state.analysis_notes = response.content
            span["outputs"] = {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            }
        state.add_trace_event(
            "analyst.completed",
            {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
                "trace_provider": span["provider"],
                "trace_run_id": span.get("run_id"),
                "duration_seconds": span["duration_seconds"],
            },
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=state.analysis_notes or "",
                metadata={"cost_usd": response.cost_usd, "trace_run_id": span.get("run_id")},
            )
        )
        return state
