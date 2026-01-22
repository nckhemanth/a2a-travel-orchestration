from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from a2a.client.client import ClientConfig
from a2a.client.client_factory import ClientFactory
from a2a.types import Message, Task
import httpx
from src.a2a_utils import (
    create_agent_card,
    create_text_message_with_data,
    extract_text_from_message,
    get_data_part,
)
from urllib.parse import urlsplit, urlunsplit


async def _send_message(endpoint: str, message: Message) -> tuple[Message, Any]:
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(120.0, connect=30.0, read=120.0, write=120.0, pool=None)
    )
    client_config = ClientConfig(streaming=False, httpx_client=http_client)
    client = await ClientFactory.connect(endpoint, client_config=client_config)
    try:
        final_message: Message | None = None
        async for response in client.send_message(message):
            if isinstance(response, Message):
                final_message = response
            else:
                task, update = response
                if isinstance(task, Task) and task.history:
                    final_message = task.history[-1]
        if final_message is None:
            raise RuntimeError(f"Agent at {endpoint} did not return a message response.")
        card = await client.get_card()
        return final_message, card
    finally:
        await client.close()
        await http_client.aclose()


def orchestrate_trip_planning(
    csv_path: str | Path,
    *,
    output_dir: str | Path = "artifacts",
    model_overrides: dict[str, str] | None = None,
    agent_endpoints: dict[str, str] | None = None,
    progress_callback: Callable[[str, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Drive agent-to-agent collaboration for Travel Planning."""

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset could not be located at {path}")

    endpoints = agent_endpoints or {
        "reader": "http://localhost:8001",
        "analyst": "http://localhost:8002",
        "visualizer": "http://localhost:8003",
    }

    normalized_endpoints: dict[str, str] = {}
    for name, url in endpoints.items():
        parsed = urlsplit(url)
        base = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        normalized_endpoints[name] = base or url

    default_models = {
        "reader": "gpt-4o-mini",
        "analyst": "gpt-4o-mini",
        "visualizer": "gpt-4o",
    }
    if model_overrides:
        default_models.update(model_overrides)

    # Try multiple locations for artifacts directory
    # Priority: 1) Environment variable, 2) /tmp, 3) user home, 4) /app
    artifacts_root = None
    candidates = [
        os.environ.get("ARTIFACTS_DIR"),
        "/tmp/artifacts",
        str(Path.home() / "artifacts"),
        "/app/artifacts",
    ]
    
    for candidate in candidates:
        if not candidate:
            continue
        try:
            candidate_path = Path(candidate)
            candidate_path.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = candidate_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            artifacts_root = candidate_path
            break
        except (PermissionError, OSError):
            continue
    
    if artifacts_root is None:
        raise RuntimeError("Could not find a writable directory for artifacts. Tried: " + ", ".join(candidates))

    dataset_df = pd.read_csv(path)
    dataset_csv = dataset_df.to_csv(index=False)

    async def _run() -> dict[str, Any]:
        transcript: list[dict[str, Any]] = []

        # User request prompt (dynamic in real app, static for now if input empty?)
        # Ideally this comes from UI. But here we inject the prompt.
        # Wait, the 'create_text_message' prompt is what the Agent sees.
        # But we also need the User's "Query" (e.g. "Trip to Paris").
        # For now, we put it in the text.
        
        user_query = "Find travel options for Paris, Tokyo, and New York."
        
        reader_request = create_text_message_with_data(
            f"You are the Concierge. {user_query} Parse the database.",
            data={
                "dataset_path": str(path.resolve()),
                "csv_text": dataset_csv,
                "model": default_models["reader"],
            },
        )
        transcript.append({"from": "coordinator", "message": reader_request})
        reader_message, reader_card = await _send_message(normalized_endpoints["reader"], reader_request)
        transcript.append({"from": "Travel Concierge", "message": reader_message})
        if progress_callback:
            progress_callback("concierge", {"message": reader_message})

        reader_text = extract_text_from_message(reader_message)
        reader_payload = get_data_part(reader_message) or {}

        analyst_request = create_text_message_with_data(
            "Debate the options and finalize the itinerary (Budget vs Experience).",
            data={
                "travel_options": reader_payload.get("records", []),
                "concierge_summary": reader_text,
                # "metrics": reader_payload.get("metrics", {}), # Optional
                "model": default_models["analyst"],
            },
        )
        analyst_message, analyst_card = await _send_message(normalized_endpoints["analyst"], analyst_request)
        transcript.append({"from": "Planning Committee", "message": analyst_message})
        if progress_callback:
            progress_callback("committee", {"message": analyst_message})

        analyst_text = extract_text_from_message(analyst_message)
        analyst_payload = get_data_part(analyst_message) or {}

        visual_request = create_text_message_with_data(
            "Visualize the itinerary and budget breakdown.",
            data={
                "travel_options": reader_payload.get("records", []), # Context
                "final_itinerary": analyst_text,
                "artifacts_dir": str((artifacts_root / "autogen").resolve()),
                "model": default_models["visualizer"],
            },
        )
        visual_message, visual_card = await _send_message(normalized_endpoints["visualizer"], visual_request)
        transcript.append({"from": "Itinerary Artist", "message": visual_message})
        if progress_callback:
            progress_callback("artist", {"message": visual_message})

        visual_text = extract_text_from_message(visual_message)
        visual_payload = get_data_part(visual_message) or {}

        # Helper to safely serialize objects
        def serialize_object(obj: Any) -> Any:
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            if hasattr(obj, "dict"):
                 return obj.dict()
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            return str(obj)

        cards = {
            "concierge": serialize_object(reader_card),
            "committee": serialize_object(analyst_card),
            "artist": serialize_object(visual_card),
        }
        
        # Serialize transcript messages
        serialized_transcript = []
        for entry in transcript:
            serialized_transcript.append({
                "from": entry["from"],
                "message": serialize_object(entry["message"])
            })

        return {
            "cards": cards,
            "transcript": serialized_transcript,
            "concierge": {
                "summary": reader_text,
                "metrics": reader_payload.get("metrics"),
                "options": reader_payload.get("records"),
            },
            "committee": {
                "itinerary": analyst_text,
                "structured": analyst_payload.get("itinerary_json"),
            },
            "artist": {
                "caption": visual_text,
                "tool_outputs": visual_payload.get("tool_outputs", []),
                "artifacts_directory": visual_payload.get("artifacts_directory"),
                "raw_messages": visual_payload.get("raw_messages", []),
            },
            "conversation_log": [
                {
                    "speaker": entry["from"],
                    "text": extract_text_from_message(entry["message"]),
                    "data": get_data_part(entry["message"]),
                }
                for entry in transcript
            ],
        }

    return asyncio.run(_run())
