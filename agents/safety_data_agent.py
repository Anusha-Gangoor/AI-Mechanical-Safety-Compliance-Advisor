"""
Safety Data Agent: Receives machine operational data, retrieves relevant safety
information using RAG, and prepares context for downstream agents.
"""

import os
import json
from typing import Dict, Any, Optional

from llm.groq_client import GroqClient, GroqClientError
from rag.retriever import Retriever, RetrievedContext


def _load_prompt(prompt_file: str) -> str:
    """Load a prompt from the prompts directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "prompts", prompt_file)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _build_machine_query(machine_data: Dict[str, Any]) -> str:
    """Build a RAG query string from machine data."""
    parts = [
        f"machine type: {machine_data.get('machine_type', 'unknown')}",
        f"operating condition: {machine_data.get('operating_condition', 'unknown')}",
    ]

    # Add numeric parameters
    if machine_data.get("temperature") not in (None, ""):
        parts.append(f"temperature {machine_data['temperature']} degrees celsius")
    if machine_data.get("pressure") not in (None, ""):
        parts.append(f"pressure {machine_data['pressure']} PSI")
    if machine_data.get("rpm") not in (None, ""):
        parts.append(f"RPM {machine_data['rpm']}")

    # Add safety device states
    guard = machine_data.get("safety_guard", "")
    if guard:
        parts.append(f"safety guard {guard}")
        if guard.upper() == "OPEN":
            parts.append("open safety guard risk compliance")
    estop = machine_data.get("emergency_stop", "")
    if estop:
        parts.append(f"emergency stop {estop}")
        if estop.upper() == "NON-FUNCTIONAL":
            parts.append("non-functional emergency stop critical risk")

    return " ".join(parts)


def _format_machine_data_for_llm(machine_data: Dict[str, Any]) -> str:
    """Format machine data as a readable string for the LLM."""
    lines = [
        "=== MACHINE OPERATIONAL DATA ===",
        f"Machine ID: {machine_data.get('machine_id', 'N/A')}",
        f"Machine Type: {machine_data.get('machine_type', 'N/A')}",
        f"Temperature: {machine_data.get('temperature', 'NOT PROVIDED')}°C",
        f"Pressure: {machine_data.get('pressure', 'NOT PROVIDED')} PSI",
        f"RPM: {machine_data.get('rpm', 'NOT PROVIDED')}",
        f"Safety Guard Status: {machine_data.get('safety_guard', 'NOT PROVIDED')}",
        f"Emergency Stop Status: {machine_data.get('emergency_stop', 'NOT PROVIDED')}",
        f"Operating Condition: {machine_data.get('operating_condition', 'NOT PROVIDED')}",
        f"Additional Notes: {machine_data.get('notes', 'None')}",
    ]
    return "\n".join(lines)


class SafetyDataAgent:
    """
    Safety Data Agent.

    Responsibilities:
    - Receive machine operational data.
    - Build a RAG query from the machine data.
    - Retrieve relevant safety context from the knowledge base.
    - Use the LLM to summarize what is relevant.
    - Return structured output for downstream agents.
    """

    def __init__(self, groq_client: GroqClient, retriever: Retriever):
        self.client = groq_client
        self.retriever = retriever
        self._system_prompt = _load_prompt("safety_data_prompt.txt")

    def run(self, machine_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Safety Data Agent.

        Args:
            machine_data: Dict with keys: machine_id, machine_type, temperature,
                          pressure, rpm, safety_guard, emergency_stop,
                          operating_condition, notes.

        Returns:
            Dict with agent output + retrieved context for downstream agents.
        """
        # Step 1: Build RAG query and retrieve context
        query = _build_machine_query(machine_data)
        retrieved: RetrievedContext = self.retriever.retrieve(query, top_k=6)

        if retrieved.is_empty:
            return {
                "agent": "Safety Data Agent",
                "status": "INSUFFICIENT EVIDENCE",
                "error": "No relevant safety information found in the knowledge base.",
                "retrieved_context": None,
                "sources": [],
                "machine_data": machine_data,
                "machine_data_formatted": _format_machine_data_for_llm(machine_data),
            }

        # Step 2: Prepare LLM input
        machine_str = _format_machine_data_for_llm(machine_data)
        user_message = (
            f"{machine_str}\n\n"
            f"=== RETRIEVED SAFETY CONTEXT ===\n"
            f"{retrieved.context_text}"
        )

        # Step 3: Call LLM
        try:
            result = self.client.chat_json(
                system_prompt=self._system_prompt,
                user_message=user_message,
            )
        except GroqClientError as e:
            return {
                "agent": "Safety Data Agent",
                "status": "ERROR",
                "error": str(e),
                "retrieved_context": retrieved,
                "sources": retrieved.sources,
                "machine_data": machine_data,
                "machine_data_formatted": machine_str,
            }

        # Step 4: Attach the full retrieved context for downstream agents
        result["retrieved_context"] = retrieved
        result["machine_data"] = machine_data
        result["machine_data_formatted"] = machine_str
        result["full_context_text"] = retrieved.context_text
        result["status"] = "OK"
        return result
