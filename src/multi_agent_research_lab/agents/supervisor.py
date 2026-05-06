"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, max_iterations: int | None = None) -> None:
        settings = get_settings()
        self.max_iterations = (
            max_iterations if max_iterations is not None else settings.max_iterations
        )

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        with trace_span(
            "agent.supervisor",
            {"iteration": state.iteration, "max_iterations": self.max_iterations},
            run_type="chain",
            tags=["agent", "supervisor"],
        ) as span:
            if state.iteration >= self.max_iterations:
                route = "done"
            elif not state.sources or not state.research_notes:
                route = AgentName.RESEARCHER.value
            elif not state.analysis_notes:
                route = AgentName.ANALYST.value
            elif not state.final_answer:
                route = AgentName.WRITER.value
            else:
                route = "done"

            state.record_route(route)
            span["outputs"] = {"route": route, "iteration": state.iteration}
        state.add_trace_event(
            "supervisor.route",
            {
                "iteration": state.iteration,
                "route": route,
                "trace_provider": span["provider"],
                "trace_run_id": span.get("run_id"),
                "duration_seconds": span["duration_seconds"],
            },
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.SUPERVISOR,
                content=f"Routed to: {route}",
                metadata={"iteration": state.iteration, "trace_run_id": span.get("run_id")},
            )
        )
        return state
