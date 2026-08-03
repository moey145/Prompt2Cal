"""
Claude-based event parser.

Reuses the entire prompt-building, post-processing, recurrence-normalization
and validation pipeline from ``IntelligentEventParser`` and swaps only the raw
LLM call so the GPT and Claude extractors are directly comparable in the
research benchmark.
"""

import json
import logging
import re

import anthropic

from .intelligent_parser import IntelligentEventParser

logger = logging.getLogger(__name__)

DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 2000


class ClaudeEventParser(IntelligentEventParser):
    """Event parser backed by Anthropic's Claude models.

    Inherits all parsing logic from :class:`IntelligentEventParser`; only the
    provider client and the raw ``_call_llm`` request are overridden.
    """

    def __init__(self, api_key: str, model: str = DEFAULT_CLAUDE_MODEL):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self._setup_common()

    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        # Claude has no native JSON response-format flag, so we instruct it in
        # the system prompt and defensively strip any markdown fences.
        system = (
            system_prompt
            + "\n\nIMPORTANT: Respond with a single valid JSON object only. "
            "Do not wrap it in markdown code fences or add any commentary."
        )

        message = self.client.messages.create(
            model=self.model,
            max_tokens=CLAUDE_MAX_TOKENS,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = message.content[0].text if message.content else ""
        return self._extract_json(text)

    @staticmethod
    def _extract_json(text: str) -> str:
        """Return the JSON substring from a model response.

        Handles the common cases where Claude wraps output in ```json fences or
        adds leading/trailing prose despite instructions.
        """
        if not text:
            return "{}"

        stripped = text.strip()

        # Remove ```json ... ``` or ``` ... ``` fences if present.
        fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
        if fence_match:
            return fence_match.group(1).strip()

        # Otherwise, slice from the first '{' to the last '}'.
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return stripped[start : end + 1]

        return stripped
