from __future__ import annotations

from pathlib import Path
from typing import Any
import sys
import time
import json

import pandas as pd
import plotly.io as pio
import streamlit as st
from dotenv import load_dotenv

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.orchestrator import orchestrate_trip_planning

# --- 🎨 THEME & STYLING ---
def inject_custom_css():
    st.markdown("""
        <style>
            /* IMPORT FONTS */
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;600&display=swap');

            /* RESET & VARIABLES */
            :root {
                --primary: #1E3A8A; /* Midnight Blue */
                --accent: #D4AF37; /* Champagne Gold */
                --text-dark: #0F172A; /* Slate 900 */
                --text-light: #64748B; /* Slate 500 */
                --white: #FFFFFF;
            }

            /* GLOBAL OVERRIDES */
            .stApp {
                background-color: #F8FAFC;
                font-family: 'Inter', sans-serif;
                color: var(--text-dark);
            }

            p, li, label, .stMarkdown {
                color: var(--text-dark) !important;
            }

            h1, h2, h3, h4, .stHtml {
                font-family: 'Playfair Display', serif !important;
                color: var(--primary) !important;
            }

            /* HERO SECTION (Fixed: No negative margins) */
            .hero-container {
                padding: 3rem 2rem;
                background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
                border-radius: 16px;
                color: white;
                text-align: center;
                margin-bottom: 2rem;
                box-shadow: 0 10px 30px rgba(37, 99, 235, 0.2);
            }
            .hero-title {
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                color: white !important;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .hero-subtitle {
                font-size: 1.25rem;
                font-weight: 300;
                opacity: 0.9;
                color: #EFF6FF !important;
                font-style: italic;
            }

            /* INPUT & WIDGET FIXES (Aggressive Override) */
            input, textarea, select {
                background-color: #FFFFFF !important;
                color: #0F172A !important; /* Force Black text */
                caret-color: #0F172A !important;
                border: 1px solid #CBD5E1 !important;
                opacity: 1 !important; /* Prevent double opacity reduction */
            }
            input:disabled {
                background-color: #F8FAFC !important; /* Very light gray */
                color: #64748B !important; /* Slate 500 - Visible but disabled looking */
                /* border-color: #E2E8F0 !important; */
                -webkit-text-fill-color: #64748B !important; /* Fix for Safari/Chrome text opacity */
            }
            div[data-baseweb="select"] > div {
                background-color: #FFFFFF !important;
                color: #0F172A !important;
            }
            .stTextInput label, .stSelectbox label, .stRadio label {
                color: #1E293B !important; /* Dark Slate Labels */
                font-weight: 700 !important;
            }
            
            /* CONTENT TEXT FIXES */
            p, li, span, div.stMarkdown, .stText {
                color: #334155 !important; /* Slate 700 - Readable */
            }
            
            /* CODE BLOCKS */
            code {
                color: #D946EF !important; /* Pink for contrast */
                background: #F1F5F9 !important;
            }

            /* CHECKBOX FIX */
            div[data-baseweb="checkbox"] div {
                 border-color: #1E3A8A !important;
            }
            div[data-baseweb="checkbox"] div:first-child {
                background-color: transparent !important; /* Ensure box background is clear/white */
            }
            div[data-baseweb="checkbox"] div[aria-checked="true"] {
                background-color: #1E3A8A !important;
                border-color: #1E3A8A !important;
            }

            /* EXPANDER STYLING (Targeting the summary element) */
            div[data-testid="stExpander"] {
                background-color: #FFFFFF !important;
                border: 1px solid #E2E8F0 !important;
                border-radius: 8px !important;
                overflow: hidden;
            }
            div[data-testid="stExpander"] > details > summary {
                background-color: #FFFFFF !important;
                color: #1E3A8A !important;
                font-weight: 600 !important;
                border-bottom: 1px solid #E2E8F0;
            }
            div[data-testid="stExpander"] > details > summary:hover {
                color: #D4AF37 !important;
                background-color: #F8FAFC !important;
            }
            div[data-testid="stExpander"] > details[open] > summary {
                border-bottom: 1px solid #E2E8F0 !important;
            }
            div[data-testid="stExpander"] > details > div {
                color: #0F172A !important;
            }

            /* FEATURE CARDS (Bottom Columns) */
            .feature-card {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
                text-align: center;
                height: 100%;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            }
            .feature-card h4 { margin-top: 1rem; margin-bottom: 0.5rem; }
            .feature-card .icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
            .feature-card p { font-size: 0.9rem; color: var(--text-light) !important; line-height: 1.5; }

            /* BUTTONS */
            .stButton button {
                background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%) !important;
                color: white !important;
                border: none !important;
                font-weight: 600 !important;
                padding: 0.75rem 2rem !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3) !important;
                transition: transform 0.2s ease !important;
            }
            /* BUTTON TEXT FIX - Ensure it is white */
            .stButton button, .stButton button p, .stButton button span {
                color: #FFFFFF !important;
                font-weight: 600 !important;
            }
            .stButton button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(30, 58, 138, 0.4) !important;
            }

            /* CHAT & AVATARS */
            .chat-row { display: flex; margin-bottom: 1.5rem; align-items: flex-start; }
            .avatar {
                width: 48px; height: 48px; border-radius: 12px;
                display: flex; align-items: center; justify-content: center;
                font-size: 1.5rem; color: white; margin-right: 1rem; flex-shrink: 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .chat-bubble {
                background: white; padding: 1.5rem; border-radius: 0 16px 16px 16px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #F1F5F9; width: 100%;
            }
            .avatar-watcher { background: #EF4444; }
            .avatar-guru { background: #8B5CF6; }
            .avatar-concierge { background: #10B981; }
            .avatar-artist { background: #F59E0B; }
            
            /* METRICS */
            div[data-testid="stMetricValue"] { color: var(--primary) !important; font-family: 'Playfair Display', serif !important; }

        </style>
    """, unsafe_allow_html=True)

# --- 🛠️ HELPER FUNCTIONS ---

def _render_hero():
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">DreamTrip Architect</div>
            <div class="hero-subtitle">"Orchestrating your perfect journey through Agentic Intelligence"</div>
        </div>
    """, unsafe_allow_html=True)
    
def _render_feature_cards():
    """Renders the three agent descriptions in nice cards."""
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🕵️</div>
            <h4>Concierge</h4>
            <p>Scours the database for hidden gems and validates flight availability against real-world constraints.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">⚖️</div>
            <h4>Committee</h4>
            <p>A heated debate between a Budget Watchdog & Experience Guru to find the perfect trade-off.</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🎨</div>
            <h4>Artist</h4>
            <p>Visualizes your spend breakdown and generates the final client-ready manifesto.</p>
        </div>
        """, unsafe_allow_html=True)

def _persist_upload(upload) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / upload.name
    file_path.write_bytes(upload.getbuffer())
    return file_path

def _render_plot(artifact: dict[str, Any]) -> None:
    path = artifact.get("figure_path")
    if not path:
        return
    figure_file = Path(path)
    if not figure_file.exists():
        st.warning(f"Chart missing: {figure_file}")
        return
    try:
        figure_json = figure_file.read_text(encoding="utf-8")
        figure = pio.from_json(figure_json)
        figure.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': "Inter, sans-serif"},
            title_font={'family': "Playfair Display, serif", 'size': 20, 'color': '#1E3A8A'}
        )
        st.plotly_chart(figure, use_container_width=True)
    except Exception as exc:
        st.error(f"Chart Render Error: {exc}")

def _render_itinerary_card(itinerary_text: str):
    st.markdown(f"""
    <div style="background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); border: 1px solid #E2E8F0;">
        <h3 style="margin-top:0; border-bottom: 2px solid #D4AF37; padding-bottom: 1rem; margin-bottom: 2rem; text-align: center;">✨ Approved Itinerary</h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(itinerary_text)

# --- 🚀 MAIN APP ---

def main() -> None:
    st.set_page_config(page_title="DreamTrip Architect", layout="wide", page_icon="✈️")
    inject_custom_css()
    _render_hero()

    load_dotenv()

    # --- SIDEBAR / ENGINE ROOM ---
    with st.expander("⚙️ The Engine Room (Configuration)", expanded=False):
        # Safety Lock: Prevent accidental edits - PERMANENTLY LOCKED for Client
        # enable_editing = st.checkbox("🔓 Enable Advanced Configuration", value=False)
        st.caption("🔒 Configuration is locked by administrator.")
        
        col_conf1, col_conf2 = st.columns(2)
        with col_conf1:
            st.markdown("**🤖 Model Configuration**")
            langchain_model = st.text_input("Concierge Model", value="gpt-4o-mini", disabled=True)
            crewai_model = st.text_input("Committee Model", value="gpt-4o-mini", disabled=True)
            autogen_model = st.text_input("Artist Model", value="gpt-4o", disabled=True)
        with col_conf2:
            st.markdown("**🔗 Agent Endpoints**")
            reader_endpoint = st.text_input("Reader URL", value="http://localhost:8001/a2a", disabled=True)
            analyst_endpoint = st.text_input("Analyst URL", value="http://localhost:8002/a2a", disabled=True)
            visualizer_endpoint = st.text_input("Visualizer URL", value="http://localhost:8003/a2a", disabled=True)

    # --- DATA SELECTION ---
    st.markdown("### 1. Select Your Destination Source")
    default_dataset = Path("data/travel_options.csv")
    
    col_data, col_btn = st.columns([3, 1])
    with col_data:
        dataset_choice = st.radio("", ["Use Curated Destinations (Demo)", "Upload Custom CSV"], horizontal=True, label_visibility="collapsed")
    
    dataset_path: Path | None = None
    
    if dataset_choice == "Use Curated Destinations (Demo)":
        if default_dataset.exists():
            dataset_path = default_dataset
            # Show visible preview
            df = pd.read_csv(default_dataset)
            st.success(f"✅ Loaded verified database with {len(df)} options.")
            with st.expander("👀 View Travel Database (Preview)", expanded=True):
                st.dataframe(df, use_container_width=True)
        else:
            st.error("Default dataset missing.")
    else:
        uploaded = st.file_uploader("Upload CSV", type="csv")
        if uploaded:
            dataset_path = _persist_upload(uploaded)
            df = pd.read_csv(dataset_path)
            st.success("Custom dataset loaded.")
            with st.expander("👀 View Uploaded Data", expanded=True):
                st.dataframe(df, use_container_width=True)

    # --- EXECUTION ---
    with col_btn:
        st.write("") # Spacer
        run_button = st.button("🚀 Launch Architect", type="primary", use_container_width=True, disabled=dataset_path is None)

    if not run_button:
        st.markdown("---")
        _render_feature_cards()
        st.stop()

    # --- LIVE PROCESSING STORY ---
    status_placeholder = st.empty()
    
    with status_placeholder.container():
        st.markdown("""
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E3A8A; padding: 1rem; border-radius: 8px; text-align: center; font-weight: 500;">
                🛫 Initiating Flight Protocol... Waking up Agents...
            </div>
        """, unsafe_allow_html=True)

    results = None
    try:
        def progress_callback(step: str, payload: dict[str, Any]) -> None:
            if step == "concierge":
                status_placeholder.markdown("""
                    <div style="background: #ECFDF5; border: 1px solid #A7F3D0; color: #064E3B; padding: 1rem; border-radius: 8px; text-align: center; font-weight: 500;">
                        ✅ <b>Concierge</b> has identified top candidates. Sending to Committee...
                    </div>
                """, unsafe_allow_html=True)
            elif step == "committee":
                status_placeholder.markdown("""
                    <div style="background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E; padding: 1rem; border-radius: 8px; text-align: center; font-weight: 500;">
                        ⚖️ <b>Committee</b> consensus reached! Budget vs Luxury debate concluded.
                    </div>
                """, unsafe_allow_html=True)
            elif step == "artist":
                status_placeholder.empty() # Clear for final reveal

        results = orchestrate_trip_planning(
            dataset_path,
            model_overrides={"reader": langchain_model, "analyst": crewai_model, "visualizer": autogen_model},
            agent_endpoints={"reader": reader_endpoint, "analyst": analyst_endpoint, "visualizer": visualizer_endpoint},
            progress_callback=progress_callback,
        )

    except Exception as exc:
        st.error(f"Mission Abort! {exc}")
        st.stop()

    # --- 🏆 FINAL REVEAL ---
    
    # Layout: Two columns (Itinerary | Visuals)
    st.markdown("---")
    
    # Tabbed Interface for the Results
    tab_overview, tab_debate, tab_charts, tab_logs = st.tabs(["✨ Itinerary", "🔥 The Debate", "📊 Financials", "📜 System Logs"])

    with tab_overview:
        col_itinerary, col_summary = st.columns([1.5, 1])
        
        with col_itinerary:
            _render_itinerary_card(results["committee"]["itinerary"])
        
        with col_summary:
            st.markdown("### 💰 Trip Summary")
            
            # Metrics Row
            json_data = results["committee"].get("structured") or {}
            cost = json_data.get("total_cost", "N/A")
            
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Total Cost", f"${cost}")
            with m2:
                st.metric("Agents Involved", "3")
                
            st.markdown("#### Selected Options")
            if json_data:
                st.info(f"✈️ **Flight:** {json_data.get('selected_flight', 'N/A')}")
                st.success(f"🏨 **Hotel:** {json_data.get('selected_hotel', 'N/A')}")
                st.warning(f"🎟️ **Activities:** {', '.join(json_data.get('selected_activities', []))}")
            else:
                st.write("Parsing structured data failed. See itinerary text.")

            st.markdown("---")
            st.caption("This itinerary was negotiated by AI agents to balance cost and experience.")

    with tab_debate:
        st.subheader("🔥 Behind Closed Doors: The Committee Debate")
        st.caption("Watch how the Budget Watchdog and Experience Guru fought for your trip.")
        
        # We simulate the chat UI from the transcript
        # Filter for Committee logic
        chat_log = results.get("conversation_log", [])
        
        for msg in chat_log:
            speaker = msg["speaker"]
            text = msg["text"]
            
            # Determine Avatar/Color
            avatar_initial = "🤖"
            css_class = ""
            if "Concierge" in speaker:
                avatar_initial = "🕵️"
                css_class = "avatar-concierge"
            elif "Committee" in speaker:
                avatar_initial = "⚖️"
                css_class = "avatar-watcher" # Default to watcher color for committee wrapper
            elif "Artist" in speaker:
                avatar_initial = "🎨"
                css_class = "avatar-artist"
            
            # Render Bubble
            st.markdown(f"""
                <div class="chat-row">
                    <div class="avatar {css_class}">{avatar_initial}</div>
                    <div class="chat-bubble">
                        <h4>{speaker}</h4>
                        <div style="font-size: 0.95rem; line-height: 1.5;">{text}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with tab_charts:
        st.subheader("📊 Financial Visualization")
        col_chart1, col_chart2 = st.columns(2)
        
        tool_outputs = results["artist"].get("tool_outputs", [])
        
        if len(tool_outputs) >= 1:
            with col_chart1:
                 _render_plot(tool_outputs[0])
        if len(tool_outputs) >= 2:
            with col_chart2:
                 _render_plot(tool_outputs[1])
                 
        if not tool_outputs:
            st.warning("The Artist did not produce charts this time.")
            
        st.markdown("---")
        st.markdown("**Artist's Analysis:**")
        st.write(results["artist"]["caption"])

    with tab_logs:
        with st.expander("Full System JSON Trace"):
            # Use st.code instead of st.json to respect custom theme/colors
            # and avoid dark-on-dark or pink-on-dark issues
            st.code(json.dumps(results, indent=2, default=str), language="json")

if __name__ == "__main__":
    main()
