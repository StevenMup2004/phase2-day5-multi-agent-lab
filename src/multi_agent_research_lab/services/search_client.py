"""Search client abstraction for ResearcherAgent."""

import json
from urllib import request

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import SourceDocument
from multi_agent_research_lab.observability.tracing import trace_span


class SearchClient:
    """Provider-agnostic search client skeleton."""

    def __init__(self, tavily_api_key: str | None = None) -> None:
        settings = get_settings()
        self.tavily_api_key = (
            tavily_api_key if tavily_api_key is not None else settings.tavily_api_key
        )

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Requires a real Tavily provider call.
        """
        if not self.tavily_api_key:
            raise AgentExecutionError("TAVILY_API_KEY is missing. Real search call is required.")
        with trace_span(
            "service.search.tavily",
            {"query": query, "max_results": max_results},
            run_type="retriever",
            tags=["service", "tavily"],
            metadata={"ls_provider": "tavily"},
        ) as span:
            docs = self._search_tavily(query, max_results=max_results)
            if not docs:
                raise AgentExecutionError("Tavily search returned no results.")
            span["outputs"] = {"result_count": len(docs)}
            return docs

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url="https://api.tavily.com/search",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            data = self._post_tavily(req)
        except Exception as exc:
            raise AgentExecutionError(f"Real Tavily search failed: {exc}") from exc

        results = data.get("results", [])
        docs: list[SourceDocument] = []
        for item in results:
            title = item.get("title", "Untitled source")
            url = item.get("url")
            snippet = item.get("content") or item.get("snippet") or ""
            docs.append(
                SourceDocument(
                    title=title,
                    url=url,
                    snippet=snippet[:600],
                    metadata={"provider": "tavily"},
                )
            )
        return docs

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
    )
    def _post_tavily(self, req: request.Request) -> dict[str, object]:
        with request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise AgentExecutionError("Tavily response is not a JSON object.")
        return payload
