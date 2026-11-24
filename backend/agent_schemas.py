"""Pydantic schemas that every LLM agent response is validated against.

Unknown keys are dropped, missing fields fall back to safe defaults, and
0-100 scores are clamped, so the API only ever stores well-formed results.
"""
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, field_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="ignore")


def _clamp_score(value) -> int:
    return max(0, min(100, int(round(float(value)))))


class AgentOutput(_Strict):
    # True only when DEMO_MODE served canned output because the LLM was unreachable.
    demo_mode: bool = False


class Strength(_Strict):
    title: str
    detail: str = ""


class Gap(_Strict):
    title: str
    detail: str = ""
    severity: Literal["low", "medium", "high"] = "medium"


class FitAnalysis(AgentOutput):
    match_rate: int = 0
    verdict: str = ""
    summary: str = ""
    strengths: List[Strength] = []
    gaps: List[Gap] = []
    matched_keywords: List[str] = []
    missing_keywords: List[str] = []

    @field_validator("match_rate", mode="before")
    @classmethod
    def _clamp(cls, value):
        return _clamp_score(value)


class ScoreBreakdown(_Strict):
    category: str
    score: int = 0
    note: str = ""

    @field_validator("score", mode="before")
    @classmethod
    def _clamp(cls, value):
        return _clamp_score(value)


class AtsScore(AgentOutput):
    overall_score: int = 0
    breakdown: List[ScoreBreakdown] = []
    missing_keywords: List[str] = []
    suggestions: List[str] = []

    @field_validator("overall_score", mode="before")
    @classmethod
    def _clamp(cls, value):
        return _clamp_score(value)


class ResumeChange(_Strict):
    section: str = ""
    original: str = ""
    improved: str = ""
    reason: str = ""


class ResumeRewrite(AgentOutput):
    rewritten_resume: str = ""
    changes: List[ResumeChange] = []
    summary_of_changes: str = ""


class CoverLetter(AgentOutput):
    cover_letter: str = ""
    hook: str = ""


class InterviewQuestion(_Strict):
    question: str
    category: str = "Role-specific"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    suggested_answer: str = ""
    tip: str = ""


class InterviewPack(AgentOutput):
    questions: List[InterviewQuestion] = []
    focus_areas: List[str] = []


class NegotiationScript(_Strict):
    scenario: str
    script: str


class SalaryNegotiation(AgentOutput):
    market_value_estimate: str = "Unknown"
    negotiation_scripts: List[NegotiationScript] = []
    tips: List[str] = []
