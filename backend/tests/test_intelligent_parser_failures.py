"""How the live parser reports a reply with no events versus a failed call."""

import asyncio

import pytest

from backend.services.intelligent_parser import IntelligentEventParser
from backend.services.parse_errors import ParserUnavailable


class ScriptedParser(IntelligentEventParser):
    """Answers with a fixed reply instead of calling a model."""

    def __init__(self, reply=None, error=None):
        self._setup_common()
        self.model = "scripted"
        self.reply = reply
        self.error = error

    def _call_llm(self, system_prompt, user_prompt, temperature):
        if self.error:
            raise self.error
        return self.reply


def parse(parser, text, **kwargs):
    return asyncio.run(parser.parse(text, "Australia/Sydney", use_cache=False, **kwargs))


def test_no_events_is_an_answer_not_a_failure():
    parser = ScriptedParser(reply='{"events": []}')
    assert parse(parser, "hmm", raise_on_failure=True) == []


def test_an_unreachable_model_raises_when_asked():
    parser = ScriptedParser(error=RuntimeError("credit balance is too low"))
    with pytest.raises(ParserUnavailable):
        parse(parser, "Lunch Friday at 1pm", raise_on_failure=True)


def test_the_harness_still_gets_an_empty_list():
    parser = ScriptedParser(error=RuntimeError("credit balance is too low"))
    assert parse(parser, "Lunch Friday at 1pm") == []
