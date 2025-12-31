from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
from langchain_community.document_loaders import CSVLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.a2a_utils import create_agent_message


def _load_dataframe(csv_path: str | Path) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Travel dataset not found: {path}")
    return pd.read_csv(path)


def _build_prompt() -> ChatPromptTemplate:
    template = (
        "You are a Travel Concierge agent. "
        "Review the available travel options (Flights, Hotels, Activities) and identify "
        "the best matches for a potential itinerary. "
        "Highlight cost-effective choices and premium experiences."
        "\n\nDataset preview:\n{preview}\n\n"
        "Provide:\n"
        "1. Three top recommendations for Flights, Hotels, and Activities.\n"
        "2. A summary of the cost range for this trip.\n"
        "3. A JSON block named travel_metrics summarizing avg_costs and total_options."
    )
    return ChatPromptTemplate.from_messages([("system", template)])


def _compute_metrics(df: pd.DataFrame) -> dict[str, Any]:
    # Travel metrics calculation
    
    if "Type" not in df.columns or "Cost" not in df.columns:
        return {"error": "Dataset missing Type or Cost columns"}

    avg_costs = df.groupby("Type")["Cost"].mean().to_dict()
    cheapest = df.nsmallest(3, "Cost")[["Name", "Cost", "Type"]].to_dict(orient="records")
    
    total_options = len(df)
    
    return {
        "avg_costs": avg_costs,
        "cheapest_options": cheapest,
        "total_options_available": total_options,
        "types_breakdown": df["Type"].value_counts().to_dict(),
        "cities_available": df["City"].unique().tolist() if "City" in df.columns else []
    }


def _format_preview(df: pd.DataFrame, rows: int = 5) -> str:
    preview_df = df.head(rows)
    return preview_df.to_csv(index=False)


def run_langchain_reader(
    csv_path: str | Path | None,
    *,
    dataframe: pd.DataFrame | None = None,
    llm_model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> dict[str, Any]:
    """Load the travel dataset and produce a structured Travel Concierge summary."""
    if dataframe is None:
        if csv_path is None:
            raise ValueError("Either csv_path or dataframe must be provided to run_langchain_reader.")
        dataframe = _load_dataframe(csv_path)
    
    metrics = _compute_metrics(dataframe)
    preview = _format_preview(dataframe)

    if csv_path is not None:
        loader = CSVLoader(str(csv_path))
        documents = loader.load()
        joined_rows = "\n".join(doc.page_content for doc in documents)
    else:
        joined_rows = dataframe.to_csv(index=False)

    from src.a2a_utils import get_llm_config
    
    llm_config = get_llm_config()
    final_model = llm_model if llm_model else llm_config["model_default"]

    llm = ChatOpenAI(
        model=final_model, 
        temperature=temperature,
        api_key=llm_config["api_key"],
        base_url=llm_config["base_url"]
    )
    prompt = _build_prompt()
    response = llm.invoke(prompt.format_messages(preview=preview + "\n" + joined_rows))
    summary_text = response.content.strip()

    message = create_agent_message(
        text=summary_text,
        data={
            "schema": list(dataframe.columns),
            "records": dataframe.to_dict(orient="records"),
            "metrics": metrics,
        },
    )

    return {
        "message": message,
        "summary_text": summary_text,
        "dataframe": dataframe,
        "records": dataframe.to_dict(orient="records"),
        "metrics": metrics,
        "preview": preview,
    }
