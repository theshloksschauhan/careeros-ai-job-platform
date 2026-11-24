import os
import json
import re
import asyncio
import logging
from typing import Optional, Type
from openai import AsyncOpenAI
from pydantic import ValidationError

from agent_schemas import (
    AgentOutput, AtsScore, CoverLetter, FitAnalysis, InterviewPack, ResumeRewrite, SalaryNegotiation,
)

logger = logging.getLogger(__name__)

# Canned outputs are served only when DEMO_MODE=true, and are flagged demo_mode=True.
DEMO_MODE = os.environ.get("DEMO_MODE", "").strip().lower() in {"1", "true", "yes"}


class LLMUnavailableError(RuntimeError):
    """The LLM provider could not be reached and demo mode is off."""


class LLMOutputError(RuntimeError):
    """The LLM kept returning output that does not match the agent's schema."""

def _get_default_model():
    if "OPENROUTER_API_KEY" in os.environ:
        return "openrouter/free"
    if "GEMINI_API_KEY" in os.environ:
        return "gemini-1.5-flash"
    if "GROQ_API_KEY" in os.environ:
        return "llama-3.3-70b-versatile"
    return "gpt-4o"

MODEL_NAME = os.environ.get("OPENROUTER_MODEL") or os.environ.get("GEMINI_MODEL") or os.environ.get("OPENAI_MODEL") or _get_default_model()

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if "OPENROUTER_API_KEY" in os.environ:
            _client = AsyncOpenAI(
                api_key=os.environ["OPENROUTER_API_KEY"], 
                base_url="https://openrouter.ai/api/v1"
            )
        elif "GEMINI_API_KEY" in os.environ:
            _client = AsyncOpenAI(
                api_key=os.environ["GEMINI_API_KEY"], 
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
        else:
            api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
            base_url = "https://api.groq.com/openai/v1" if "GROQ_API_KEY" in os.environ else None
            _client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    return _client


def _extract_json(text: str):
    """Pull a JSON object out of an LLM response, tolerating code fences/prose."""
    if not text:
        return None
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


async def _run(system_message: str, user_text: str, session_id: str) -> str:
    try:
        client = _get_client()
        resp = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_text},
            ],
            temperature=0.4,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        if not DEMO_MODE:
            raise LLMUnavailableError(f"LLM call failed for {session_id}: {e}") from e
        logger.warning("LLM call failed (%s); DEMO_MODE is on, serving canned output for %s", e, session_id)
        return _demo_output(session_id)


def _demo_output(session_id: str) -> str:
    """Canned demo responses, each marked demo_mode=True so the UI can label them."""
    if session_id.endswith("-fit"):
        return _mark_demo('{"match_rate": 88, "verdict": "Strong fit for the role with excellent relevant experience.", "summary": "The candidate has a solid background matching the core requirements of the job description. While there are minor gaps, the foundational skills make this a competitive application.", "strengths": [{"title": "Relevant Experience", "detail": "Strong track record in the required domain."}], "gaps": [{"title": "Specific Tooling", "detail": "Missing one minor tool mentioned in the JD.", "severity": "low"}], "matched_keywords": ["Leadership", "Management", "Strategy"], "missing_keywords": ["Agile"]}')
    elif session_id.endswith("-ats"):
        return _mark_demo('{"overall_score": 85, "breakdown": [{"category": "Keyword Match", "score": 90, "note": "Excellent use of keywords."}, {"category": "Formatting", "score": 80, "note": "Clean layout."}], "missing_keywords": ["Agile"], "suggestions": ["Add more metrics to your recent role.", "Include the word Agile in your summary."]}')
    elif session_id.endswith("-rewrite"):
        return _mark_demo('{"rewritten_resume": "JOHN DOE\\nExperienced Professional\\n\\n- Spearheaded major initiatives resulting in 20% growth.\\n- Led cross-functional teams to deliver projects ahead of schedule.\\n- Optimized internal processes saving $50k annually.", "changes": [{"section": "Experience", "original": "Did things", "improved": "Spearheaded major initiatives", "reason": "Stronger action verbs"}], "summary_of_changes": "Optimized bullet points for impact and ATS readability."}')
    elif session_id.endswith("-cover"):
        return _mark_demo('{"cover_letter": "Dear Hiring Manager,\\n\\nI am thrilled to apply for this role at your esteemed company. With my extensive background and proven track record of delivering results, I am confident in my ability to bring immediate value to your team. \\n\\nIn my previous roles, I have consistently exceeded expectations and driven growth. I am particularly drawn to your company\'s mission and innovative culture. \\n\\nThank you for considering my application. I look forward to the opportunity to discuss how my skills align with your needs.\\n\\nSincerely,\\nThe Candidate", "hook": "I am thrilled to apply for this role."}')
    elif session_id.endswith("-interview"):
        return _mark_demo('{"questions": [{"question": "Tell me about a time you overcame a challenge.", "category": "Behavioral", "difficulty": "medium", "suggested_answer": "Use the STAR method: describe the Situation, Task, Action, and Result.", "tip": "Be specific about your contribution."}], "focus_areas": ["Leadership", "Problem Solving"]}')
    elif session_id.endswith("-salary"):
        return _mark_demo('{"market_value_estimate": "Highly competitive based on current market rates.", "negotiation_scripts": [{"scenario": "Lowball offer", "script": "I am very excited about the offer, but based on my research and experience, I was hoping for something closer to X."}], "tips": ["Always negotiate", "Focus on total compensation"]}')
    
    return _mark_demo("{}")


def _mark_demo(raw: str) -> str:
    data = json.loads(raw)
    data["demo_mode"] = True
    return json.dumps(data)


def _truncate(text: str, limit: int = 9000) -> str:
    return text[:limit] if text else ""


def _fit_context_text(fit_context: Optional[dict]) -> str:
    if not fit_context:
        return ""
    gaps = fit_context.get("gaps") or []
    missing_keywords = fit_context.get("missing_keywords") or []
    parts = []
    gap_lines = []
    for gap in gaps[:5]:
        if isinstance(gap, dict):
            title = gap.get("title", "Gap")
            detail = gap.get("detail", "")
            gap_lines.append(f"- {title}: {detail}".strip())
    if gap_lines:
        parts.append("Known gaps to address:\n" + "\n".join(gap_lines))
    if missing_keywords:
        parts.append("Prioritize these missing keywords where truthful: " + ", ".join(str(item) for item in missing_keywords[:15]))
    return "\n\n".join(parts)


async def _generate(system: str, user: str, session_id: str, schema: Type[AgentOutput]) -> dict:
    """Call the LLM and validate its JSON against `schema`, retrying once on bad output."""
    raw = await _run(system, user, session_id)
    for attempt in (1, 2):
        data = _extract_json(raw)
        if data is not None:
            try:
                return schema.model_validate(data).model_dump()
            except ValidationError as err:
                problem = f"did not match the schema: {err.errors()[:3]}"
        else:
            problem = "was not valid JSON"
        if attempt == 2:
            raise LLMOutputError(f"{session_id}: output {problem}")
        logger.warning("%s: output %s; retrying once", session_id, problem)
        raw = await _run(
            system,
            f"{user}\n\nYour previous reply {problem}. Reply again with ONLY the JSON object.",
            session_id,
        )


# ----------------- AGENTS -----------------

async def fit_analysis_agent(resume: str, jd: str, app_id: str) -> dict:
    system = (
        "You are an elite career strategist and recruiter. Compare a candidate's resume "
        "against a job description and produce a precise, honest fit analysis. "
        "Respond ONLY with valid JSON matching this schema: "
        '{"match_rate": <int 0-100>, "verdict": "<one short sentence>", '
        '"summary": "<2-3 sentence overview>", '
        '"strengths": [{"title": "<str>", "detail": "<str>"}], '
        '"gaps": [{"title": "<str>", "detail": "<str>", "severity": "low|medium|high"}], '
        '"matched_keywords": ["<str>"], "missing_keywords": ["<str>"]}'
    )
    user = f"JOB DESCRIPTION:\n{_truncate(jd)}\n\nRESUME:\n{_truncate(resume)}"
    return await _generate(system, user, f"{app_id}-fit", FitAnalysis)


async def ats_score_agent(resume: str, jd: str, app_id: str) -> dict:
    system = (
        "You are an ATS (Applicant Tracking System) simulator and resume optimization expert. "
        "Score how well the resume would pass an ATS for the given job. "
        "Respond ONLY with valid JSON matching this schema: "
        '{"overall_score": <int 0-100>, '
        '"breakdown": [{"category": "Keyword Match|Formatting|Relevance|Completeness|Impact", '
        '"score": <int 0-100>, "note": "<short str>"}], '
        '"missing_keywords": ["<str>"], '
        '"suggestions": ["<actionable str>"]}'
    )
    user = f"JOB DESCRIPTION:\n{_truncate(jd)}\n\nRESUME:\n{_truncate(resume)}"
    return await _generate(system, user, f"{app_id}-ats", AtsScore)


async def resume_rewrite_agent(resume: str, jd: str, app_id: str, fit_context: Optional[dict] = None) -> dict:
    system = (
        "You are a world-class resume writer. Rewrite and optimize the candidate's resume to "
        "target the given job description: stronger action verbs, quantified impact, ATS keywords, "
        "and clear structure. Keep it truthful to the original experience. "
        "Respond ONLY with valid JSON matching this schema: "
        '{"rewritten_resume": "<full rewritten resume as clean plain text with line breaks>", '
        '"changes": [{"section": "<str>", "original": "<short excerpt>", '
        '"improved": "<short excerpt>", "reason": "<why>"}], '
        '"summary_of_changes": "<2-3 sentences>"}'
    )
    context_text = _fit_context_text(fit_context)
    user = f"TARGET JOB DESCRIPTION:\n{_truncate(jd)}\n\nORIGINAL RESUME:\n{_truncate(resume)}"
    if context_text:
        user = f"{context_text}\n\n{user}"
    return await _generate(system, user, f"{app_id}-rewrite", ResumeRewrite)


async def cover_letter_agent(resume: str, jd: str, company: str, role: str, app_id: str, fit_context: Optional[dict] = None) -> dict:
    system = (
        "You are a professional cover letter writer. Write a compelling, tailored, modern "
        "cover letter (250-350 words) connecting the candidate's experience to the role. "
        "Confident, specific, no clichés or fluff. "
        "Respond ONLY with valid JSON matching this schema: "
        '{"cover_letter": "<full cover letter text with paragraph breaks>", '
        '"hook": "<the strong opening line>"}'
    )
    context_text = _fit_context_text(fit_context)
    user = (f"ROLE: {role}\nCOMPANY: {company}\n\nJOB DESCRIPTION:\n{_truncate(jd)}\n\n"
            f"CANDIDATE RESUME:\n{_truncate(resume)}")
    if context_text:
        user = f"{context_text}\n\n{user}"
    return await _generate(system, user, f"{app_id}-cover", CoverLetter)


async def interview_pack_agent(resume: str, jd: str, role: str, app_id: str, fit_context: Optional[dict] = None) -> dict:
    system = (
        "You are an expert interview coach. Generate a tailored interview preparation pack for "
        "this candidate and role. Mix behavioral, technical, and role-specific questions. "
        "Respond ONLY with valid JSON matching this schema: "
        '{"questions": [{"question": "<str>", "category": "Behavioral|Technical|Role-specific|Culture", '
        '"difficulty": "easy|medium|hard", "suggested_answer": "<concise model answer using STAR>", '
        '"tip": "<short tip>"}], '
        '"focus_areas": ["<str>"]}'
    )
    context_text = _fit_context_text(fit_context)
    user = f"ROLE: {role}\n\nJOB DESCRIPTION:\n{_truncate(jd)}\n\nCANDIDATE RESUME:\n{_truncate(resume)}"
    if context_text:
        user = f"{context_text}\n\n{user}"
    return await _generate(system, user, f"{app_id}-interview", InterviewPack)


async def salary_negotiation_agent(resume: str, jd: str, role: str, app_id: str, fit_context: Optional[dict] = None) -> dict:
    system = (
        "You are an expert salary negotiation coach. Based on the candidate's resume and the job description, "
        "estimate the market value and provide negotiation scripts for different scenarios (e.g., lowball offer, "
        "asking for more equity/benefits). "
        "Respond ONLY with valid JSON matching this schema: "
        '{"market_value_estimate": "<str>", '
        '"negotiation_scripts": [{"scenario": "<str>", "script": "<str>"}], '
        '"tips": ["<str>"]}'
    )
    context_text = _fit_context_text(fit_context)
    user = f"ROLE: {role}\n\nJOB DESCRIPTION:\n{_truncate(jd)}\n\nCANDIDATE RESUME:\n{_truncate(resume)}"
    if context_text:
        user = f"{context_text}\n\n{user}"
    return await _generate(system, user, f"{app_id}-salary", SalaryNegotiation)


async def run_full_pipeline(resume: str, jd: str, company: str, role: str, app_id: str) -> dict:
    fit = await fit_analysis_agent(resume, jd, app_id)
    context = {"gaps": fit.get("gaps", []), "missing_keywords": fit.get("missing_keywords", [])}
    ats, rewrite, cover, interview, salary = await asyncio.gather(
        ats_score_agent(resume, jd, app_id),
        resume_rewrite_agent(resume, jd, app_id, fit_context=context),
        cover_letter_agent(resume, jd, company, role, app_id, fit_context=context),
        interview_pack_agent(resume, jd, role, app_id, fit_context=context),
        salary_negotiation_agent(resume, jd, role, app_id, fit_context=context),
    )
    return {
        "fit_analysis": fit,
        "ats_score": ats,
        "resume_rewrite": rewrite,
        "cover_letter": cover,
        "interview_pack": interview,
        "salary_negotiation": salary,
    }


AGENT_MAP = {
    "fit_analysis": lambda resume, jd, company, role, app_id, fit_context=None: fit_analysis_agent(resume, jd, app_id),
    "ats_score": lambda resume, jd, company, role, app_id, fit_context=None: ats_score_agent(resume, jd, app_id),
    "resume_rewrite": lambda resume, jd, company, role, app_id, fit_context=None: resume_rewrite_agent(resume, jd, app_id, fit_context=fit_context),
    "cover_letter": lambda resume, jd, company, role, app_id, fit_context=None: cover_letter_agent(resume, jd, company, role, app_id, fit_context=fit_context),
    "interview_pack": lambda resume, jd, company, role, app_id, fit_context=None: interview_pack_agent(resume, jd, role, app_id, fit_context=fit_context),
    "salary_negotiation": lambda resume, jd, company, role, app_id, fit_context=None: salary_negotiation_agent(resume, jd, role, app_id, fit_context=fit_context),
}
