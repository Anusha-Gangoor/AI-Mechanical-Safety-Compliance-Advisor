"""
Compliance Agent: Compares machine operating conditions against retrieved
safety requirements and determines compliance status.
"""

import os
from typing import Dict, Any, List

from llm.groq_client import GroqClient, GroqClientError


def _load_prompt(prompt_file: str) -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "prompts", prompt_file)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _fallback_compliance_check(machine_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rule-based compliance fallback when LLM is unavailable.
    Based on limits documented in the knowledge base.
    """
    findings = []
    overall = "COMPLIANT"

    temp = machine_data.get("temperature")
    pressure = machine_data.get("pressure")
    rpm = machine_data.get("rpm")
    guard = str(machine_data.get("safety_guard", "")).upper()
    estop = str(machine_data.get("emergency_stop", "")).upper()

    # Safety guard
    if guard in ("OPEN", "MISSING", "REMOVED"):
        findings.append({
            "parameter": "Safety Guard",
            "observed_value": guard,
            "required_condition": "Safety guard must be CLOSED during machine operation.",
            "status": "NON-COMPLIANT",
            "reason": "Retrieved guidelines require safety guard to be CLOSED. Found: OPEN.",
            "source": "safety_guidelines.txt",
        })
        overall = "NON-COMPLIANT"
    elif guard in ("CLOSED", "SECURED"):
        findings.append({
            "parameter": "Safety Guard",
            "observed_value": guard,
            "required_condition": "Safety guard must be CLOSED during machine operation.",
            "status": "COMPLIANT",
            "reason": "Safety guard is CLOSED, satisfying the retrieved requirement.",
            "source": "safety_guidelines.txt",
        })
    elif guard in ("", "UNKNOWN", "NOT PROVIDED"):
        findings.append({
            "parameter": "Safety Guard",
            "observed_value": "NOT PROVIDED",
            "required_condition": "Safety guard status must be confirmed.",
            "status": "INSUFFICIENT EVIDENCE",
            "reason": "Safety guard status was not provided. Cannot determine compliance.",
            "source": "safety_guidelines.txt",
        })
        if overall == "COMPLIANT":
            overall = "INSUFFICIENT EVIDENCE"

    # Emergency stop
    if estop == "NON-FUNCTIONAL":
        findings.append({
            "parameter": "Emergency Stop",
            "observed_value": "NON-FUNCTIONAL",
            "required_condition": "Emergency stop must be FUNCTIONAL at all times.",
            "status": "NON-COMPLIANT",
            "reason": "Retrieved guidelines state a non-functional emergency stop is a critical safety violation.",
            "source": "safety_guidelines.txt",
        })
        overall = "NON-COMPLIANT"
    elif estop == "FUNCTIONAL":
        findings.append({
            "parameter": "Emergency Stop",
            "observed_value": "FUNCTIONAL",
            "required_condition": "Emergency stop must be FUNCTIONAL at all times.",
            "status": "COMPLIANT",
            "reason": "Emergency stop is FUNCTIONAL, satisfying the retrieved requirement.",
            "source": "safety_guidelines.txt",
        })
    elif estop in ("", "UNKNOWN", "NOT PROVIDED"):
        findings.append({
            "parameter": "Emergency Stop",
            "observed_value": "NOT PROVIDED",
            "required_condition": "Emergency stop functionality must be confirmed.",
            "status": "INSUFFICIENT EVIDENCE",
            "reason": "Emergency stop status was not provided.",
            "source": "safety_guidelines.txt",
        })
        if overall == "COMPLIANT":
            overall = "INSUFFICIENT EVIDENCE"

    # Temperature
    if temp not in (None, ""):
        try:
            temp_val = float(temp)
            if temp_val > 100:
                findings.append({
                    "parameter": "Temperature",
                    "observed_value": f"{temp_val}°C",
                    "required_condition": "Temperature must not exceed 100°C.",
                    "status": "NON-COMPLIANT",
                    "reason": f"{temp_val}°C exceeds the HIGH risk threshold of 100°C per retrieved guidelines.",
                    "source": "safety_guidelines.txt",
                })
                overall = "NON-COMPLIANT"
            elif temp_val > 80:
                findings.append({
                    "parameter": "Temperature",
                    "observed_value": f"{temp_val}°C",
                    "required_condition": "Normal operating temperature: 20°C to 80°C.",
                    "status": "NON-COMPLIANT",
                    "reason": f"{temp_val}°C is in the caution range (81°C-100°C) per retrieved guidelines.",
                    "source": "safety_guidelines.txt",
                })
                overall = "NON-COMPLIANT"
            else:
                findings.append({
                    "parameter": "Temperature",
                    "observed_value": f"{temp_val}°C",
                    "required_condition": "Normal operating temperature: 20°C to 80°C.",
                    "status": "COMPLIANT",
                    "reason": f"{temp_val}°C is within the normal operating range per retrieved guidelines.",
                    "source": "safety_guidelines.txt",
                })
        except (ValueError, TypeError):
            findings.append({
                "parameter": "Temperature",
                "observed_value": str(temp),
                "required_condition": "Valid numeric temperature reading required.",
                "status": "INSUFFICIENT EVIDENCE",
                "reason": "Temperature value could not be evaluated.",
                "source": "safety_guidelines.txt",
            })
    else:
        findings.append({
            "parameter": "Temperature",
            "observed_value": "NOT PROVIDED",
            "required_condition": "Temperature must be within normal operating range.",
            "status": "INSUFFICIENT EVIDENCE",
            "reason": "Temperature data was not provided.",
            "source": "safety_guidelines.txt",
        })
        if overall == "COMPLIANT":
            overall = "INSUFFICIENT EVIDENCE"

    # Pressure
    if pressure not in (None, ""):
        try:
            psi_val = float(pressure)
            if psi_val > 200:
                findings.append({
                    "parameter": "Pressure",
                    "observed_value": f"{psi_val} PSI",
                    "required_condition": "Pressure must not exceed 200 PSI.",
                    "status": "NON-COMPLIANT",
                    "reason": f"{psi_val} PSI exceeds the HIGH risk threshold of 200 PSI per retrieved guidelines.",
                    "source": "safety_guidelines.txt",
                })
                overall = "NON-COMPLIANT"
            elif psi_val > 150:
                findings.append({
                    "parameter": "Pressure",
                    "observed_value": f"{psi_val} PSI",
                    "required_condition": "Normal operating pressure: 0 to 150 PSI.",
                    "status": "NON-COMPLIANT",
                    "reason": f"{psi_val} PSI is in the caution range (151-200 PSI) per retrieved guidelines.",
                    "source": "safety_guidelines.txt",
                })
                overall = "NON-COMPLIANT"
            else:
                findings.append({
                    "parameter": "Pressure",
                    "observed_value": f"{psi_val} PSI",
                    "required_condition": "Normal operating pressure: 0 to 150 PSI.",
                    "status": "COMPLIANT",
                    "reason": f"{psi_val} PSI is within the normal operating range per retrieved guidelines.",
                    "source": "safety_guidelines.txt",
                })
        except (ValueError, TypeError):
            findings.append({
                "parameter": "Pressure",
                "observed_value": str(pressure),
                "required_condition": "Valid numeric pressure reading required.",
                "status": "INSUFFICIENT EVIDENCE",
                "reason": "Pressure value could not be evaluated.",
                "source": "safety_guidelines.txt",
            })
    else:
        findings.append({
            "parameter": "Pressure",
            "observed_value": "NOT PROVIDED",
            "required_condition": "Pressure must be within normal operating range.",
            "status": "INSUFFICIENT EVIDENCE",
            "reason": "Pressure data was not provided.",
            "source": "safety_guidelines.txt",
        })
        if overall == "COMPLIANT":
            overall = "INSUFFICIENT EVIDENCE"

    # RPM
    if rpm not in (None, ""):
        try:
            rpm_val = float(rpm)
            if rpm_val > 4500:
                findings.append({
                    "parameter": "RPM",
                    "observed_value": f"{rpm_val} RPM",
                    "required_condition": "RPM must not exceed 4500 RPM.",
                    "status": "NON-COMPLIANT",
                    "reason": f"{rpm_val} RPM exceeds the HIGH risk threshold of 4500 RPM per retrieved guidelines.",
                    "source": "safety_guidelines.txt",
                })
                overall = "NON-COMPLIANT"
            elif rpm_val > 3500:
                findings.append({
                    "parameter": "RPM",
                    "observed_value": f"{rpm_val} RPM",
                    "required_condition": "Normal RPM range: 0 to 3500 RPM.",
                    "status": "NON-COMPLIANT",
                    "reason": f"{rpm_val} RPM is in the caution range (3501-4500) per retrieved guidelines.",
                    "source": "safety_guidelines.txt",
                })
                overall = "NON-COMPLIANT"
            else:
                findings.append({
                    "parameter": "RPM",
                    "observed_value": f"{rpm_val} RPM",
                    "required_condition": "Normal RPM range: 0 to 3500 RPM.",
                    "status": "COMPLIANT",
                    "reason": f"{rpm_val} RPM is within the normal operating range per retrieved guidelines.",
                    "source": "safety_guidelines.txt",
                })
        except (ValueError, TypeError):
            findings.append({
                "parameter": "RPM",
                "observed_value": str(rpm),
                "required_condition": "Valid numeric RPM reading required.",
                "status": "INSUFFICIENT EVIDENCE",
                "reason": "RPM value could not be evaluated.",
                "source": "safety_guidelines.txt",
            })
    else:
        findings.append({
            "parameter": "RPM",
            "observed_value": "NOT PROVIDED",
            "required_condition": "RPM must be within normal operating range.",
            "status": "INSUFFICIENT EVIDENCE",
            "reason": "RPM data was not provided.",
            "source": "safety_guidelines.txt",
        })
        if overall == "COMPLIANT":
            overall = "INSUFFICIENT EVIDENCE"

    non_compliant_count = sum(1 for f in findings if f["status"] == "NON-COMPLIANT")
    compliant_count = sum(1 for f in findings if f["status"] == "COMPLIANT")
    insuff_count = sum(1 for f in findings if f["status"] == "INSUFFICIENT EVIDENCE")

    summary = (
        f"Compliance check completed. {non_compliant_count} NON-COMPLIANT finding(s), "
        f"{compliant_count} COMPLIANT finding(s), {insuff_count} with INSUFFICIENT EVIDENCE. "
        f"Overall status: {overall}."
    )

    return {
        "compliance_findings": findings,
        "overall_status": overall,
        "compliance_summary": summary,
        "agent": "Compliance Agent",
        "method": "fallback_rule_based",
    }


class ComplianceAgent:
    """
    Compliance Agent.

    Responsibilities:
    - Compare machine operating conditions with retrieved safety requirements.
    - Determine compliance status for each parameter.
    - Reference supporting source documents.
    """

    def __init__(self, groq_client: GroqClient):
        self.client = groq_client
        self._system_prompt = _load_prompt("compliance_prompt.txt")

    def run(self, safety_data_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Compliance Agent.

        Args:
            safety_data_output: Output dict from the SafetyDataAgent.

        Returns:
            Dict with compliance findings, overall status, and explanations.
        """
        machine_data = safety_data_output.get("machine_data", {})
        machine_data_formatted = safety_data_output.get("machine_data_formatted", "")
        context_text = safety_data_output.get("full_context_text", "")

        # If no context retrieved, use fallback
        if not context_text:
            return _fallback_compliance_check(machine_data)

        user_message = (
            f"{machine_data_formatted}\n\n"
            f"=== RETRIEVED SAFETY CONTEXT ===\n"
            f"{context_text}"
        )

        try:
            result = self.client.chat_json(
                system_prompt=self._system_prompt,
                user_message=user_message,
            )
            result["method"] = "llm"
            return result
        except GroqClientError as e:
            fallback = _fallback_compliance_check(machine_data)
            fallback["llm_error"] = str(e)
            return fallback
