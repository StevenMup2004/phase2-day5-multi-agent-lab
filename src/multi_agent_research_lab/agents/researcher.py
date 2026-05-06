"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self, search_client: SearchClient | None = None) -> None:
        self.search_client = search_client or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        with trace_span(
            "agent.researcher",
            {"query": state.request.query, "max_sources": state.request.max_sources},
            run_type="retriever",
            tags=["agent", "researcher"],
        ) as span:
            sources = self.search_client.search(
                query=state.request.query,
                max_results=state.request.max_sources,
            )
            state.sources = sources
            note_lines = [
                f"- [{idx}] {doc.title}: {doc.snippet.strip()[:220]}"
                for idx, doc in enumerate(sources, start=1)
            ]
            state.research_notes = "\n".join(note_lines)
            span["outputs"] = {"source_count": len(sources)}
        state.add_trace_event(
            "researcher.completed",
            {
                "source_count": len(sources),
                "trace_provider": span["provider"],
                "trace_run_id": span.get("run_id"),
                "duration_seconds": span["duration_seconds"],
            },
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=state.research_notes or "",
                metadata={"source_count": len(sources), "trace_run_id": span.get("run_id")},
            )
        )
        return state
