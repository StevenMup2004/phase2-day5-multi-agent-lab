"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings


def _langsmith_available() -> bool:
    settings = get_settings()
    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        return False
    try:
        import langsmith  # noqa: F401
    except Exception:
        return False
    return True


def get_tracing_provider() -> str:
    return "langsmith" if _langsmith_available() else "local"


def _build_langsmith_client() -> Any:
    import langsmith as ls

    settings = get_settings()
    kwargs: dict[str, Any] = {"api_key": settings.langsmith_api_key}
    if settings.langsmith_endpoint:
        kwargs["api_url"] = settings.langsmith_endpoint
    return ls.Client(**kwargs)


def flush_traces() -> None:
    """Flush tracing buffers before process exit."""
    if not _langsmith_available():
        return
    try:
        client = _build_langsmith_client()
        client.flush()
    except Exception:
        # Tracing failures should not break the app pipeline.
        return


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    *,
    run_type: str = "chain",
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Create a provider-backed span (LangSmith when configured)."""
    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "provider": get_tracing_provider(),
        "run_id": None,
        "outputs": {},
        "error": None,
        "duration_seconds": None,
    }
    if span["provider"] != "langsmith":
        try:
            yield span
        except Exception as exc:
            span["error"] = str(exc)
            raise
        finally:
            span["duration_seconds"] = perf_counter() - started
        return

    try:
        import langsmith as ls
    except Exception:
        span["provider"] = "local"
        try:
            yield span
        except Exception as exc:
            span["error"] = str(exc)
            raise
        finally:
            span["duration_seconds"] = perf_counter() - started
        return

    settings = get_settings()
    run_metadata = {"app_env": settings.app_env, "component": "multi_agent_research_lab"}
    if metadata:
        run_metadata.update(metadata)
    client = _build_langsmith_client()
    with (
        ls.tracing_context(
            enabled=True,
            project_name=settings.langsmith_project,
            client=client,
        ),
        ls.trace(
            name=name,
            run_type=run_type,
            inputs=span["attributes"],
            project_name=settings.langsmith_project,
            tags=tags,
            metadata=run_metadata,
            client=client,
        ) as run,
    ):
        span["run_id"] = str(run.id)
        try:
            yield span
        except Exception as exc:
            span["error"] = str(exc)
            raise
        finally:
            span["duration_seconds"] = perf_counter() - started
            outputs = {"duration_seconds": span["duration_seconds"]}
            if isinstance(span.get("outputs"), dict):
                outputs.update(span["outputs"])
            run.end(
                outputs=outputs,
                error=span["error"],
                metadata={"duration_seconds": span["duration_seconds"]},
            )
