"""
Risk Detection Agent: Analyzes machine operational parameters and retrieved
safety information to identify potential hazards and assign risk levels.
"""

import os
import json
from typing import Dict, Any, List

from llm.groq_client import GroqClient, GroqClientError


def _load_prompt(prompt_file: str) -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "prompts", prompt_file)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _build_user_message(machine_data_formatted: str, context_text: str) -> str:
    return (
        f"{machine_data_formatted}\n\n"
        f"=== RETRIEVED SAFETY CONTEXT ===\n"
        f"{context_text}"
    )


def _fallback_risk_detection(machine_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lightweight rule-based fallback if LLM is unavailable.
    Only uses limits documented in the knowledge base.
    """
    risks = []

    temp = machine_data.get("temperature")
    pressure = machine_data.get("pressure")
    rpm = machine_data.get("rpm")
    guard = str(machine_data.get("safety_guard", "")).upper()
    estop = str(machine_data.get("emergency_stop", "")).upper()

    if guard == "OPEN":
        risks.append({
            "parameter": "safety_guard",
            "observed_value": "OPEN",
            "risk_description": "Safety guard is open during operation.",
            "risk_level": "HIGH",
            "reason": "Retrieved guidelines state: safety guard must be CLOSED during machine operation. An open guard is a HIGH risk condition.",
            "source": "safety_guidelines.txt",
        })

    if estop == "NON-FUNCTIONAL":
        risks.append({
            "parameter": "emergency_stop",
            "observed_value": "NON-FUNCTIONAL",
            "risk_description": "Emergency stop is non-functional.",
            "risk_level": "HIGH",
            "reason": "Retrieved guidelines state: a non-functional emergency stop is a critical safety violation. Machine must not operate.",
            "source": "safety_guidelines.txt",
        })

    if temp is not None:
        try:
            temp_val = float(temp)
            if temp_val > 100:
                risks.append({
                    "parameter": "temperature",
                    "observed_value": f"{temp_val}°C",
                    "risk_description": "Temperature exceeds HIGH risk threshold.",
                    "risk_level": "HIGH",
                    "reason": "Retrieved guidelines state: temperatures exceeding 100°C require immediate shutdown.",
                    "source": "safety_guidelines.txt",
                })
            elif temp_val > 80:
                risks.append({
                    "parameter": "temperature",
                    "observed_value": f"{temp_val}°C",
                    "risk_description": "Temperature in caution range.",
                    "risk_level": "MEDIUM",
                    "reason": "Retrieved guidelines state: temperatures above 80°C trigger a caution alert.",
                    "source": "safety_guidelines.txt",
                })
        except (ValueError, TypeError):
            pass

    if pressure is not None:
        try:
            psi_val = float(pressure)
            if psi_val > 200:
                risks.append({
                    "parameter": "pressure",
                    "observed_value": f"{psi_val} PSI",
                    "risk_description": "Pressure exceeds HIGH risk threshold.",
                    "risk_level": "HIGH",
                    "reason": "Retrieved guidelines state: pressures exceeding 200 PSI represent a HIGH risk condition.",
                    "source": "safety_guidelines.txt",
                })
            elif psi_val > 150:
                risks.append({
                    "parameter": "pressure",
                    "observed_value": f"{psi_val} PSI",
                    "risk_description": "Pressure in caution range.",
                    "risk_level": "MEDIUM",
                    "reason": "Retrieved guidelines state: pressures between 150 and 200 PSI are in the caution zone.",
                    "source": "safety_guidelines.txt",
                })
        except (ValueError, TypeError):
            pass

    if rpm is not None:
        try:
            rpm_val = float(rpm)
            if rpm_val > 4500:
                risks.append({
                    "parameter": "rpm",
                    "observed_value": f"{rpm_val} RPM",
                    "risk_description": "RPM exceeds HIGH risk threshold.",
                    "risk_level": "HIGH",
                    "reason": "Retrieved guidelines state: RPM values exceeding 4500 represent a HIGH risk condition.",
                    "source": "safety_guidelines.txt",
                })
            elif rpm_val > 3500:
                risks.append({
                    "parameter": "rpm",
                    "observed_value": f"{rpm_val} RPM",
                    "risk_description": "RPM in caution range, requires operator review.",
                    "risk_level": "MEDIUM",
                    "reason": "Retrieved guidelines state: RPM values above 3500 require operator review.",
                    "source": "safety_guidelines.txt",
                })
        except (ValueError, TypeError):
            pass

    # Overall risk
    if any(r["risk_level"] == "HIGH" for r in risks):
        overall = "HIGH"
    elif any(r["risk_level"] == "MEDIUM" for r in risks):
        overall = "MEDIUM"
    elif risks:
        overall = "LOW"
    else:
        overall = "LOW"

    summary = (
        f"{len(risks)} risk(s) detected. Overall risk level: {overall}."
        if risks
        else "No risks detected. All evaluated parameters are within normal operating ranges."
    )

    return {
        "risks": risks,
        "overall_risk_level": overall,
        "risk_summary": summary,
        "agent": "Risk Detection Agent",
        "method": "fallback_rule_based",
    }


class RiskDetectionAgent:
    """
    Risk Detection Agent.

    Responsibilities:
    - Analyze machine operational parameters.
    - Analyze retrieved safety information.
    - Identify potentially unsafe conditions.
    - Assign risk levels based on retrieved information.
    """

    def __init__(self, groq_client: GroqClient):
        self.client = groq_client
        self._system_prompt = _load_prompt("risk_detection_prompt.txt")

    def run(self, safety_data_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Risk Detection Agent.

        Args:
            safety_data_output: Output dict from the SafetyDataAgent.

        Returns:
            Dict with detected risks, risk levels, and supporting evidence.
        """
        machine_data = safety_data_output.get("machine_data", {})
        machine_data_formatted = safety_data_output.get("machine_data_formatted", "")
        context_text = safety_data_output.get("full_context_text", "")

        # If no context was retrieved, use fallback
        if not context_text:
            return _fallback_risk_detection(machine_data)

        user_message = _build_user_message(machine_data_formatted, context_text)

        try:
            result = self.client.chat_json(
                system_prompt=self._system_prompt,
                user_message=user_message,
            )
            result["method"] = "llm"
            return result
        except GroqClientError as e:
            # Fallback to rule-based if LLM fails
            fallback = _fallback_risk_detection(machine_data)
            fallback["llm_error"] = str(e)
            return fallback
