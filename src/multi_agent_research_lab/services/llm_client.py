"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from typing import Any

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.observability.tracing import trace_span


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.openai_model
        self.api_key = api_key if api_key is not None else settings.openai_api_key

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Requires a real provider call. Raises on configuration or runtime failures.
        """
        if not self.api_key:
            raise AgentExecutionError("OPENAI_API_KEY is missing. Real LLM call is required.")

        with trace_span(
            "service.llm.complete",
            {"model": self.model},
            run_type="llm",
            tags=["service", "openai"],
            metadata={"ls_provider": "openai", "ls_model_name": self.model},
        ) as span:
            try:
                from openai import OpenAI
            except Exception as exc:
                span["error"] = str(exc)
                raise AgentExecutionError(
                    "OpenAI SDK is unavailable. Install optional dependency set '.[llm]'."
                ) from exc

            client = OpenAI(api_key=self.api_key)
            try:
                completion = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                )
            except Exception as exc:
                span["error"] = str(exc)
                raise AgentExecutionError(f"Real LLM completion failed: {exc}") from exc

            content = self._extract_content(completion)
            if not content.strip():
                raise AgentExecutionError("Real LLM completion returned empty content.")
            usage = getattr(completion, "usage", None)
            input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
            output_tokens = getattr(usage, "completion_tokens", None) if usage else None
            cost_usd = self._estimate_cost(input_tokens, output_tokens)
            span["outputs"] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": cost_usd,
            }
            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )

    @staticmethod
    def _extract_content(completion: Any) -> str:
        choices = getattr(completion, "choices", None) or []
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None) if message else None
        return content or ""

    def _estimate_cost(self, input_tokens: int | None, output_tokens: int | None) -> float | None:
        if input_tokens is None or output_tokens is None:
            return None
        # Approx pricing reference used for relative benchmarking only.
        if self.model == "gpt-4o-mini":
            return (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)
        return None
