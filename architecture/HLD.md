# High-Level Design

## Goals

DreamTrip demonstrates framework interoperability through the A2A protocol. A coordinator passes structured travel context through three independently hosted agent capabilities: option discovery, budget-versus-experience negotiation, and visualization.

## System boundaries

![System architecture](diagrams/system-architecture.svg)

| Component | Technology | Responsibility |
|---|---|---|
| Experience layer | Streamlit | Captures requests, shows progress, transcript, itinerary, and generated charts |
| Coordinator | Python, pandas, httpx, A2A client SDK | Loads CSV context, creates protocol messages, calls agents in order, aggregates results |
| Travel Concierge | LangChain on FastAPI/A2A, port 8001 | Parses options, computes metrics, summarizes feasible candidates |
| Planning Committee | CrewAI on FastAPI/A2A, port 8002 | Runs Budget Watchdog and Experience Guru debate and produces a consensus itinerary |
| Itinerary Artist | AutoGen on FastAPI/A2A, port 8003 | Calls Plotly tooling and writes cost visualization artifacts |
| Protocol boundary | A2A JSON-RPC over HTTP | Agent cards, typed message/data parts, request and response exchange |
| Artifact store | Writable local/container directory | Plotly JSON charts and transcript-adjacent outputs |

## Orchestration model

The coordinator is intentionally deterministic: Concierge, then Committee, then Artist. Each step receives only the structured payload it needs. A2A agent cards expose capability metadata, while JSON-RPC messages carry human-readable text and typed data parts. Blocking framework calls run through thread offloading inside async FastAPI handlers.

## Data contracts

- Concierge input: dataset path, CSV text, or records plus model key.
- Concierge output: summary, records, average costs, cheapest options, and available cities.
- Committee input: travel options and concierge summary.
- Committee output: narrative itinerary and structured itinerary JSON.
- Artist input: travel options, final itinerary, and artifact directory.
- Artist output: caption, tool outputs, and generated artifact paths.

## Reliability

- HTTP clients use explicit connect/read/write timeouts and close after each call.
- Each handler rejects missing or incorrectly shaped protocol data before invoking an agent framework.
- The coordinator tests multiple artifact directories and fails clearly if none is writable.
- A production design should add correlation IDs, retries only for idempotent stages, circuit breakers, persisted workflow state, and per-agent health/readiness probes.
- Partial results should remain available when a downstream visualization step fails.

## Security

- Keep model keys in platform secrets, never A2A payloads, logs, or artifacts.
- Authenticate the UI-to-coordinator and coordinator-to-agent channels in production.
- Validate agent-card URLs and restrict outbound destinations to prevent SSRF.
- Treat model-produced code/tool arguments as untrusted and sandbox visualization tools.
- Redact user details from transcripts and set retention limits on generated artifacts.

## Scaling and deployment

The Docker image can run the Streamlit UI and agent servers together for a demonstration. Production should deploy each A2A agent independently so Concierge, Committee, and Artist can scale by their latency and resource profiles. External object storage should replace local artifacts, and a durable workflow engine or state store should support resumable execution.
