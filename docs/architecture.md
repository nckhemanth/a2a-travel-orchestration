# DreamTrip Travel Planner - Architecture Documentation

## System Overview

This is an Agent-to-Agent (A2A) multi-agent system for travel itinerary planning, where three specialized AI agents collaborate through standardized A2A protocol messages to search travel options, debate budget vs experience trade-offs, and generate visual itineraries.

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│                          COORDINATOR (Orchestrator)                           │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  orchestrate_trip_planning()                                            │ │
│  │  - Uses httpx.AsyncClient + ClientFactory                              │ │
│  │  - Sends A2A messages sequentially to 3 agents                         │ │
│  │  - Aggregates results and creates transcript                           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└─────────────────┬──────────────────┬──────────────────┬──────────────────────┘
                  │                  │                  │
                  │ A2A Message      │ A2A Message      │ A2A Message
                  │ (HTTP/JSON-RPC)  │ (HTTP/JSON-RPC)  │ (HTTP/JSON-RPC)
                  ▼                  ▼                  ▼
    ┌────────────────────────┐ ┌──────────────────────────┐ ┌────────────────────────┐
    │                        │ │                          │ │                        │
    │  Travel Concierge      │ │  Planning Committee      │ │  Itinerary Artist      │
    │  (LangChain)           │ │  (CrewAI - Dual Agents)  │ │  (AutoGen)             │
    │                        │ │                          │ │                        │
    │  Port: 8001            │ │  Port: 8002              │ │  Port: 8003            │
    │  ──────────            │ │  ──────────              │ │  ──────────            │
    │                        │ │                          │ │                        │
    │  Framework:            │ │  Framework:              │ │  Framework:            │
    │  • LangChain           │ │  •  CrewAI (2 agents)    │ │  • AutoGen AgentChat   │
    │  • CSVLoader           │ │  • Agent + Crew + Task   │ │  • AssistantAgent      │
    │  • ChatOpenAI          │ │  • ChatOpenAI            │ │  • OpenAI Client       │
    │                        │ │                          │ │  • Plotly Express      │
    │  Model:                │ │  Model:                  │ │                        │
    │  gpt-4o-mini           │ │  gpt-4o-mini             │ │  Model:                │
    │                        │ │                          │ │  gpt-4o                │
    │  Functions:            │ │  Agents:                 │ │                        │
    │  • Load travel CSV     │ │  • Budget Watchdog       │ │  Functions:            │
    │  • Compute avg costs   │ │     - Frugal accountant  │ │  • render_travel_      │
    │  • Find cheapest       │ │  • Experience Guru       │ │    chart() tool        │
    │  • Generate summary    │ │     - Luxury influencer  │ │  • Save Plotly JSON    │
    │                        │ │                          │ │    (Cost charts)       │
    │  Inputs:               │ │  Inputs:                 │ │                        │
    │  • csv_text            │ │  • travel_options        │ │  Inputs:               │
    │  • dataset_path        │ │  • concierge_summary     │ │  • travel_options      │
    │  • model               │ │  • metrics (optional)    │ │  • final_itinerary     │
    │                        │ │  • model                 │ │  • artifacts_dir       │
    │  Outputs:              │ │                          │ │  • model               │
    │  • summary             │ │  Process:                │ │                        │
    │  • avg_costs           │ │  • Debate: Budget vs $   │ │  Outputs:              │
    │  • cheapest_options    │ │  • Negotiate itinerary   │ │  • caption             │
    │  • options (records)   │ │  • Reach consensus       │ │  • tool_outputs        │
    │  • cities_available    │ │                          │ │  • artifacts_dir       │
    │                        │ │  Outputs:                │ │                        │
    └────────────────────────┘ │  • itinerary (markdown)  │ └────────────┬───────────┘
                               │  • itinerary_json        │              │
                               │  • task_outputs          │              │ writes
                               └──────────────────────────┘              ▼
                                                          ┌─────────────────────────────┐
                                                          │  Artifacts Directory        │
                                                          │  artifacts/autogen/         │
                                                          │  ──────────────────────     │
                                                          │  • cost_by_name.json        │
                                                          │    (Plotly bar chart)       │
                                                          │  • cost_by_type.json        │
                                                          │    (Plotly bar chart)       │
                                                          └─────────────────────────────┘

                    ┌────────────────────────┐
                    │   Data Source          │
                    │                        │
                    │  travel_options.csv    │
                    │  ──────────────────    │
                    │  • City                │
                    │  • Type                │
                    │  • Name                │
                    │  • Cost                │
                    │  • Rating              │
                    │  • Duration            │
                    │  • Description         │
                    └────────────────────────┘
                              │
                              │ read by Coordinator
                              └──────► (pandas.read_csv)
```

## Component Details

### 1. **Coordinator** (`src/orchestrator.py`)
- **Purpose**: Orchestrates the entire travel planning workflow
- **Technology**: Python asyncio, httpx, A2A ClientFactory
- **Key Functions**:
  - `orchestrate_trip_planning()`: Main entry point
  - `_send_message()`: Sends A2A messages to agents via HTTP
- **Flow**:
  1. Reads `travel_options.csv` using `pandas.read_csv()`
  2. Sends query to Travel Concierge: "Find travel options for Paris, Tokyo, New York"
  3. Forwards results to Planning Committee: "Debate and finalize itinerary"
  4. Forwards final plan to Itinerary Artist: "Visualize costs and budget"
  5. Aggregates all responses into transcript with agent cards

### 2. **A2A Server Layer** (`src/a2a_servers.py`)

#### **FastAPI Application Structure**
Each agent runs as a **FastAPI server** using:
- **Uvicorn**: ASGI server
- **A2AFastAPIApplication**: Wrapper with A2A protocol support
- **Endpoint**: `/a2a` (JSON-RPC 2.0)
- **Transport**: HTTP with JSON-RPC

#### **Server Creation Functions**
- `create_reader_app()`: Travel Concierge (port 8001)
- `create_analyst_app()`: Planning Committee (port 8002)
- `create_visualizer_app()`: Itinerary Artist (port 8003)

#### **ReaderRequestHandler** (Port 8001)
- **Accepts**: `dataset_path`, `csv_text`, or `records`
- **Processing**: Calls `run_langchain_reader()` via `asyncio.to_thread()`
- **Agent Card**:
  - `name`: "Travel Concierge"
  - `skill_id`: "travel_csv_ingest"
  - `skill_description`: "Searches flights, hotels, and activities"

#### **AnalystRequestHandler** (Port 8002)
- **Accepts**: `travel_options`, `concierge_summary`, `metrics` (optional)
- **Processing**: Calls `run_crewai_analysis()` via `asyncio.to_thread()`
- **Special**: Maps `travel_options` → `sales_records` for compatibility
- **Agent Card**:
  - `name`: "Planning Committee"
  - `skill_id`: "trip_planning_committee"
  - `skill_description`: "Budget Watchdog and Experience Guru negotiate the best trip"

#### **VisualizerRequestHandler** (Port 8003)
- **Accepts**: `travel_options`, `final_itinerary`, `artifacts_dir`
- **Processing**: Calls `run_autogen_visualizer()` via `asyncio.to_thread()`
- **Agent Card**:
  - `name`: "Itinerary Artist"
  - `skill_id`: "travel_visual_story"
  - `skill_description`: "Generates cost charts and visual summaries"

### 3. **Travel Concierge Agent** (`src/agents/langchain_agent.py`)
- **Port**: 8001
- **Framework**: LangChain
- **Model**: gpt-4o-mini
- **Purpose**: Data ingestion and travel option discovery
- **Key Functions**:
  - `run_langchain_reader()`: Main function
  - `_compute_metrics()`: Calculates travel-specific metrics
- **Metrics Computed**:
  - `avg_costs`: Average cost by Type (Flight, Hotel, Activity)
  - `cheapest_options`: Top 3 lowest-cost items
  - `types_breakdown`: Count of each category
  - `cities_available`: Unique cities list
- **Output**: Summary text + structured data (avg_costs, cheapest, options)

### 4. **Planning Committee Agent** (`src/agents/crewai_agent.py`)
- **Port**: 8002
- **Framework**: CrewAI (Multi-Agent)
- **Model**: gpt-4o-mini
- **Purpose**: Debate and negotiate final itinerary

#### **Dual-Agent Architecture**
**Agent 1: Budget Watchdog**
- **Role**: "Budget Watchdog"
- **Goal**: "Ensure the trip is affordable and under budget"
- **Backstory**: "Strict accountant who hates wasting money. Argues against expensive flights."
- **Perspective**: Cost-minimization, value optimization

**Agent 2: Experience Guru**
- **Role**: "Experience Guru"
- **Goal**: "Ensure the trip is memorable, fun, and comfortable"
- **Backstory**: "Luxury travel influencer. Life is short, experiences matter. Advocates for direct flights and nice hotels."
- **Perspective**: Quality-maximization, comfort, memories

#### **Collaborative Task**
- **Description**: "Budget Watchdog and Experience Guru must **debate** the options and **AGREE** on a final itinerary"
- **Requirement**: Must include valid Flight, Hotel, and at least 2 Activities
- **Process**: Sequential negotiation (CrewAI Process.sequential)
- **Expected Output**:
  - Markdown itinerary (Day-by-Day plan)
  - JSON with: `total_cost`, `selected_flight`, `selected_hotel`, `selected_activities`

### 5 **Itinerary Artist Agent** (`src/agents/autogen_agent.py`)
- **Port**: 8003
- **Framework**: AutoGen AgentChat
- **Model**: gpt-4o
- **Purpose**: Visual cost storytelling

#### **Tool Function: `render_travel_chart()`**
- **Parameters**: `metric`, `group_by`, `chart_type`, `top_n`
- **Defaults**: `metric="Cost"`, `group_by="Name"`, `chart_type="bar"`, `top_n=8`
- **Process**:
  1. Groups travel options by dimension (Name or Type)
  2. Calculates average Cost per group
  3. Creates Plotly bar chart
  4. Saves as JSON to artifacts directory

#### **Agent Configuration**
- **Name**: "itinerary_artist"
- **Tools**: `[render_travel_chart]`
- **System Message**: "You are an Itinerary Artist. Call `render_travel_chart` twice: once for Cost by Name, once for Cost by Type"
- **Max Iterations**: 3

#### **Generated Visualizations**
1. **Cost by Name**: Shows most expensive individual options (e.g., JAL Executive $2,500)
2. **Cost by Type**: Compares average Flight/Hotel/Activity costs

## Data Flow

```
travel_options.csv → Coordinator → Concierge → Coordinator → Committee → Coordinator → Artist → Artifacts
      (load)          (query)      (search)     (summary)     (debate)    (itinerary)   (visualize)  (charts)
```

## Agent Collaboration Example

### Step 1: Concierge Finds Options
**Input**: "Find travel options for Paris, Tokyo, New York"

**Output**:
```
avg_costs: {Flight: $1,125, Hotel: $300, Activity: $75}
cheapest: Senso-ji Temple ($0), Seine River Cruise ($20)
```

### Step 2: Committee Debates
**Budget Watchdog**: "Budget Air Connect at $600 is economical!"
**Experience Guru**: "Direct flight saves 6 hours and jet lag - worth the $1,200!"
**Consensus**: "Economy Saver at $900 + Le Grand Paris Hotel"

### Step 3: Artist Visualizes
**Charts**:
- Cost by Name: Bar chart (JAL Executive $2,500 → Senso-ji $0)
- Cost by Type: Average Flight ($1,125) vs Hotel ($300) vs Activity ($75)

## Output Artifacts

Generated in `artifacts/autogen/`:
- `cost_by_name.json`: Plotly chart of individual travel options by cost
- `cost_by_type.json`: Plotly chart of average cost by category

## Key Technologies

- **A2A Protocol**: Agent-to-agent communication standard
- **FastAPI**: Web framework for agent servers
- **LangChain**: Travel Concierge framework
- **CrewAI**: Multi-agent debate framework (Budget vs Experience)
- **AutoGen AgentChat**: Itinerary Artist with tool calling
- **OpenAI GPT**: LLM backbone (gpt-4o-mini, gpt-4o)
- **Plotly**: Interactive chart generation
- **Pandas**: Data manipulation

## Design Principles

1. **Dual-Agent Debate**: CrewAI enables Budget vs Experience negotiation
2. **Framework Diversity**: Demonstrates LangChain/CrewAI/AutoGen interoperability
3. **A2A Standard**: Uses standardized protocol for agent communication
4. **Async Architecture**: Non-blocking I/O for scalability
5. **Modular Design**: Agents can be deployed independently
6. **Tool Integration**: AutoGen demonstrates autonomous chart generation

## Use Case: Travel Planning vs Sales Analysis

| Aspect | Sales Demo | Travel Planner |
|--------|-----------|----------------|
| **Data Source** | `sales_marketing.csv` | `travel_options.csv` |
| **Agent 1** | Revenue Reader | Travel Concierge |
| **Agent 2** | Single Analyst | **Dual Debate** (Budget + Experience) |
| **Agent 3** | Sales Charts | Cost Visualizations |
| **Metrics** | Sales, Spend, ROI | Avg Cost, Cheapest, Types |
| **Output** | Revenue Report | Day-by-Day Itinerary |
| **Negotiation** | None | Budget vs Experience Debate |
