---
title: DreamTrip Architect
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# DreamTrip Architect: A2A Travel Orchestration

**The Future of Agentic AI is Here.**

DreamTrip Architect is a **state-of-the-art Multi-Agent System (MAS)** that orchestrates a seamless collaboration between three specialized AI frameworks—**LangChain**, **CrewAI**, and **AutoGen**—to deliver hyper-personalized travel itineraries.

Built on the **Agent-to-Agent (A2A) Protocol**, this platform demonstrates the power of **interoperable AI**, where agents negotiate, debate, and visualize data autonomously without human intervention.

---

## Key Technologies & Buzzwords

*   **Agentic Orchestration**: Autonomous coordination between disparate AI agents.
*   **Multi-Framework Interop**: Unifies **LangChain** (Data Ingestion), **CrewAI** (Sequential Debate), and **AutoGen** (Code-Based Visualization).
*   **A2A JSON-RPC Protocol**: Standardized, high-performance communication layer.
*   **Cognitive Negotiation**: "Budget Watchdog" vs "Experience Guru" agents debate dynamically to find optimal trade-offs.
*   **Glassmorphism UI**: Beautiful, narrative-driven interface built with heavily customized **Streamlit**.
*   **Dockerized Deployment**: Container-native architecture ready for **Hugging Face Spaces**.
*   **Euri / OpenAI Agnostic**: Seamlessly supports **Euron API** (`EUR_API_KEY`) and standard OpenAI models.

---

## Architecture

For a concise visual map, protocol boundaries, failure behavior, and the end-to-end planning sequence, see the [architecture package](architecture/README.md).

1.  **Travel Concierge (LangChain)**
    *   Ingests raw CSV data (RAG-lite).
    *   Performs semantic filtering and validates travel feasibility.
    *   Output: Structured travel candidates.

2.  **Planning Committee (CrewAI)**
    *   **Agent 1 (Watchdog)**: Minimizes cost, enforces frugality.
    *   **Agent 2 (Guru)**: Maximizes experience, upgrades lifestyle.
    *   *Result*: A perfectly balanced, negotiated itinerary.

3.  **Itinerary Artist (AutoGen)**
    *   Code-executing agent.
    *   Generates **Plotly** visualizations on the fly for cost breakdowns.
    *   Writes physical artifacts (`.json` charts) to disk.

---

## Quick Start

### 1. Installation
Clone the repo and ensure you have `python 3.10+` or `uv`.

```bash
git clone repo_url
cd a2a-travel-orchestration
```

### 2. Configuration
Create a `.env` file with your credentials. **Native support for Euri!**

```bash
# Option 1: Euri (Recommended)
EUR_API_KEY=euri-xxx...

# Option 2: OpenAI
OPENAI_API_KEY=sk-xxx...
```

### 3. Launch
One script to rule them all. Kills zombie processes, installs deps, and launches the UI.

```bash
./setup_and_run.sh
```

---

## Deployment (Docker)

Ready for the cloud? Deploy to **Hugging Face Spaces** (free tier compatible).

1.  Create a Space (Docker SDK).
2.  Set `EUR_API_KEY` in Space Secrets.
3.  Push this repo.
4.  *The `Dockerfile` and `entrypoint.sh` handle the rest.*

---

*"Orchestrating your perfect journey through Agentic Intelligence."*
