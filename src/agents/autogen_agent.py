from __future__ import annotations

import asyncio
import ast
import json
import os
import re
from pathlib import Path
from typing import Any, Awaitable

import pandas as pd
import plotly.express as px
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, ToolCallSummaryMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.a2a_utils import create_agent_message


def _ensure_output_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _run_coro(task: Awaitable[Any]) -> Any:
    try:
        return asyncio.run(task)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(task)
        finally:
            loop.close()


def run_autogen_visualizer(
    *,
    records: list[dict[str, Any]],
    analysis_summary: str,
    output_dir: str | Path,
    llm_model: str = "gpt-4o",
    temperature: float = 0.0,
) -> dict[str, Any]:
    """Leverage AutoGen AgentChat to craft travel cost visualizations."""
    from src.a2a_utils import get_llm_config
    
    llm_config = get_llm_config()
    api_key = llm_config["api_key"]
    if not api_key:
        raise RuntimeError("Neither OPENAI_API_KEY nor EUR_API_KEY environment variables are set.")

    dataframe = pd.DataFrame(records)
    artifacts_dir = _ensure_output_dir(output_dir)

    def render_travel_chart(
        metric: str = "Cost",
        group_by: str = "Name",
        chart_type: str = "bar",
        top_n: int = 8,
    ) -> dict[str, Any]:
        """Render a Plotly chart for travel options and save it as JSON on disk."""
        if metric not in dataframe.columns:
            raise ValueError(f"Unknown metric '{metric}'. Available columns: {list(dataframe.columns)}")
        if group_by not in dataframe.columns:
            raise ValueError(f"Cannot group by '{group_by}'. Choose from {list(dataframe.columns)}")

        aggregated = (
            dataframe.groupby(group_by)[metric]
            .mean()  # Average cost for duplicate names
            .sort_values(ascending=False)
        )
        if top_n and top_n > 0:
            aggregated = aggregated.head(int(top_n))

        if chart_type == "line":
            fig = px.line(
                aggregated.reset_index(),
                x=group_by,
                y=metric,
                title=f"{metric} by {group_by}",
            )
        else:
            fig = px.bar(
                aggregated.reset_index(),
                x=group_by,
                y=metric,
                title=f"{metric} by {group_by}",
            )
        fig.update_layout(template="plotly_white")

        figure_json = fig.to_json()
        file_stub = f"{metric.lower()}_by_{group_by.lower()}"
        artifact_path = artifacts_dir / f"{file_stub}.json"
        artifact_path.write_text(figure_json, encoding="utf-8")

        return {
            "figure_path": str(artifact_path),
            "metric": metric,
            "group_by": group_by,
            "chart_type": chart_type,
            "top_n": int(top_n),
        }

    async def dispatch() -> Any:
        final_model = llm_model if llm_model else llm_config["model_default"]
        
        # Build kwargs, only including base_url if it's set (standard OpenAI doesn't like explicit None sometimes)
        client_kwargs = {
            "model": final_model,
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": 800,
        }
        if llm_config["base_url"]:
            client_kwargs["base_url"] = llm_config["base_url"]

        model_client = OpenAIChatCompletionClient(**client_kwargs)
        agent = AssistantAgent(
            name="itinerary_artist",
            model_client=model_client,
            tools=[render_travel_chart],
            max_tool_iterations=3,
            reflect_on_tool_use=True,
            system_message=(
                "You are an Itinerary Artist. Always call the tool "
                "`render_travel_chart` to visualize costs. "
                "Try 1: metric='Cost', group_by='Name', chart_type='bar', top_n=8 (Most expensive options). "
                "Try 2: metric='Cost', group_by='Type', chart_type='bar' (Category breakdown: Flight/Hotel/Activity). "
                "Conclude your final response with the word TERMINATE."
            ),
        )

        prompt = (
            "Use the travel options and committee itinerary below to craft a visual summary. "
            "Call the tool `render_travel_chart` to compare costs. "
            "For example, compare 'Cost' by 'Name' for individual options, or 'Cost' by 'Type' for categories. "
            "After tool execution, summarize the visuals and confirm the budget breakdown."
            f"\n\nItinerary Context:\n{analysis_summary}"
        )
        return await agent.run(task=prompt)

    task_result = _run_coro(dispatch())

    agent_text_segments: list[str] = []
    tool_payloads: list[dict[str, Any]] = []
    raw_messages: list[str] = []

    def _parse_tool_execution_strings(text: str) -> list[dict[str, Any]]:
        extracted: list[dict[str, Any]] = []
        pattern = r"FunctionExecutionResult\(content=\"(.*?)\", name='render_travel_chart'"
        for content in re.findall(pattern, text):
            normalized = content.encode('utf-8').decode('unicode_escape')
            parsed: Any
            try:
                parsed = json.loads(normalized)
            except json.JSONDecodeError:
                try:
                    parsed = ast.literal_eval(normalized)
                except (ValueError, SyntaxError):
                    parsed = {"raw": normalized}
            if isinstance(parsed, dict):
                extracted.append(parsed)
            else:
                extracted.append({"raw": parsed})
        return extracted

    for message in task_result.messages:
        raw_messages.append(str(message))
        if isinstance(message, TextMessage) and message.source == "itinerary_artist":
            agent_text_segments.append(message.content)
        if isinstance(message, ToolCallSummaryMessage):
            for result in message.results:
                parsed: Any
                try:
                    parsed = json.loads(result.content)
                except json.JSONDecodeError:
                    try:
                        parsed = ast.literal_eval(result.content)
                    except (ValueError, SyntaxError):
                        parsed = {"raw": result.content}
                if isinstance(parsed, dict):
                    tool_payloads.append(parsed)
                else:
                    tool_payloads.append({"raw": parsed})
        if not isinstance(message, (TextMessage, ToolCallSummaryMessage)):
            tool_payloads.extend(_parse_tool_execution_strings(str(message)))

    combined_text = "\n".join(agent_text_segments).replace("TERMINATE", "").strip()

    if not tool_payloads:
        # Generate default charts if agent didn't call tools
        defaults = [
            render_travel_chart(metric="Cost", group_by="Name", chart_type="bar", top_n=8),
            render_travel_chart(metric="Cost", group_by="Type", chart_type="bar", top_n=10),
        ]
        tool_payloads.extend(defaults)
        if combined_text:
            combined_text += "\n\n(Generated default charts for Name and Type views.)"
        else:
            combined_text = "Generated default charts for travel cost comparison."

    seen_paths: set[str] = set()
    unique_payloads: list[dict[str, Any]] = []
    for payload in tool_payloads:
        path = payload.get("figure_path") if isinstance(payload, dict) else None
        if path and path in seen_paths:
            continue
        if path:
            seen_paths.add(path)
        unique_payloads.append(payload)

    message = create_agent_message(
        text=combined_text,
        data={
            "tool_outputs": unique_payloads,
            "artifacts_directory": str(artifacts_dir),
            "raw_messages": raw_messages,
        },
    )

    return {
        "message": message,
        "visual_text": combined_text,
        "tool_outputs": unique_payloads,
        "task_messages": raw_messages,
    }
