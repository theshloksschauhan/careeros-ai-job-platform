"""Unit tests for LLM output validation, retry, and demo-mode behaviour."""
import asyncio
import json

import pytest

import llm_agents
from agent_schemas import FitAnalysis


def _scripted_run(replies):
    calls = []

    async def fake_run(system_message, user_text, session_id):
        calls.append(user_text)
        return replies[len(calls) - 1]

    return fake_run, calls


def test_valid_output_is_validated_and_clamped(monkeypatch):
    fake, calls = _scripted_run([json.dumps({"match_rate": 140, "gaps": [{"title": "SQL", "severity": "high"}]})])
    monkeypatch.setattr(llm_agents, "_run", fake)

    result = asyncio.run(llm_agents._generate("sys", "user", "app-fit", FitAnalysis))

    assert result["match_rate"] == 100
    assert result["gaps"][0]["severity"] == "high"
    assert result["demo_mode"] is False
    assert len(calls) == 1


def test_bad_output_is_retried_once(monkeypatch):
    fake, calls = _scripted_run(["Sorry, here you go!", '```json\n{"match_rate": 70}\n```'])
    monkeypatch.setattr(llm_agents, "_run", fake)

    result = asyncio.run(llm_agents._generate("sys", "user", "app-fit", FitAnalysis))

    assert result["match_rate"] == 70
    assert len(calls) == 2
    assert "was not valid JSON" in calls[1]


def test_schema_violation_twice_raises(monkeypatch):
    bad = json.dumps({"gaps": [{"title": "x", "severity": "catastrophic"}]})
    fake, _ = _scripted_run([bad, bad])
    monkeypatch.setattr(llm_agents, "_run", fake)

    with pytest.raises(llm_agents.LLMOutputError):
        asyncio.run(llm_agents._generate("sys", "user", "app-fit", FitAnalysis))


class _FailingClient:
    class chat:
        class completions:
            @staticmethod
            async def create(**kwargs):
                raise ConnectionError("provider down")


def test_provider_failure_raises_without_demo_mode(monkeypatch):
    monkeypatch.setattr(llm_agents, "_get_client", lambda: _FailingClient())
    monkeypatch.setattr(llm_agents, "DEMO_MODE", False)

    with pytest.raises(llm_agents.LLMUnavailableError):
        asyncio.run(llm_agents._run("sys", "user", "app-fit"))


def test_provider_failure_in_demo_mode_is_flagged(monkeypatch):
    monkeypatch.setattr(llm_agents, "_get_client", lambda: _FailingClient())
    monkeypatch.setattr(llm_agents, "DEMO_MODE", True)

    result = asyncio.run(llm_agents.fit_analysis_agent("resume", "jd", "app"))

    assert result["demo_mode"] is True
    assert result["match_rate"] == 88
