"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        with trace_span(
            "agent.writer",
            {"query": state.request.query, "source_count": len(state.sources)},
            run_type="chain",
            tags=["agent", "writer"],
        ) as span:
            sources_section = "\n".join(
                [
                    f"[{idx}] {doc.title} ({doc.url or 'no-url'})"
                    for idx, doc in enumerate(state.sources, start=1)
                ]
            )
            prompt = (
                f"User query:\n{state.request.query}\n\n"
                f"Research notes:\n{state.research_notes or 'No notes'}\n\n"
                f"Analysis notes:\n{state.analysis_notes or 'No analysis'}\n\n"
                f"Sources:\n{sources_section}\n\n"
                "Write a concise, structured answer with references like [1], [2]."
            )
            response = self.llm_client.complete(
                system_prompt="You are a technical writer producing clear, factual summaries.",
                user_prompt=prompt,
            )
            state.final_answer = response.content
            span["outputs"] = {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            }
        state.add_trace_event(
            "writer.completed",
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
                agent=AgentName.WRITER,
                content=state.final_answer or "",
                metadata={"cost_usd": response.cost_usd, "trace_run_id": span.get("run_id")},
            )
        )
        return state
