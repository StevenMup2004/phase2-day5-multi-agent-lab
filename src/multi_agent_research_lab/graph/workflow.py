"""LangGraph workflow skeleton."""

from multi_agent_research_lab.agents import (
    AnalystAgent,
    CriticAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.max_iterations = settings.max_iterations
        self.supervisor = SupervisorAgent(max_iterations=settings.max_iterations)
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()

    def build(self) -> object:
        """Create a LangGraph graph."""
        try:
            from langgraph.graph import END, StateGraph
        except Exception as exc:
            raise AgentExecutionError(
                "LangGraph is required for orchestration. Install optional dependency set '.[llm]'."
            ) from exc

        graph = StateGraph(ResearchState)
        graph.add_node("supervisor", self.supervisor.run)
        graph.add_node("researcher", self.researcher.run)
        graph.add_node("analyst", self.analyst.run)
        graph.add_node("writer", self.writer.run)
        graph.add_node("critic", self.critic.run)

        graph.set_entry_point("supervisor")
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", "critic")
        graph.add_edge("critic", "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._route_from_state,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END,
            },
        )
        return graph.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        app = self.build()
        with trace_span(
            "workflow.multi_agent",
            {
                "query": state.request.query,
                "max_sources": state.request.max_sources,
                "max_iterations": self.max_iterations,
            },
            run_type="chain",
            tags=["workflow", "multi-agent"],
        ) as span:
            try:
                result = app.invoke(state)
            except Exception as exc:
                span["error"] = str(exc)
                raise AgentExecutionError(f"Multi-agent workflow execution failed: {exc}") from exc

            if isinstance(result, ResearchState):
                span["outputs"] = {
                    "iteration": result.iteration,
                    "route_history": result.route_history,
                    "error_count": len(result.errors),
                }
                return result
            if isinstance(result, dict):
                parsed = ResearchState.model_validate(result)
                span["outputs"] = {
                    "iteration": parsed.iteration,
                    "route_history": parsed.route_history,
                    "error_count": len(parsed.errors),
                }
                return parsed
            raise AgentExecutionError(f"Unexpected workflow result type: {type(result)!r}")

    @staticmethod
    def _route_from_state(state: ResearchState) -> str:
        if not state.route_history:
            return "done"
        route = state.route_history[-1]
        if route not in {"researcher", "analyst", "writer", "done"}:
            return "done"
        return route
