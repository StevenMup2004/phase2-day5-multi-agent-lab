import pytest

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


def _skip_if_missing_real_provider_keys() -> None:
    settings = get_settings()
    if not settings.openai_api_key:
        pytest.skip("OPENAI_API_KEY is required for real integration tests.")
    if not settings.tavily_api_key:
        pytest.skip("TAVILY_API_KEY is required for real integration tests.")


def _skip_if_langsmith_not_enabled() -> None:
    settings = get_settings()
    if not settings.langsmith_tracing:
        pytest.skip("LANGSMITH_TRACING=true is required for LangSmith integration checks.")
    if not settings.langsmith_api_key:
        pytest.skip("LANGSMITH_API_KEY is required for LangSmith integration checks.")


@pytest.mark.integration
def test_search_client_uses_tavily_provider() -> None:
    _skip_if_missing_real_provider_keys()
    docs = SearchClient().search("GraphRAG state-of-the-art methods", max_results=3)
    assert docs
    assert all(doc.metadata.get("provider") == "tavily" for doc in docs)
    assert any(doc.url for doc in docs)


@pytest.mark.integration
def test_llm_client_real_call_has_no_fallback_signature() -> None:
    _skip_if_missing_real_provider_keys()
    response = LLMClient().complete(
        system_prompt="Return concise factual answers.",
        user_prompt="Respond with one short sentence about GraphRAG.",
    )
    assert response.content.strip()
    assert "fallback response" not in response.content.lower()


@pytest.mark.integration
def test_multi_agent_workflow_uses_real_providers() -> None:
    _skip_if_missing_real_provider_keys()
    state = ResearchState(
        request=ResearchQuery(query="Research GraphRAG state-of-the-art and summarize key methods")
    )
    result = MultiAgentWorkflow().run(state)
    assert result.sources
    assert all(source.metadata.get("provider") == "tavily" for source in result.sources)
    assert result.final_answer
    assert "fallback response" not in result.final_answer.lower()


@pytest.mark.integration
def test_multi_agent_workflow_records_langsmith_trace_ids() -> None:
    _skip_if_missing_real_provider_keys()
    _skip_if_langsmith_not_enabled()
    state = ResearchState(
        request=ResearchQuery(query="Research GraphRAG state-of-the-art and summarize key methods")
    )
    result = MultiAgentWorkflow().run(state)
    langsmith_events = [
        event
        for event in result.trace
        if event.get("payload", {}).get("trace_provider") == "langsmith"
    ]
    assert langsmith_events
    assert all(event["payload"].get("trace_run_id") for event in langsmith_events)
