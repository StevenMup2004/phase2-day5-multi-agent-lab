# Lab 20: Hệ thống Nghiên cứu Multi-Agent

Repo này là bài lab xây dựng hệ thống nghiên cứu multi-agent với pipeline:
- Supervisor
- Researcher
- Analyst
- Writer
- Critic (bổ sung để kiểm tra trích dẫn)

Hệ thống benchmark để so sánh `single-agent baseline` và `multi-agent workflow`.

## 1. Kiến trúc

### 1.1 Luồng xử lý tổng quan

```text
User Query
   |
   v
CLI
   |
   v
MultiAgentWorkflow (LangGraph)
   |
   +--> Supervisor (điều phối)
          |
          +--> Researcher (Tavily search) --> sources, research_notes
          +--> Analyst (OpenAI LLM)        --> analysis_notes
          +--> Writer (OpenAI LLM)         --> final_answer
          +--> Critic (validation)         --> citation check
   |
   v
ResearchState + Trace + Benchmark metrics
```

### 1.2 Shared state

Dữ liệu được truyền giữa các agent thông qua `ResearchState`:
- `request`
- `iteration`, `route_history`
- `sources`, `research_notes`, `analysis_notes`, `final_answer`
- `agent_results`, `trace`, `errors`

### 1.3 Tracing

Tracing provider hiện tại:
- LangSmith (khi `LANGSMITH_TRACING=true` và có `LANGSMITH_API_KEY`)

Pipeline đã được gắn span tại:
- workflow
- agents
- services (`LLMClient`, `SearchClient`)

## 2. Nguyên tắc runtime

- Real-provider only: dùng OpenAI + Tavily thật.
- Không có mock/fallback output trong runtime pipeline.
- Khi provider lỗi: hệ thống fail-fast bằng `AgentExecutionError`.

## 3. Cấu trúc thư mục

```text
src/multi_agent_research_lab/
  agents/
  core/
  evaluation/
  graph/
  observability/
  services/
  cli.py
docs/
reports/
tests/
```

## 4. Cài đặt

### 4.1 Tạo virtual environment

```powershell
cd C:\Users\dangv\Downloads\VinCourse\day20\phase2-day5-multi-agent-lab
python -m venv .venv
.\.venv\Scripts\activate
```

### 4.2 Cài dependencies

```powershell
pip install -e ".[dev,llm]"
```

### 4.3 Cấu hình `.env`

Tạo file `.env` từ `.env.example` và điền key:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini

TAVILY_API_KEY=...

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=multi-agent-research-lab
# optional
LANGSMITH_ENDPOINT=

APP_ENV=local
LOG_LEVEL=INFO
MAX_ITERATIONS=6
TIMEOUT_SECONDS=60
```

## 5. Cách chạy

### 5.1 Xem help

```powershell
python -m multi_agent_research_lab.cli --help
```

### 5.2 Baseline (single-agent)

```powershell
python -m multi_agent_research_lab.cli baseline --query "Research GraphRAG state-of-the-art and summarize key methods"
```

### 5.3 Multi-agent

```powershell
python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art and summarize key methods"
```

### 5.4 Benchmark

```powershell
python -m multi_agent_research_lab.cli benchmark --query "Research GraphRAG state-of-the-art and summarize key methods"
```

## 6. Test

### 6.1 Unit tests

```powershell
pytest -m "not integration"
```

### 6.2 Integration tests (gọi API thật)

```powershell
$env:LANGSMITH_TRACING="true"
pytest -m integration
```

Integration tests kiểm tra:
- provider search là `tavily`
- output LLM không có fallback signature
- workflow không có mock source
- trace event có `trace_run_id` khi bật LangSmith

## 7. Báo cáo

Các artifact quan trọng:
- `reports/benchmark_report.md`
- `reports/failure_mode.md`
- `reports/requirement_validation.md`

## 8. Lưu ý

- Nếu không có internet hoặc key sai, run sẽ fail rõ ràng (không fake output).
- Để benchmark ổn định hơn, nên chạy nhiều query và nhiều lần rồi lấy trung bình.
