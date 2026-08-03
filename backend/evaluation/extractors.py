from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

from backend.services.claude_parser import ClaudeEventParser
from backend.services.intelligent_parser import IntelligentEventParser
from backend.services.rules_parser import parse_with_rules

from .models import EvalEvent
from .normalize import parsed_event_to_eval_event, rule_event_to_eval_event

load_dotenv()


class RegexExtractor:
    """Rules-based extractor for benchmark evaluation (single event per input)."""

    def extract(self, text: str, timezone: str) -> List[EvalEvent]:
        rule_events = parse_with_rules(text, timezone)
        if not rule_events:
            return []
        return [rule_event_to_eval_event(rule_events[0], timezone)]


class LLMExtractor:
    """LLM-based extractor for benchmark evaluation.

    ``provider`` selects the backing model:
      - ``"openai"`` (default): GPT via :class:`IntelligentEventParser`
      - ``"claude"``: Claude via :class:`ClaudeEventParser`
    """

    def __init__(
        self,
        api_key: str | None = None,
        provider: str = "openai",
        model: str | None = None,
    ):
        self.provider = provider

        if provider == "claude":
            key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is required for Claude extraction runs."
                )
            self.parser = (
                ClaudeEventParser(key, model=model)
                if model
                else ClaudeEventParser(key)
            )
        else:
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise RuntimeError("OPENAI_API_KEY is required for LLM extraction runs.")
            self.parser = IntelligentEventParser(key)
            if model:
                self.parser.model = model

    async def extract(
        self,
        text: str,
        timezone: str,
        *,
        use_cache: bool = False,
        temperature: float = 0.0,
    ) -> List[EvalEvent]:
        parsed_events = await self.parser.parse(
            text,
            timezone,
            use_cache=use_cache,
            temperature=temperature,
        )
        return [parsed_event_to_eval_event(event, timezone) for event in parsed_events]
