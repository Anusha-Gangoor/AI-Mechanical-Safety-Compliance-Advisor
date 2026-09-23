"""
Safety Recommendation Agent: Generates corrective safety recommendations
based on detected risks, compliance findings, and retrieved safety information.
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


DISCLAIMER = (
    "This is a prototype for educational and demonstration purposes. "
    "It does not replace qualified safety professionals, official standards, "
    "inspections, or regulatory compliance procedures."
)


def _fallback_recommendations(
    risk_output: Dict[str, Any],
    compliance_output: Dict[str, Any],
    machine_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Rule-based fallback when LLM is unavailable."""
    recommendations = []
    overall_action = "NO ACTION REQUIRED"

    risks = risk_output.get("risks", [])
    findings = compliance_output.get("compliance_findings", [])
    overall_risk = risk_output.get("overall_risk_level", "LOW")
    overall_compliance = compliance_output.get("overall_status", "COMPLIANT")

    # Process non-compliant findings
    for finding in findings:
        if finding["status"] == "NON-COMPLIANT":
            param = finding["parameter"].lower()

            if "guard" in param:
                recommendations.append({
                    "issue": f"Safety guard is NON-COMPLIANT: {finding['observed_value']}",
                    "action": "Stop machine immediately. Verify safety guard is properly installed and secured before restarting. Test interlock functionality. Do not operate machine with open safety guard.",
                    "priority": "IMMEDIATE",
                    "basis": "Retrieved guidelines state machine must not be operated with open safety guard.",
                    "source": finding.get("source", "safety_guidelines.txt"),
                })
                overall_action = "STOP MACHINE"

            elif "stop" in param:
                recommendations.append({
                    "issue": f"Emergency stop is NON-COMPLIANT: {finding['observed_value']}",
                    "action": "Isolate machine power immediately. Tag machine as OUT OF SERVICE. Have qualified technician repair and retest emergency stop. Do not operate until emergency stop is functional.",
                    "priority": "IMMEDIATE",
                    "basis": "Retrieved guidelines state machines must not operate with non-functional emergency stop.",
                    "source": finding.get("source", "safety_guidelines.txt"),
                })
                overall_action = "STOP MACHINE"

            elif "temperature" in param:
                recommendations.append({
                    "issue": f"Temperature is NON-COMPLIANT: {finding['observed_value']}",
                    "action": "Reduce machine load and check cooling system operation. If temperature exceeds 100°C, initiate immediate shutdown. Investigate root cause before restart.",
                    "priority": "IMMEDIATE" if overall_risk == "HIGH" else "SHORT-TERM",
                    "basis": "Retrieved guidelines define normal temperature range as 20°C to 80°C.",
                    "source": finding.get("source", "safety_guidelines.txt"),
                })
                if overall_action == "NO ACTION REQUIRED":
                    overall_action = "STOP MACHINE" if overall_risk == "HIGH" else "CAUTION REVIEW"

            elif "pressure" in param:
                recommendations.append({
                    "issue": f"Pressure is NON-COMPLIANT: {finding['observed_value']}",
                    "action": "Verify pressure relief valve operation. Reduce process input. If pressure exceeds 200 PSI, initiate immediate shutdown. Depressurize safely before any maintenance.",
                    "priority": "IMMEDIATE" if overall_risk == "HIGH" else "SHORT-TERM",
                    "basis": "Retrieved guidelines define normal pressure range as 0 to 150 PSI.",
                    "source": finding.get("source", "safety_guidelines.txt"),
                })
                if overall_action == "NO ACTION REQUIRED":
                    overall_action = "STOP MACHINE" if overall_risk == "HIGH" else "CAUTION REVIEW"

            elif "rpm" in param:
                recommendations.append({
                    "issue": f"RPM is NON-COMPLIANT: {finding['observed_value']}",
                    "action": "Reduce machine load. Check speed control system. If RPM exceeds 4500, activate emergency stop. Allow machine to come to complete rest before inspecting drive components.",
                    "priority": "IMMEDIATE" if overall_risk == "HIGH" else "SHORT-TERM",
                    "basis": "Retrieved guidelines define normal RPM range as 0 to 3500 RPM.",
                    "source": finding.get("source", "safety_guidelines.txt"),
                })
                if overall_action == "NO ACTION REQUIRED":
                    overall_action = "STOP MACHINE" if overall_risk == "HIGH" else "CAUTION REVIEW"

    # Handle insufficient evidence
    insuff_params = [f["parameter"] for f in findings if f["status"] == "INSUFFICIENT EVIDENCE"]
    if insuff_params:
        recommendations.append({
            "issue": f"Missing data for: {', '.join(insuff_params)}",
            "action": "Collect complete operational data for all missing parameters before resuming machine operation. Have qualified safety personnel assess the machine.",
            "priority": "SHORT-TERM",
            "basis": "Compliance cannot be determined without complete parameter data.",
            "source": "safety_guidelines.txt",
        })
        if overall_action == "NO ACTION REQUIRED":
            overall_action = "CAUTION REVIEW"

    # If no recommendations, add a positive finding
    if not recommendations:
        recommendations.append({
            "issue": "No immediate safety issues detected.",
            "action": "Continue normal operation. Maintain scheduled inspection and maintenance routines per operating procedures.",
            "priority": "SCHEDULED",
            "basis": "All evaluated parameters are within retrieved safety guidelines.",
            "source": "safety_guidelines.txt",
        })

    risk_desc = f"Overall risk: {overall_risk}. " if overall_risk else ""
    compliance_desc = f"Overall compliance: {overall_compliance}."
    summary = (
        f"{len(recommendations)} recommendation(s) generated. "
        f"{risk_desc}{compliance_desc} "
        f"Required action: {overall_action}."
    )

    return {
        "recommendations": recommendations,
        "overall_action_required": overall_action,
        "summary": summary,
        "disclaimer": DISCLAIMER,
        "agent": "Safety Recommendation Agent",
        "method": "fallback_rule_based",
    }


class RecommendationAgent:
    """
    Safety Recommendation Agent.

    Responsibilities:
    - Analyze detected risks and compliance findings.
    - Use retrieved safety information.
    - Generate corrective recommendations with priority levels.
    """

    def __init__(self, groq_client: GroqClient):
        self.client = groq_client
        self._system_prompt = _load_prompt("recommendation_prompt.txt")

    def run(
        self,
        safety_data_output: Dict[str, Any],
        risk_output: Dict[str, Any],
        compliance_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the Safety Recommendation Agent.

        Args:
            safety_data_output: Output from SafetyDataAgent.
            risk_output: Output from RiskDetectionAgent.
            compliance_output: Output from ComplianceAgent.

        Returns:
            Dict with recommendations, priorities, and action summary.
        """
        machine_data = safety_data_output.get("machine_data", {})
        machine_data_formatted = safety_data_output.get("machine_data_formatted", "")
        context_text = safety_data_output.get("full_context_text", "")

        if not context_text:
            return _fallback_recommendations(risk_output, compliance_output, machine_data)

        # Build rich user message with all agent outputs
        risk_summary = json.dumps(risk_output, indent=2, default=str)
        compliance_summary = json.dumps(compliance_output, indent=2, default=str)

        user_message = (
            f"{machine_data_formatted}\n\n"
            f"=== RISK DETECTION AGENT OUTPUT ===\n{risk_summary}\n\n"
            f"=== COMPLIANCE AGENT OUTPUT ===\n{compliance_summary}\n\n"
            f"=== RETRIEVED SAFETY CONTEXT ===\n{context_text}"
        )

        try:
            result = self.client.chat_json(
                system_prompt=self._system_prompt,
                user_message=user_message,
            )
            # Ensure disclaimer is always present
            result.setdefault("disclaimer", DISCLAIMER)
            result["method"] = "llm"
            return result
        except GroqClientError as e:
            fallback = _fallback_recommendations(risk_output, compliance_output, machine_data)
            fallback["llm_error"] = str(e)
            return fallback
