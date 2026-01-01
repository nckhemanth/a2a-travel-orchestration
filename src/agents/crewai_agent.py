from __future__ import annotations

import json
from typing import Any

from crewai import Agent, Crew, Task
from crewai.process import Process
from langchain_openai import ChatOpenAI

from src.a2a_utils import create_agent_message


def run_crewai_analysis(
    *,
    records: list[dict[str, Any]],
    reader_summary: str,
    metrics: dict[str, Any],
    llm_model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> dict[str, Any]:
    """Run a CrewAI Planning Committee with dual agents debating travel options."""
    from src.a2a_utils import get_llm_config
    
    llm_config = get_llm_config()
    final_model = llm_model if llm_model else llm_config["model_default"]

    llm = ChatOpenAI(
        model=final_model, 
        temperature=temperature,
        api_key=llm_config["api_key"],
        base_url=llm_config["base_url"]
    )

    budget_watchdog = Agent(
        role="Budget Watchdog",
        goal="Ensure the trip is affordable and under budget",
        backstory=(
            "You are a strict accountant who hates wasting money. You scrutinize every "
            "expense and always suggest cheaper alternatives. You argue against "
            "expensive flights and hotels unless they are undeniably worth it."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )

    experience_guru = Agent(
        role="Experience Guru",
        goal="Ensure the trip is memorable, fun, and comfortable",
        backstory=(
            "You are a luxury travel influencer. You believe life is short and "
            "experiences matter more than money. You advocate for direct flights, "
            "nice hotels, and bucket-list activities."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )

    context_blob = json.dumps(
        {
            "concierge_summary": reader_summary,
            "metrics": metrics,
            "sample_options": records[:15],  # Show more options for debate
        },
        indent=2,
    )

    # Task 1: Budget Watchdog analyzes first
    task_budget = Task(
        description=(
            "Review the travel options provided by the Concierge. "
            "Identify the most cost-effective Flight, Hotel, and Activities. "
            "Propose a draft itinerary that strictly minimizes cost."
            "Context:\n{{context}}"
        ),
        expected_output="A frugal draft itinerary with cost breakdown.",
        agent=budget_watchdog,
    )

    # Task 2: Experience Guru upgrades and finalizes
    task_finalize = Task(
        description=(
            "Review the Budget Watchdog's draft. "
            "You MUST upgrade the trip to be more enjoyable while acknowledging the budget constraints. "
            "Negotiate a final plan that balances cost and comfort. "
            "The plan must include valid Flight, Hotel, and at least 2 Activities."
        ),
        expected_output=(
            "Return a markdown itinerary (Day-by-Day plan) and a summary of the total estimated cost. "
            "Finish with a ```json``` block named itinerary_json "
            "containing keys: total_cost, selected_flight, selected_hotel, selected_activities (list)."
        ),
        agent=experience_guru,
    )

    crew = Crew(
        name="trip_planning_crew",
        agents=[budget_watchdog, experience_guru],
        tasks=[task_budget, task_finalize],
        process=Process.sequential,
        verbose=False,
    )

    output = crew.kickoff(inputs={"context": context_blob})

    structured = output.json_dict
    
    # Fallback: Try to extract JSON manually if CrewAI failed to parse it
    if not structured and output.raw:
        import re
        raw_text = output.raw.strip()
        # Try to find JSON block wrapped in ```json ... ```
        match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if not match:
             # Try to find any JSON-like block
             match = re.search(r"^\s*(\{.*\})\s*$", raw_text, re.DOTALL | re.MULTILINE)
        
        if match:
            try:
                structured = json.loads(match.group(1))
            except json.JSONDecodeError:
                structured = {}
        else:
            structured = {}
    message_text = output.raw.strip() if output.raw else json.dumps(structured, indent=2)

    message = create_agent_message(
        text=message_text,
        data={
            "itinerary_json": structured,  # Changed from analytics_json
            "task_outputs": [task_output.model_dump() for task_output in output.tasks_output],
        },
    )

    return {
        "message": message,
        "analysis_text": message_text,
        "structured": structured,
        "crew_output": output.model_dump(),
    }
