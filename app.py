"""
AI Mechanical Safety Compliance Advisor
Streamlit main application entry point.

DISCLAIMER: This is a prototype for educational and demonstration purposes.
It does not replace qualified safety professionals, official standards,
inspections, or regulatory compliance procedures.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

import streamlit as st
from dotenv import load_dotenv

# ── Load environment variables ─────────────────────────────────────
load_dotenv()

# ── Page configuration ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Mechanical Safety Advisor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── General ───────────────────────────────────────────────────── */
    body { font-family: 'Segoe UI', sans-serif; }

    /* ── Force dark text on every light-background custom card ───────
       Streamlit's dark theme sets the inherited text colour to near-
       white.  Any custom HTML <div> with a light background must
       declare its own explicit dark colour so content is always legible
       without the user needing to select/highlight text.             */

    /* Class-based cards */
    .metric-card,
    .report-box,
    .agent-card,
    .disclaimer {
        color: #1e293b !important;
    }
    .metric-card *,
    .report-box *,
    .agent-card *,
    .disclaimer * {
        color: inherit;
    }

    /* Inline-style cards produced by st.markdown(unsafe_allow_html).
       These divs carry background:#fafafa / #f8fafc / #eff6ff etc.
       We match the first two hex digits of the colour value so that
       every shade of off-white / light-blue / light-red is covered.  */
    [data-testid="stMarkdownContainer"] div[style*="background:#fa"],
    [data-testid="stMarkdownContainer"] div[style*="background: #fa"],
    [data-testid="stMarkdownContainer"] div[style*="background:#f8"],
    [data-testid="stMarkdownContainer"] div[style*="background: #f8"],
    [data-testid="stMarkdownContainer"] div[style*="background:#ff"],
    [data-testid="stMarkdownContainer"] div[style*="background: #ff"],
    [data-testid="stMarkdownContainer"] div[style*="background:#ef"],
    [data-testid="stMarkdownContainer"] div[style*="background: #ef"],
    [data-testid="stMarkdownContainer"] div[style*="background:#f0"],
    [data-testid="stMarkdownContainer"] div[style*="background: #f0"],
    [data-testid="stMarkdownContainer"] div[style*="background:#fe"],
    [data-testid="stMarkdownContainer"] div[style*="background: #fe"],
    [data-testid="stMarkdownContainer"] div[style*="background:#db"],
    [data-testid="stMarkdownContainer"] div[style*="background: #db"],
    [data-testid="stMarkdownContainer"] div[style*="background:#d1"],
    [data-testid="stMarkdownContainer"] div[style*="background: #d1"] {
        color: #1e293b !important;
    }
    [data-testid="stMarkdownContainer"] div[style*="background:#fa"] *,
    [data-testid="stMarkdownContainer"] div[style*="background: #fa"] *,
    [data-testid="stMarkdownContainer"] div[style*="background:#f8"] *,
    [data-testid="stMarkdownContainer"] div[style*="background: #f8"] *,
    [data-testid="stMarkdownContainer"] div[style*="background:#ff"] *,
    [data-testid="stMarkdownContainer"] div[style*="background: #ff"] *,
    [data-testid="stMarkdownContainer"] div[style*="background:#ef"] *,
    [data-testid="stMarkdownContainer"] div[style*="background: #ef"] *,
    [data-testid="stMarkdownContainer"] div[style*="background:#f0"] *,
    [data-testid="stMarkdownContainer"] div[style*="background: #f0"] *,
    [data-testid="stMarkdownContainer"] div[style*="background:#fe"] *,
    [data-testid="stMarkdownContainer"] div[style*="background: #fe"] *,
    [data-testid="stMarkdownContainer"] div[style*="background:#db"] *,
    [data-testid="stMarkdownContainer"] div[style*="background: #db"] *,
    [data-testid="stMarkdownContainer"] div[style*="background:#d1"] *,
    [data-testid="stMarkdownContainer"] div[style*="background: #d1"] * {
        color: #1e293b !important;
    }

    /* ── Header (dark bg → white text) ─────────────────────────────── */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white !important; margin: 0; font-size: 1.8rem; }
    .main-header p  { color: #b3c6ff !important; margin: 0.2rem 0 0; font-size: 0.9rem; }

    /* ── Status badges (explicit contrast pairs) ─────────────────────── */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-green  { background:#d1fae5 !important; color:#065f46 !important; }
    .badge-red    { background:#fee2e2 !important; color:#991b1b !important; }
    .badge-orange { background:#fff7ed !important; color:#9a3412 !important; }
    .badge-gray   { background:#f3f4f6 !important; color:#374151 !important; }
    .badge-blue   { background:#dbeafe !important; color:#1e40af !important; }

    /* ── Metric cards (light bg → dark text) ────────────────────────── */
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        text-align: center;
        color: #1e293b;
    }
    .metric-card .value { font-size: 2.2rem; font-weight: 800; }
    .metric-card .label { font-size: 0.8rem; color: #475569 !important; margin-top: 0.2rem; }

    /* ── Report box (light bg → dark text) ──────────────────────────── */
    .report-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        color: #1e293b;
    }
    .report-box strong, .report-box h3 { color: #1e293b !important; }
    .report-box p { color: #475569 !important; }

    /* ── Agent step cards (light bg → dark text) ─────────────────────── */
    .agent-card {
        border-left: 4px solid #3b82f6;
        background: #eff6ff;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0;
        border-radius: 0 6px 6px 0;
        color: #1e293b;
    }
    .agent-card.complete { border-left-color: #22c55e; background: #f0fdf4; color: #1e293b; }
    .agent-card.error    { border-left-color: #ef4444; background: #fef2f2; color: #7f1d1d; }

    /* ── Disclaimer (amber bg → dark amber text) ─────────────────────── */
    .disclaimer {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 6px;
        padding: 0.7rem 1rem;
        font-size: 0.82rem;
        color: #856404 !important;
        margin: 1rem 0;
    }
    .disclaimer * { color: #856404 !important; }

    /* ── Recommendation cards (custom HTML — explicit contrast) ──────
       Three priority levels, each with a light background and dark text
       so they are readable regardless of the Streamlit theme.          */

    /* IMMEDIATE — light red bg, dark red text */
    .rec-immediate {
        background: #fff0f0;
        border-left: 5px solid #dc2626;
        border-radius: 0 6px 6px 0;
        padding: 0.9rem 1.1rem;
        margin: 0.5rem 0;
        color: #7f1d1d !important;
    }
    .rec-immediate *,
    .rec-immediate p,
    .rec-immediate strong,
    .rec-immediate em,
    .rec-immediate span {
        color: #7f1d1d !important;
    }

    /* SHORT-TERM — light amber bg, dark amber text */
    .rec-short-term {
        background: #fffbeb;
        border-left: 5px solid #d97706;
        border-radius: 0 6px 6px 0;
        padding: 0.9rem 1.1rem;
        margin: 0.5rem 0;
        color: #78350f !important;
    }
    .rec-short-term *,
    .rec-short-term p,
    .rec-short-term strong,
    .rec-short-term em,
    .rec-short-term span {
        color: #78350f !important;
    }

    /* SCHEDULED — light blue bg, dark blue text */
    .rec-scheduled {
        background: #eff6ff;
        border-left: 5px solid #2563eb;
        border-radius: 0 6px 6px 0;
        padding: 0.9rem 1.1rem;
        margin: 0.5rem 0;
        color: #1e3a8a !important;
    }
    .rec-scheduled *,
    .rec-scheduled p,
    .rec-scheduled strong,
    .rec-scheduled em,
    .rec-scheduled span {
        color: #1e3a8a !important;
    }

    /* Ensure Streamlit's stMarkdownContainer doesn't override the above */
    [data-testid="stMarkdownContainer"] .rec-immediate,
    [data-testid="stMarkdownContainer"] .rec-immediate * { color: #7f1d1d !important; }
    [data-testid="stMarkdownContainer"] .rec-short-term,
    [data-testid="stMarkdownContainer"] .rec-short-term * { color: #78350f !important; }
    [data-testid="stMarkdownContainer"] .rec-scheduled,
    [data-testid="stMarkdownContainer"] .rec-scheduled * { color: #1e3a8a !important; }

    /* ── st.metric ────────────────────────────────────────────────── */
    [data-testid="stMetricLabel"]  p { color: #94a3b8 !important; }
    [data-testid="stMetricValue"]    { color: #f1f5f9 !important; }
    [data-testid="stMetricDelta"]    { color: #94a3b8 !important; }

    /* ── st.expander ─────────────────────────────────────────────────
       Header: keep light (dark theme nav); body: keep default theme
       text (near-white in dark mode) EXCEPT where a nested custom
       card overrides with its own background (handled above).        */
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span {
        color: #f1f5f9 !important;
        font-weight: 600;
    }

    /* ── st.text_area (RAG context viewer) ──────────────────────────── */
    [data-testid="stTextArea"] textarea {
        color: #1e293b !important;
        background-color: #f8fafc !important;
    }
    [data-testid="stTextArea"] label {
        color: #e2e8f0 !important;
    }

    /* ── inline <code> inside custom cards ──────────────────────────── */
    [data-testid="stMarkdownContainer"] code {
        color: #1e40af !important;
        background: #eff6ff !important;
    }

    /* ── Sidebar footer note ─────────────────────────────────────────── */
    .css-1d391kg { padding-top: 1rem; }
    section[data-testid="stSidebar"] small { color: #94a3b8 !important; }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Path setup ─────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")
INDEX_DIR = os.path.join(BASE_DIR, "storage", "rag_index")

# ── Imports (after path setup) ─────────────────────────────────────
from llm.groq_client import GroqClient, GroqClientError
from rag.retriever import Retriever
from agents.safety_data_agent import SafetyDataAgent
from agents.risk_detection_agent import RiskDetectionAgent
from agents.compliance_agent import ComplianceAgent
from agents.recommendation_agent import RecommendationAgent
from utils.helpers import (
    load_history,
    save_to_history,
    format_timestamp,
    sanitize_machine_input,
    get_risk_color,
    get_status_color,
    get_status_icon,
    get_action_color,
    build_history_record,
    get_dashboard_stats,
    load_demo_machines,
    format_report_text,
)


# ══════════════════════════════════════════════════════════════════════
# Cached resource initialization
# ══════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def init_retriever() -> tuple:
    """Initialize and cache the RAG retriever."""
    retriever = Retriever(
        knowledge_base_dir=KNOWLEDGE_BASE_DIR,
        index_dir=INDEX_DIR,
        top_k=5,
        chunk_size=500,
        chunk_overlap=100,
    )
    stats = retriever.initialize()
    return retriever, stats


@st.cache_resource(show_spinner=False)
def init_groq_client() -> Optional[GroqClient]:
    """Initialize the Groq client (returns None if not configured)."""
    try:
        return GroqClient()
    except GroqClientError:
        return None


def get_agents(groq_client: Optional[GroqClient], retriever: Retriever):
    """Return instantiated agents."""
    return (
        SafetyDataAgent(groq_client, retriever),
        RiskDetectionAgent(groq_client),
        ComplianceAgent(groq_client),
        RecommendationAgent(groq_client),
    )


# ══════════════════════════════════════════════════════════════════════
# Helper UI components
# ══════════════════════════════════════════════════════════════════════

def render_header():
    st.markdown(
        """
        <div class="main-header">
            <h1>🛡️ AI Mechanical Safety Compliance Advisor</h1>
            <p>Multi-agent AI system for industrial machine safety analysis · Prototype · Educational Use Only</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer():
    st.markdown(
        """
        <div class="disclaimer">
            ⚠️ <strong>PROTOTYPE DISCLAIMER:</strong>
            This application is for educational and demonstration purposes only.
            It does not replace qualified safety professionals, official regulatory standards,
            formal inspections, or legal compliance procedures.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _badge(text: str, color: str) -> str:
    cls_map = {
        "#38a169": "badge-green",
        "#e53e3e": "badge-red",
        "#dd6b20": "badge-orange",
        "#718096": "badge-gray",
        "#3182ce": "badge-blue",
    }
    cls = cls_map.get(color, "badge-gray")
    return f'<span class="badge {cls}">{text}</span>'


def status_badge(status: str) -> str:
    return _badge(status, get_status_color(status))


def risk_badge(level: str) -> str:
    return _badge(level, get_risk_color(level))


def action_badge(action: str) -> str:
    return _badge(action, get_action_color(action))


def rec_card(index: int, priority: str, action: str, issue: str = "", basis: str = "") -> str:
    """
    Return an HTML string for a recommendation card.
    Uses explicit light-background + dark-text classes so the card is
    readable in both light and dark Streamlit themes without relying on
    inherited colour from the theme.
    """
    cls_map = {
        "IMMEDIATE":  ("rec-immediate",  "🛑"),
        "SHORT-TERM": ("rec-short-term", "⚠️"),
        "SCHEDULED":  ("rec-scheduled",  "ℹ️"),
    }
    css_cls, icon = cls_map.get(priority.upper(), ("rec-scheduled", "ℹ️"))

    parts = [
        f'<div class="{css_cls}">',
        f'<strong>{index}. {icon} [{priority}]</strong> {action}',
    ]
    if issue:
        parts.append(f'<br/><em>Issue: {issue}</em>')
    if basis:
        parts.append(f'<br/><em>Basis: {basis}</em>')
    parts.append("</div>")
    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════
# Page: Dashboard
# ══════════════════════════════════════════════════════════════════════

def page_dashboard():
    render_header()
    render_disclaimer()

    history = load_history()
    stats = get_dashboard_stats(history)

    # ── Key metrics ──
    st.subheader("📊 Safety Overview")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    cards = [
        (c1, stats["total_checks"],  "Total Checks",    "#3182ce"),
        (c2, stats["compliant"],     "Compliant",        "#38a169"),
        (c3, stats["non_compliant"], "Non-Compliant",    "#e53e3e"),
        (c4, stats["with_risks"],    "With Risks",       "#dd6b20"),
        (c5, stats["high_risk"],     "High Risk",        "#e53e3e"),
        (c6, stats["stop_required"], "Stop Required",    "#e53e3e"),
    ]
    for col, val, label, color in cards:
        col.markdown(
            f"""<div class="metric-card">
                <div class="value" style="color:{color};">{val}</div>
                <div class="label">{label}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Recent checks ──
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("🕐 Recent Safety Checks")
        recent = stats["recent"]
        if recent:
            for rec in recent:
                icon = get_status_icon(rec.get("overall_status", ""))
                risk_icon = get_status_icon(rec.get("overall_risk_level", ""))
                st.markdown(
                    f"""<div class="report-box" style="margin-bottom:0.5rem;">
                        <strong>{icon} {rec.get('machine_id','N/A')}</strong>
                        &nbsp;|&nbsp; {rec.get('machine_type','N/A')}
                        &nbsp;|&nbsp; {rec.get('timestamp','')}
                        <br/>
                        Status: {status_badge(rec.get('overall_status','N/A'))}
                        &nbsp; Risk: {risk_badge(rec.get('overall_risk_level','N/A'))}
                        &nbsp; Action: {action_badge(rec.get('action_required','N/A'))}
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No safety checks have been performed yet. Go to 🔍 Safety Check to begin.")

    with col_right:
        st.subheader("🚨 Safety Alerts")
        high_risk_records = [h for h in history if h.get("overall_risk_level") == "HIGH"]
        if high_risk_records:
            for rec in high_risk_records[-5:][::-1]:
                st.error(
                    f"🔴 **{rec.get('machine_id','N/A')}** ({rec.get('machine_type','N/A')}) — "
                    f"HIGH RISK detected on {rec.get('timestamp','')}"
                )
        else:
            st.success("✅ No high-risk machines in history.")

        st.markdown("---")
        st.subheader("📋 Compliance Summary")
        if history:
            total = stats["total_checks"]
            if total > 0:
                compliant_pct = (stats["compliant"] / total) * 100
                st.metric("Compliance Rate", f"{compliant_pct:.0f}%")
                nc = stats["non_compliant"]
                if nc > 0:
                    st.warning(f"⚠️ {nc} non-compliant check(s) on record.")
                else:
                    st.success("✅ All recorded checks are compliant.")
        else:
            st.info("No data yet.")

    st.markdown("---")
    st.subheader("💡 Recommended Safety Improvements")
    if history:
        # Collect unique recommendations across history
        all_recs = []
        for h in history[-20:]:
            recs = h.get("recommendation_output", {}).get("recommendations", [])
            for r in recs:
                issue = r.get("issue", "")
                action = r.get("action", "")
                priority = r.get("priority", "")
                if issue and action and (issue, action) not in [(x["issue"], x["action"]) for x in all_recs]:
                    all_recs.append({"issue": issue, "action": action, "priority": priority})

        if all_recs:
            for j, rec in enumerate(all_recs[:6], 1):
                priority = rec.get("priority", "")
                st.markdown(
                    rec_card(j, priority, rec.get("action", "")),
                    unsafe_allow_html=True,
                )
        else:
            st.info("No recommendations available yet.")
    else:
        st.info("Run safety checks to generate improvement recommendations.")


# ══════════════════════════════════════════════════════════════════════
# Page: Safety Check
# ══════════════════════════════════════════════════════════════════════

def page_safety_check():
    render_header()
    render_disclaimer()

    st.subheader("🔍 Machine Safety Check")
    st.write("Enter machine operational data or select a demo machine below, then click **CHECK SAFETY**.")

    # ── Groq API check ──
    groq_configured = GroqClient.is_configured()
    if not groq_configured:
        st.error(
            "⚠️ **GROQ_API_KEY is not configured.** "
            "The system will use fallback rule-based analysis instead of the LLM. "
            "Set `GROQ_API_KEY` in your `.env` file for full AI-powered analysis."
        )

    # ── Demo machine selector ──
    demo_machines = load_demo_machines()
    demo_options = {f"[{m['demo_label']}] {m['machine_id']} — {m['machine_type']}": m for m in demo_machines}

    selected_demo = st.selectbox(
        "Load Demo Machine (optional)",
        ["— Enter manually —"] + list(demo_options.keys()),
        key="demo_selector",
    )

    # Default values
    defaults = {
        "machine_id": "",
        "machine_type": "",
        "temperature": 65.0,
        "pressure": 100.0,
        "rpm": 2500.0,
        "safety_guard": "CLOSED",
        "emergency_stop": "FUNCTIONAL",
        "operating_condition": "NORMAL",
        "notes": "",
    }

    if selected_demo != "— Enter manually —":
        d = demo_options[selected_demo]
        defaults["machine_id"] = d.get("machine_id", "")
        defaults["machine_type"] = d.get("machine_type", "")
        defaults["temperature"] = _safe_float(d.get("temperature"), 65.0)
        defaults["pressure"] = _safe_float(d.get("pressure"), 100.0)
        defaults["rpm"] = _safe_float(d.get("rpm"), 2500.0)
        defaults["safety_guard"] = d.get("safety_guard", "CLOSED") or "CLOSED"
        defaults["emergency_stop"] = d.get("emergency_stop", "FUNCTIONAL") or "FUNCTIONAL"
        defaults["operating_condition"] = d.get("operating_condition", "NORMAL") or "NORMAL"
        defaults["notes"] = d.get("notes", "")
        st.info(f"📋 Demo machine loaded: **{d.get('demo_label','')}**")

    st.markdown("---")
    st.markdown("#### Machine Information")
    col1, col2 = st.columns(2)
    with col1:
        machine_id = st.text_input("Machine ID *", value=defaults["machine_id"], placeholder="e.g. M001")
    with col2:
        machine_type = st.text_input("Machine Type *", value=defaults["machine_type"], placeholder="e.g. Industrial Press")

    st.markdown("#### Operational Parameters")
    col3, col4, col5 = st.columns(3)
    with col3:
        temp_enabled = st.checkbox("Provide Temperature", value=(defaults["temperature"] is not None))
        temperature = st.number_input(
            "Temperature (°C)",
            min_value=-50.0, max_value=500.0,
            value=float(defaults["temperature"]) if defaults["temperature"] is not None else 65.0,
            step=0.5,
            disabled=not temp_enabled,
        )
    with col4:
        press_enabled = st.checkbox("Provide Pressure", value=(defaults["pressure"] is not None))
        pressure = st.number_input(
            "Pressure (PSI)",
            min_value=0.0, max_value=1000.0,
            value=float(defaults["pressure"]) if defaults["pressure"] is not None else 100.0,
            step=1.0,
            disabled=not press_enabled,
        )
    with col5:
        rpm_enabled = st.checkbox("Provide RPM", value=(defaults["rpm"] is not None))
        rpm = st.number_input(
            "RPM",
            min_value=0.0, max_value=10000.0,
            value=float(defaults["rpm"]) if defaults["rpm"] is not None else 2500.0,
            step=50.0,
            disabled=not rpm_enabled,
        )

    st.markdown("#### Safety Device Status")
    col6, col7 = st.columns(2)
    with col6:
        safety_guard_options = ["CLOSED", "OPEN", "UNKNOWN"]
        sg_default_idx = safety_guard_options.index(defaults["safety_guard"]) if defaults["safety_guard"] in safety_guard_options else 0
        safety_guard = st.selectbox("Safety Guard Status", safety_guard_options, index=sg_default_idx)
    with col7:
        estop_options = ["FUNCTIONAL", "NON-FUNCTIONAL", "UNKNOWN"]
        es_default_idx = estop_options.index(defaults["emergency_stop"]) if defaults["emergency_stop"] in estop_options else 0
        emergency_stop = st.selectbox("Emergency Stop Status", estop_options, index=es_default_idx)

    st.markdown("#### Operating Condition & Notes")
    col8, col9 = st.columns(2)
    with col8:
        op_cond_options = ["NORMAL", "MAINTENANCE", "FAULT", "EMERGENCY", "UNKNOWN"]
        oc_default_idx = op_cond_options.index(defaults["operating_condition"]) if defaults["operating_condition"] in op_cond_options else 0
        operating_condition = st.selectbox("Operating Condition", op_cond_options, index=oc_default_idx)
    with col9:
        notes = st.text_area("Additional Notes", value=defaults["notes"], height=100)

    st.markdown("---")
    check_btn = st.button("🔍 CHECK SAFETY", type="primary", use_container_width=True)

    if check_btn:
        # Validate required fields
        if not machine_id.strip():
            st.error("Machine ID is required.")
            return
        if not machine_type.strip():
            st.error("Machine Type is required.")
            return

        # Assemble machine data
        machine_data = {
            "machine_id": machine_id.strip(),
            "machine_type": machine_type.strip(),
            "temperature": temperature if temp_enabled else None,
            "pressure": pressure if press_enabled else None,
            "rpm": rpm if rpm_enabled else None,
            "safety_guard": safety_guard,
            "emergency_stop": emergency_stop,
            "operating_condition": operating_condition,
            "notes": notes.strip(),
        }
        machine_data = sanitize_machine_input(machine_data)

        # Store in session state and run pipeline
        st.session_state["last_machine_data"] = machine_data
        _run_safety_pipeline(machine_data, groq_configured)


def _safe_float(val, default=None):
    """Safely convert CSV string to float."""
    if val is None or str(val).strip() == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _run_safety_pipeline(machine_data: Dict[str, Any], groq_configured: bool):
    """Execute the full multi-agent safety pipeline with progress display."""

    st.markdown("---")
    st.subheader("⚙️ Agent Pipeline Execution")

    retriever, rag_stats = init_retriever()
    groq_client = init_groq_client() if groq_configured else None

    if groq_client is None:
        st.warning("🔶 LLM (Groq) not available — using fallback rule-based analysis.")

    # ── Agents ──
    safety_agent = SafetyDataAgent(groq_client, retriever)
    risk_agent = RiskDetectionAgent(groq_client)
    compliance_agent = ComplianceAgent(groq_client)
    recommendation_agent = RecommendationAgent(groq_client)

    progress = st.progress(0, text="Starting pipeline...")
    results = {}

    # Step 1: Safety Data Agent + RAG
    with st.expander("🔎 Step 1: Safety Data Agent — RAG Retrieval", expanded=True):
        st.markdown('<div class="agent-card">Running Safety Data Agent...</div>', unsafe_allow_html=True)
        try:
            safety_data_output = safety_agent.run(machine_data)
            results["safety_data"] = safety_data_output
            sources = safety_data_output.get("sources", [])
            context_text = safety_data_output.get("full_context_text", "")

            st.markdown('<div class="agent-card complete">✅ Safety Data Agent complete</div>', unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Relevant Parameters:**", safety_data_output.get("relevant_parameters", []))
                st.write("**Relevant Topics:**", safety_data_output.get("relevant_topics", []))
            with col_b:
                st.write("**Data Completeness:**", safety_data_output.get("data_completeness", "N/A"))
                st.write("**Sources Retrieved:**", sources)

            if context_text:
                with st.expander("📄 Retrieved Safety Context", expanded=False):
                    st.text(context_text[:3000] + ("..." if len(context_text) > 3000 else ""))
        except Exception as e:
            st.error(f"Safety Data Agent error: {e}")
            results["safety_data"] = {
                "agent": "Safety Data Agent", "status": "ERROR",
                "machine_data": machine_data,
                "machine_data_formatted": str(machine_data),
                "full_context_text": "",
                "sources": [],
            }

    progress.progress(25, text="Risk Detection Agent running...")

    # Step 2: Risk Detection Agent
    with st.expander("⚠️ Step 2: Risk Detection Agent", expanded=True):
        st.markdown('<div class="agent-card">Running Risk Detection Agent...</div>', unsafe_allow_html=True)
        try:
            risk_output = risk_agent.run(results["safety_data"])
            results["risk"] = risk_output
            st.markdown('<div class="agent-card complete">✅ Risk Detection Agent complete</div>', unsafe_allow_html=True)

            overall_risk = risk_output.get("overall_risk_level", "N/A")
            risks = risk_output.get("risks", [])
            st.markdown(
                f"**Overall Risk Level:** {risk_badge(overall_risk)}  &nbsp; **Risks Detected:** {len(risks)}",
                unsafe_allow_html=True,
            )
            if risks:
                for r in risks:
                    lvl = r.get("risk_level", "")
                    st.markdown(
                        f"- {risk_badge(lvl)} **{r.get('parameter','?')}** ({r.get('observed_value','?')}): "
                        f"{r.get('risk_description','')}",
                        unsafe_allow_html=True,
                    )
            else:
                st.success("No risks detected.")

        except Exception as e:
            st.error(f"Risk Detection Agent error: {e}")
            results["risk"] = {"agent": "Risk Detection Agent", "risks": [], "overall_risk_level": "INSUFFICIENT EVIDENCE", "risk_summary": "Error"}

    progress.progress(50, text="Compliance Agent running...")

    # Step 3: Compliance Agent
    with st.expander("✅ Step 3: Compliance Agent", expanded=True):
        st.markdown('<div class="agent-card">Running Compliance Agent...</div>', unsafe_allow_html=True)
        try:
            compliance_output = compliance_agent.run(results["safety_data"])
            results["compliance"] = compliance_output
            st.markdown('<div class="agent-card complete">✅ Compliance Agent complete</div>', unsafe_allow_html=True)

            overall_status = compliance_output.get("overall_status", "N/A")
            st.markdown(
                f"**Overall Compliance:** {status_badge(overall_status)}",
                unsafe_allow_html=True,
            )
            findings = compliance_output.get("compliance_findings", [])
            for f in findings:
                icon = get_status_icon(f.get("status", ""))
                st.markdown(
                    f"- {icon} **{f.get('parameter','?')}**: {f.get('status','')} — {f.get('reason','')}",
                    unsafe_allow_html=True,
                )

        except Exception as e:
            st.error(f"Compliance Agent error: {e}")
            results["compliance"] = {"agent": "Compliance Agent", "compliance_findings": [], "overall_status": "INSUFFICIENT EVIDENCE", "compliance_summary": "Error"}

    progress.progress(75, text="Recommendation Agent running...")

    # Step 4: Recommendation Agent
    with st.expander("💡 Step 4: Safety Recommendation Agent", expanded=True):
        st.markdown('<div class="agent-card">Running Safety Recommendation Agent...</div>', unsafe_allow_html=True)
        try:
            recommendation_output = recommendation_agent.run(
                results["safety_data"],
                results["risk"],
                results["compliance"],
            )
            results["recommendation"] = recommendation_output
            st.markdown('<div class="agent-card complete">✅ Safety Recommendation Agent complete</div>', unsafe_allow_html=True)

            action = recommendation_output.get("overall_action_required", "N/A")
            st.markdown(
                f"**Action Required:** {action_badge(action)}",
                unsafe_allow_html=True,
            )
            recs = recommendation_output.get("recommendations", [])
            for k, rec in enumerate(recs, 1):
                priority = rec.get("priority", "")
                st.markdown(
                    rec_card(k, priority, rec.get("action", "")),
                    unsafe_allow_html=True,
                )

        except Exception as e:
            st.error(f"Recommendation Agent error: {e}")
            results["recommendation"] = {"agent": "Recommendation Agent", "recommendations": [], "overall_action_required": "N/A", "summary": "Error", "disclaimer": ""}

    progress.progress(100, text="Pipeline complete.")
    st.success("✅ Safety pipeline completed. Generating final report...")

    # Save to history
    history_record = build_history_record(
        machine_data=machine_data,
        risk_output=results["risk"],
        compliance_output=results["compliance"],
        recommendation_output=results["recommendation"],
        safety_data_output=results["safety_data"],
    )
    save_to_history(history_record)
    st.session_state["last_results"] = results
    st.session_state["last_machine_data"] = machine_data

    # Navigate hint
    st.info("📊 View the full report on the **Safety Report** page.")


# ══════════════════════════════════════════════════════════════════════
# Page: Safety Report
# ══════════════════════════════════════════════════════════════════════

def page_safety_report():
    render_header()

    st.subheader("📊 Safety Report")

    results = st.session_state.get("last_results")
    machine_data = st.session_state.get("last_machine_data")

    # If session state was cleared (e.g. page refresh or navigation), fall back
    # to the most recent record in persistent history storage.
    if not results or not machine_data:
        history = load_history()
        if history:
            latest = history[-1]
            machine_data = latest.get("machine_data", {})
            results = {
                "risk": latest.get("risk_output", {}),
                "compliance": latest.get("compliance_output", {}),
                "recommendation": latest.get("recommendation_output", {}),
                "safety_data": latest.get("safety_data_output", {}),
            }
            st.info(
                f"ℹ️ Showing most recent report from history "
                f"({latest.get('timestamp', '')} — {latest.get('machine_id', '')}). "
                "Run a new Safety Check to update."
            )
        else:
            st.info("No report available yet. Please run a Safety Check first.")
            return

    risk_output = results.get("risk", {})
    compliance_output = results.get("compliance", {})
    recommendation_output = results.get("recommendation", {})
    safety_data_output = results.get("safety_data", {})

    overall_risk = risk_output.get("overall_risk_level", "N/A")
    overall_status = compliance_output.get("overall_status", "N/A")
    action_required = recommendation_output.get("overall_action_required", "N/A")

    # ── Header ──
    st.markdown(
        f"""
        <div class="report-box" style="border-left: 6px solid {get_action_color(action_required)};">
            <h3 style="margin:0 0 0.5rem; color:#1e293b;">MECHANICAL SAFETY COMPLIANCE REPORT</h3>
            <p style="margin:0; color:#475569; font-size:0.85rem;">
                Machine: <strong style="color:#1e293b;">{machine_data.get('machine_id','N/A')}</strong> |
                Type: <strong style="color:#1e293b;">{machine_data.get('machine_type','N/A')}</strong> |
                Generated: {format_timestamp()}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_disclaimer()

    # ── Status summary ──
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f"""<div class="metric-card">
            <div class="value" style="color:{get_risk_color(overall_risk)};font-size:1.5rem;">{get_status_icon(overall_risk)} {overall_risk}</div>
            <div class="label">Overall Risk Level</div>
        </div>""",
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"""<div class="metric-card">
            <div class="value" style="color:{get_status_color(overall_status)};font-size:1.5rem;">{get_status_icon(overall_status)} {overall_status}</div>
            <div class="label">Compliance Status</div>
        </div>""",
        unsafe_allow_html=True,
    )
    c3.markdown(
        f"""<div class="metric-card">
            <div class="value" style="color:{get_action_color(action_required)};font-size:1.3rem;">{get_status_icon(action_required)} {action_required}</div>
            <div class="label">Action Required</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Operating parameters ──
    with st.expander("🔧 Operating Parameters", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Machine ID:** {machine_data.get('machine_id','N/A')}")
            st.markdown(f"**Machine Type:** {machine_data.get('machine_type','N/A')}")
            st.markdown(f"**Temperature:** {machine_data.get('temperature','NOT PROVIDED')}°C")
            st.markdown(f"**Pressure:** {machine_data.get('pressure','NOT PROVIDED')} PSI")
        with col_b:
            st.markdown(f"**RPM:** {machine_data.get('rpm','NOT PROVIDED')}")
            st.markdown(f"**Safety Guard:** {machine_data.get('safety_guard','NOT PROVIDED')}")
            st.markdown(f"**Emergency Stop:** {machine_data.get('emergency_stop','NOT PROVIDED')}")
            st.markdown(f"**Operating Condition:** {machine_data.get('operating_condition','NOT PROVIDED')}")
        if machine_data.get("notes"):
            st.markdown(f"**Notes:** {machine_data['notes']}")

    # ── Detected risks ──
    with st.expander("⚠️ Detected Risks", expanded=True):
        risks = risk_output.get("risks", [])
        if risks:
            for risk in risks:
                lvl = risk.get("risk_level", "N/A")
                color = get_risk_color(lvl)
                st.markdown(
                    f"""<div style="border-left:4px solid {color}; padding:0.8rem 1rem; margin:0.5rem 0; background:#fafafa; border-radius:0 6px 6px 0; color:#1e293b;">
                        <strong style="color:#1e293b;">{get_status_icon(lvl)} [{lvl}] {risk.get('parameter','?')}</strong> — {risk.get('observed_value','')}
                        <br/><em style="color:#374151;">{risk.get('risk_description','')}</em>
                        <br/><small style="color:#475569;">Reason: {risk.get('reason','')} | Source: {risk.get('source','')}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.success("No risks detected.")
        st.markdown(f"**Risk Summary:** {risk_output.get('risk_summary','N/A')}")

    # ── Compliance findings ──
    with st.expander("✅ Compliance Findings", expanded=True):
        findings = compliance_output.get("compliance_findings", [])
        for finding in findings:
            status = finding.get("status", "N/A")
            color = get_status_color(status)
            st.markdown(
                f"""<div style="border-left:4px solid {color}; padding:0.8rem 1rem; margin:0.5rem 0; background:#fafafa; border-radius:0 6px 6px 0; color:#1e293b;">
                    <strong style="color:#1e293b;">{get_status_icon(status)} {finding.get('parameter','?')}</strong>: {status_badge(status)}
                    <br/>Observed: <code style="color:#1e40af; background:#eff6ff;">{finding.get('observed_value','')}</code>
                    &nbsp;|&nbsp; Required: <code style="color:#1e40af; background:#eff6ff;">{finding.get('required_condition','')}</code>
                    <br/><small style="color:#475569;">{finding.get('reason','')} | Source: {finding.get('source','')}</small>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown(f"**Compliance Summary:** {compliance_output.get('compliance_summary','N/A')}")

    # ── Recommendations ──
    with st.expander("💡 Recommended Actions", expanded=True):
        recs = recommendation_output.get("recommendations", [])
        for i, rec in enumerate(recs, 1):
            priority = rec.get("priority", "")
            st.markdown(
                rec_card(
                    i,
                    priority,
                    rec.get("action", ""),
                    issue=rec.get("issue", ""),
                    basis=rec.get("basis", ""),
                ),
                unsafe_allow_html=True,
            )
        st.markdown(f"**Summary:** {recommendation_output.get('summary','N/A')}")

    # ── Supporting information ──
    with st.expander("📚 Supporting Safety Information (Retrieved Context)", expanded=False):
        sources = safety_data_output.get("sources", [])
        if sources:
            st.write("**Source Documents:**", sources)
        ctx = safety_data_output.get("full_context_text", "")
        if ctx:
            st.text_area("Retrieved Context", value=ctx, height=300)
        else:
            st.info("No retrieved context available.")

    # ── Plain text report download ──
    st.markdown("---")
    st.subheader("📥 Export Report")
    report_text = format_report_text(
        machine_data=machine_data,
        risk_output=risk_output,
        compliance_output=compliance_output,
        recommendation_output=recommendation_output,
    )
    st.download_button(
        label="⬇️ Download Plain Text Report",
        data=report_text,
        file_name=f"safety_report_{machine_data.get('machine_id','unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
    )
    st.download_button(
        label="⬇️ Download JSON Report",
        data=json.dumps(
            {
                "machine_data": machine_data,
                "risk": risk_output,
                "compliance": compliance_output,
                "recommendation": recommendation_output,
            },
            indent=2,
            default=str,
        ),
        file_name=f"safety_report_{machine_data.get('machine_id','unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )


# ══════════════════════════════════════════════════════════════════════
# Page: Knowledge Base
# ══════════════════════════════════════════════════════════════════════

def page_knowledge_base():
    render_header()
    st.subheader("📚 Knowledge Base")

    retriever, rag_stats = init_retriever()
    status_str = rag_stats.get("status", "unknown")

    if status_str == "error":
        st.error(f"❌ RAG system error: {rag_stats.get('error', 'Unknown error')}")
        return

    st.success(
        f"✅ RAG system ready — {rag_stats.get('total_chunks', 0)} indexed chunks "
        f"from {rag_stats.get('total_documents', 0)} document(s). "
        f"Status: {status_str.replace('_', ' ').title()}"
    )

    # ── Stats ──
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Documents", rag_stats.get("total_documents", 0))
    col2.metric("Total Chunks", rag_stats.get("total_chunks", 0))
    col3.metric("Vectorizer", rag_stats.get("vectorizer_type", "N/A"))

    # ── Document list ──
    st.markdown("---")
    st.subheader("📄 Indexed Documents")
    docs = rag_stats.get("documents", {})
    for doc_name, chunk_count in docs.items():
        st.markdown(f"- **{doc_name}** — {chunk_count} chunks")

    # ── Upload new document ──
    st.markdown("---")
    st.subheader("📤 Upload Document to Knowledge Base")
    st.info(
        "You can upload additional .txt or .pdf files to extend the knowledge base. "
        "The system will index the new document and it will be available for future safety checks."
    )
    uploaded_file = st.file_uploader(
        "Upload .txt or .pdf file",
        type=["txt", "pdf"],
        key="kb_upload",
    )
    if uploaded_file is not None:
        save_path = os.path.join(KNOWLEDGE_BASE_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        with st.spinner("Indexing new document..."):
            result = retriever.add_document(save_path)
        if result.get("status") in ("document_added",):
            st.success(
                f"✅ Document '{uploaded_file.name}' added. "
                f"{result.get('new_chunks', 0)} new chunks indexed. "
                f"Total chunks: {result.get('total_chunks', 0)}."
            )
            # Clear cache so next run picks up new doc
            st.cache_resource.clear()
        else:
            st.error(f"❌ Failed to index document: {result.get('error', 'Unknown error')}")

    # ── Rebuild index button ──
    st.markdown("---")
    if st.button("🔄 Rebuild RAG Index"):
        with st.spinner("Rebuilding index from all documents..."):
            retriever.initialize(force_rebuild=True)
            st.cache_resource.clear()
        st.success("Index rebuilt successfully.")
        st.rerun()

    # ── RAG search test ──
    st.markdown("---")
    st.subheader("🔍 Test Knowledge Retrieval")
    test_query = st.text_input("Enter a test query", placeholder="e.g. safety guard open risk")
    if st.button("Search Knowledge Base") and test_query:
        ctx = retriever.retrieve(test_query, top_k=3)
        if ctx.is_empty:
            st.warning("No relevant documents found for this query.")
        else:
            for i, (chunk, score) in enumerate(zip(ctx.chunks, ctx.scores), 1):
                with st.expander(f"Result {i}: {chunk.source} (score: {score:.3f})", expanded=(i == 1)):
                    st.text(chunk.text)


# ══════════════════════════════════════════════════════════════════════
# Page: History
# ══════════════════════════════════════════════════════════════════════

def page_history():
    render_header()
    st.subheader("📜 Safety Check History")

    history = load_history()

    if not history:
        st.info("No safety check history available yet. Run a safety check to create records.")
        return

    st.write(f"**Total records:** {len(history)}")

    # ── Summary table ──
    cols_header = st.columns([2, 2, 1.5, 1.5, 2, 2])
    headers = ["Timestamp", "Machine ID", "Machine Type", "Risk Level", "Status", "Action"]
    for col, h in zip(cols_header, headers):
        col.markdown(f"**{h}**")
    st.markdown("---")

    for i, rec in enumerate(reversed(history)):
        row = st.columns([2, 2, 1.5, 1.5, 2, 2])
        row[0].write(rec.get("timestamp", "N/A"))
        row[1].write(rec.get("machine_id", "N/A"))
        row[2].write(rec.get("machine_type", "N/A"))
        row[3].markdown(
            risk_badge(rec.get("overall_risk_level", "N/A")),
            unsafe_allow_html=True,
        )
        row[4].markdown(
            status_badge(rec.get("overall_status", "N/A")),
            unsafe_allow_html=True,
        )
        row[5].markdown(
            action_badge(rec.get("action_required", "N/A")),
            unsafe_allow_html=True,
        )

    # ── Detail view ──
    st.markdown("---")
    st.subheader("🔎 View Historical Report")
    options = {
        f"{rec.get('timestamp','')} | {rec.get('machine_id','')} | {rec.get('overall_status','')}": i
        for i, rec in enumerate(history)
    }
    if options:
        selected = st.selectbox("Select a record", list(reversed(list(options.keys()))))
        if selected:
            idx = options[selected]
            rec = history[idx]

            machine_data = rec.get("machine_data", {})
            risk_output = rec.get("risk_output", {})
            compliance_output = rec.get("compliance_output", {})
            recommendation_output = rec.get("recommendation_output", {})

            with st.expander("Report Details", expanded=True):
                report_text = format_report_text(
                    machine_data=machine_data,
                    risk_output=risk_output,
                    compliance_output=compliance_output,
                    recommendation_output=recommendation_output,
                    timestamp=rec.get("timestamp"),
                )
                st.text(report_text)

    # ── Clear history ──
    st.markdown("---")
    if st.button("🗑️ Clear All History", type="secondary"):
        from utils.helpers import clear_history
        clear_history()
        st.success("History cleared.")
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# Page: About
# ══════════════════════════════════════════════════════════════════════

def page_about():
    render_header()
    st.subheader("ℹ️ About This Application")

    st.markdown(
        """
        ## AI Mechanical Safety Compliance Advisor
        **Prototype · Educational Use Only**

        ---

        ### 📋 Problem Statement
        Industrial machines must comply with strict safety regulations and operational standards.
        Monitoring compliance across large industrial facilities can be difficult.
        This prototype demonstrates an AI-powered approach to detecting compliance risks.

        ---

        ### 🏗️ Architecture

        ```
        USER INPUT
            ↓
        STREAMLIT MACHINE INPUT
            ↓
        SAFETY DATA AGENT  ←── RAG (TF-IDF Vector Store + Knowledge Base)
            ↓
        RISK DETECTION AGENT
            ↓
        COMPLIANCE AGENT
            ↓
        SAFETY RECOMMENDATION AGENT
            ↓
        FINAL SAFETY REPORT + DASHBOARD
        ```

        ---

        ### 🤖 Multi-Agent System

        | Agent | Role |
        |---|---|
        | **Safety Data Agent** | Retrieves relevant safety information from the RAG knowledge base |
        | **Risk Detection Agent** | Analyzes parameters and detects hazardous conditions |
        | **Compliance Agent** | Compares observed conditions with retrieved requirements |
        | **Safety Recommendation Agent** | Generates corrective actions based on findings |

        ---

        ### 📚 RAG System
        - Documents are chunked into ~500 character segments with overlap
        - TF-IDF vectorization (scikit-learn) is used for embeddings
        - Cosine similarity search retrieves the most relevant chunks
        - Retrieved context is passed to each LLM agent as authoritative knowledge

        ---

        ### 🔧 Technology Stack
        - **Python 3.9+**
        - **Streamlit** — Web UI
        - **Groq API** — LLM inference
        - **openai/gpt-oss-120b** — LLM model (via Groq)
        - **scikit-learn** — TF-IDF vectorization for RAG
        - **python-dotenv** — Environment variable management

        ---

        ### ⚠️ Limitations
        1. This is a prototype for educational purposes only.
        2. The knowledge base contains demo documents, not official standards.
        3. The system does not connect to physical machines.
        4. AI output should never replace qualified safety professionals.
        5. No legally binding compliance determinations are made.

        ---

        ### 📄 Disclaimer
        > **This application is a prototype for educational and demonstration purposes only.
        > It does not replace qualified safety professionals, official regulatory standards,
        > formal inspections, or legal compliance procedures.**
        """
    )

    st.markdown("---")
    st.subheader("🔧 System Status")

    groq_ok = GroqClient.is_configured()
    st.write(f"**Groq API:** {'✅ Configured' if groq_ok else '❌ Not configured (set GROQ_API_KEY)'}")

    retriever, rag_stats = init_retriever()
    rag_ok = retriever.is_ready()
    st.write(f"**RAG System:** {'✅ Ready' if rag_ok else '❌ Not ready'} — {rag_stats.get('total_chunks', 0)} chunks")
    st.write(f"**LLM Model:** openai/gpt-oss-120b (via Groq)")


# ══════════════════════════════════════════════════════════════════════
# Sidebar navigation and main router
# ══════════════════════════════════════════════════════════════════════

PAGES = {
    "🏠 Dashboard": page_dashboard,
    "🔍 Safety Check": page_safety_check,
    "📊 Safety Report": page_safety_report,
    "📚 Knowledge Base": page_knowledge_base,
    "📜 History": page_history,
    "ℹ️ About": page_about,
}


def main():
    with st.sidebar:
        st.markdown("### 🛡️ Safety Advisor")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            list(PAGES.keys()),
            key="nav",
            label_visibility="collapsed",
        )

        st.markdown("---")
        # RAG status indicator
        try:
            retriever, stats = init_retriever()
            if retriever.is_ready():
                st.success(f"📚 RAG: {stats.get('total_chunks',0)} chunks ready")
            else:
                st.warning("📚 RAG: not ready")
        except Exception:
            st.error("📚 RAG: error")

        # Groq status
        if GroqClient.is_configured():
            st.success("🤖 Groq: configured")
        else:
            st.warning("🤖 Groq: not configured")

        st.markdown("---")
        st.markdown(
            "<small style='color:#94a3b8;'>Prototype · Educational Use Only<br/>Not for production industrial use.</small>",
            unsafe_allow_html=True,
        )

    # Route to selected page
    PAGES[page]()


if __name__ == "__main__":
    main()
