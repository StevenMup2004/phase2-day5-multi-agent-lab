"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        with trace_span(
            "agent.critic",
            {"has_final_answer": bool(state.final_answer)},
            run_type="tool",
            tags=["agent", "critic"],
        ) as span:
            answer = state.final_answer or ""
            has_citation = "[" in answer and "]" in answer
            finding = (
                "Citation markers detected."
                if has_citation
                else "No citation markers detected."
            )
            span["outputs"] = {"has_citation": has_citation}
        state.add_trace_event(
            "critic.completed",
            {
                "has_citation": has_citation,
                "trace_provider": span["provider"],
                "trace_run_id": span.get("run_id"),
                "duration_seconds": span["duration_seconds"],
            },
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=finding,
                metadata={"has_citation": has_citation, "trace_run_id": span.get("run_id")},
            )
        )
        if not has_citation:
            state.errors.append("Critic: final answer missing citation markers.")
        return state
