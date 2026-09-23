"""
Utility helpers for the AI Mechanical Safety Compliance Advisor.
Handles history storage, formatting, input sanitization, and UI helpers.
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional


HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "storage",
    "history.json",
)

DEMO_MACHINES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "demo_machines.csv",
)


# ──────────────────────────────────────────────
# History management
# ──────────────────────────────────────────────

def load_history() -> List[Dict[str, Any]]:
    """Load all previous safety check records from history.json."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_to_history(record: Dict[str, Any]) -> None:
    """Append a safety check record to history.json."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = load_history()
    history.append(record)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, default=str)


def clear_history() -> None:
    """Clear all history records."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


# ──────────────────────────────────────────────
# Demo machine data
# ──────────────────────────────────────────────

def load_demo_machines() -> List[Dict[str, Any]]:
    """Load demo machine data from CSV file."""
    if not os.path.exists(DEMO_MACHINES_FILE):
        return []
    machines = []
    try:
        with open(DEMO_MACHINES_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                machines.append(dict(row))
    except IOError:
        pass
    return machines


# ──────────────────────────────────────────────
# Formatting helpers
# ──────────────────────────────────────────────

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Return ISO-8601 timestamp string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp string."""
    try:
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def format_report_text(
    machine_data: Dict[str, Any],
    risk_output: Dict[str, Any],
    compliance_output: Dict[str, Any],
    recommendation_output: Dict[str, Any],
    timestamp: Optional[str] = None,
) -> str:
    """
    Generate a plain-text safety report from agent outputs.
    Used for display and export.
    """
    ts = timestamp or format_timestamp()
    lines = [
        "=" * 60,
        "       MECHANICAL SAFETY COMPLIANCE REPORT",
        "       (PROTOTYPE - FOR EDUCATIONAL PURPOSES ONLY)",
        "=" * 60,
        f"Report Generated: {ts}",
        "",
        "─" * 60,
        "MACHINE INFORMATION",
        "─" * 60,
        f"Machine ID:    {machine_data.get('machine_id', 'N/A')}",
        f"Machine Type:  {machine_data.get('machine_type', 'N/A')}",
        "",
        "─" * 60,
        "OPERATING PARAMETERS",
        "─" * 60,
        f"Temperature:       {_fmt_val(machine_data.get('temperature'))} deg C",
        f"Pressure:          {_fmt_val(machine_data.get('pressure'))} PSI",
        f"RPM:               {_fmt_val(machine_data.get('rpm'))}",
        f"Safety Guard:      {machine_data.get('safety_guard', 'NOT PROVIDED')}",
        f"Emergency Stop:    {machine_data.get('emergency_stop', 'NOT PROVIDED')}",
        f"Operating Cond.:   {machine_data.get('operating_condition', 'NOT PROVIDED')}",
        f"Notes:             {machine_data.get('notes', 'None')}",
        "",
        "─" * 60,
        "OVERALL STATUS",
        "─" * 60,
        f"Risk Level:        {risk_output.get('overall_risk_level', 'N/A')}",
        f"Compliance:        {compliance_output.get('overall_status', 'N/A')}",
        f"Action Required:   {recommendation_output.get('overall_action_required', 'N/A')}",
        "",
        "─" * 60,
        "DETECTED RISKS",
        "─" * 60,
    ]

    risks = risk_output.get("risks", [])
    if risks:
        for i, risk in enumerate(risks, 1):
            lines.append(
                f"{i}. [{risk.get('risk_level', 'N/A')}] {risk.get('parameter', 'N/A')}: "
                f"{risk.get('risk_description', '')}"
            )
            lines.append(f"   Reason: {risk.get('reason', '')}")
            lines.append(f"   Source: {risk.get('source', '')}")
    else:
        lines.append("No risks detected.")

    lines += [
        "",
        f"Overall Risk Summary: {risk_output.get('risk_summary', 'N/A')}",
        "",
        "─" * 60,
        "COMPLIANCE FINDINGS",
        "─" * 60,
    ]

    findings = compliance_output.get("compliance_findings", [])
    for f in findings:
        lines.append(
            f"  {f.get('parameter', 'N/A')}: {f.get('status', 'N/A')}"
        )
        lines.append(f"    Observed: {f.get('observed_value', 'N/A')}")
        lines.append(f"    Required: {f.get('required_condition', 'N/A')}")
        lines.append(f"    Reason:   {f.get('reason', 'N/A')}")
        lines.append(f"    Source:   {f.get('source', 'N/A')}")

    lines += [
        "",
        f"Overall Compliance: {compliance_output.get('compliance_summary', 'N/A')}",
        "",
        "─" * 60,
        "RECOMMENDED ACTIONS",
        "─" * 60,
    ]

    recs = recommendation_output.get("recommendations", [])
    for i, rec in enumerate(recs, 1):
        lines.append(
            f"{i}. [{rec.get('priority', 'N/A')}] {rec.get('action', 'N/A')}"
        )
        lines.append(f"   Issue: {rec.get('issue', '')}")
        lines.append(f"   Basis: {rec.get('basis', '')}")

    lines += [
        "",
        "─" * 60,
        "DISCLAIMER",
        "─" * 60,
        recommendation_output.get("disclaimer", ""),
        "=" * 60,
    ]

    return "\n".join(lines)


def _fmt_val(val) -> str:
    """Format a possibly-None value for display."""
    if val is None or val == "":
        return "NOT PROVIDED"
    return str(val)


# ──────────────────────────────────────────────
# Input sanitization
# ──────────────────────────────────────────────

def sanitize_machine_input(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize and normalize machine input data.
    Converts empty strings to None for numeric fields.
    """
    result = dict(raw)

    for key in ("temperature", "pressure", "rpm"):
        val = result.get(key)
        if val == "" or val is None:
            result[key] = None
        else:
            try:
                result[key] = float(val)
            except (ValueError, TypeError):
                result[key] = None

    for key in ("safety_guard", "emergency_stop", "operating_condition"):
        val = result.get(key, "")
        result[key] = str(val).strip() if val else ""

    return result


# ──────────────────────────────────────────────
# UI display helpers
# ──────────────────────────────────────────────

def get_risk_color(risk_level: str) -> str:
    """Return a CSS color string for the given risk level."""
    mapping = {
        "HIGH": "#e53e3e",        # red
        "MEDIUM": "#dd6b20",      # orange
        "LOW": "#38a169",         # green
        "INSUFFICIENT EVIDENCE": "#718096",  # gray
    }
    return mapping.get(str(risk_level).upper(), "#718096")


def get_status_color(status: str) -> str:
    """Return a CSS color string for compliance status."""
    mapping = {
        "COMPLIANT": "#38a169",
        "NON-COMPLIANT": "#e53e3e",
        "INSUFFICIENT EVIDENCE": "#718096",
    }
    return mapping.get(str(status).upper(), "#718096")


def get_status_icon(status: str) -> str:
    """Return a status icon string."""
    mapping = {
        "COMPLIANT": "✅",
        "NON-COMPLIANT": "❌",
        "INSUFFICIENT EVIDENCE": "⚠️",
        "HIGH": "🔴",
        "MEDIUM": "🟠",
        "LOW": "🟢",
        "STOP MACHINE": "🛑",
        "CAUTION REVIEW": "⚠️",
        "MONITOR": "👁️",
        "NO ACTION REQUIRED": "✅",
        "OK": "✅",
        "ERROR": "❌",
    }
    return mapping.get(str(status).upper(), "ℹ️")


def get_action_color(action: str) -> str:
    """Return color for action required."""
    mapping = {
        "STOP MACHINE": "#e53e3e",
        "CAUTION REVIEW": "#dd6b20",
        "MONITOR": "#3182ce",
        "NO ACTION REQUIRED": "#38a169",
    }
    return mapping.get(str(action).upper(), "#718096")


def build_history_record(
    machine_data: Dict[str, Any],
    risk_output: Dict[str, Any],
    compliance_output: Dict[str, Any],
    recommendation_output: Dict[str, Any],
    safety_data_output: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a history record from agent outputs."""
    return {
        "timestamp": format_timestamp(),
        "machine_id": machine_data.get("machine_id", "N/A"),
        "machine_type": machine_data.get("machine_type", "N/A"),
        "overall_risk_level": risk_output.get("overall_risk_level", "N/A"),
        "overall_status": compliance_output.get("overall_status", "N/A"),
        "action_required": recommendation_output.get("overall_action_required", "N/A"),
        "risk_count": len(risk_output.get("risks", [])),
        "sources": safety_data_output.get("sources", []),
        "machine_data": machine_data,
        "risk_output": risk_output,
        "compliance_output": compliance_output,
        "recommendation_output": recommendation_output,
        "safety_data_output": {
            k: v for k, v in safety_data_output.items()
            if k not in ("retrieved_context",)  # exclude non-serializable objects
        },
    }


def get_dashboard_stats(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute dashboard statistics from history records."""
    total = len(history)
    compliant = sum(1 for h in history if h.get("overall_status") == "COMPLIANT")
    non_compliant = sum(1 for h in history if h.get("overall_status") == "NON-COMPLIANT")
    with_risks = sum(1 for h in history if h.get("risk_count", 0) > 0)
    high_risk = sum(1 for h in history if h.get("overall_risk_level") == "HIGH")
    stop_required = sum(1 for h in history if h.get("action_required") == "STOP MACHINE")

    return {
        "total_checks": total,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "with_risks": with_risks,
        "high_risk": high_risk,
        "stop_required": stop_required,
        "recent": history[-10:][::-1] if history else [],
    }
