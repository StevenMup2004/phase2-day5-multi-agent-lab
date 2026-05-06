"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown."""

    lines = [
        "# Benchmark Report",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        row = (
            f"| {item.run_name} | {item.latency_seconds:.2f} | "
            f"{cost} | {quality} | {item.notes} |"
        )
        lines.append(row)
    if len(metrics) >= 2:
        fastest = min(metrics, key=lambda x: x.latency_seconds)
        highest_quality = max(metrics, key=lambda x: x.quality_score or 0.0)
        lines.extend(
            [
                "",
                "## Summary",
                "",
                f"- Fastest run: `{fastest.run_name}` ({fastest.latency_seconds:.2f}s)",
                "- Highest quality score: "
                f"`{highest_quality.run_name}` "
                f"({(highest_quality.quality_score or 0.0):.1f})",
                "- Notes should include trace links/screenshots in real submissions.",
            ]
        )
    return "\n".join(lines) + "\n"
