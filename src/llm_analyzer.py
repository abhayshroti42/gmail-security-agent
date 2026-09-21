"""
llm_analyzer.py
----------------
Adds an LLM-based explanation/assessment layer on top of the existing
ML classifier + deterministic email_analyzer.py output.

IMPORTANT: The LLM does NOT replace or silently override the ML prediction.
It receives the ML result and deterministic signals as EVIDENCE and is
explicitly instructed to reason from them, not contradict them casually.
Its output is an ASSESSMENT/EXPLANATION - not ground truth, and it has
no ability to take any Gmail action.
"""

import os
import json

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()  # reads GOOGLE_API_KEY from .env into the environment

def _extract_text_from_content(content) -> str:
    """
    response.content from ChatGoogleGenerativeAI can be:
      - a plain string (older/simpler responses), OR
      - a list of content blocks, where each block is either a string
        or a dict containing a "text" key (newer Gemini models can return
        multi-part responses, e.g. separate reasoning/text parts).

    This normalizes any of those shapes into one plain string.
    """
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                text_parts.append(block["text"])
        return "".join(text_parts).strip()

    # Unexpected shape - fail loudly here so it's caught by the existing
    # try/except in get_llm_assessment() and reported as UNAVAILABLE,
    # rather than silently returning something wrong.
    raise TypeError(f"Unexpected response.content type: {type(content)}")
# ---------------------------------------------------------------------------
# LLM setup - loaded once, reused across calls (same "load once" principle
# as the ML model in spam_classifier.py)
# ---------------------------------------------------------------------------

_LLM = None  # lazily initialized so a missing API key doesn't crash imports


def _get_llm():
    global _LLM
    if _LLM is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY not found. Add it to your .env file. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        _LLM = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0)
    return _LLM


# ---------------------------------------------------------------------------
# The controlled prompt
# ---------------------------------------------------------------------------
# This is the entire "control surface" for the LLM - it only ever sees the
# structured analysis we hand it, never raw Gmail access, never any tool
# that could take an action. It is asked to explain and assess, not decide.

_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a security assistant that explains email risk assessments in "
     "plain English for a human reviewer. You are NOT the final authority - "
     "an ML spam classifier and deterministic rule-based signals have ALREADY "
     "analyzed this email; treat their output as your primary evidence. "
     "Do not contradict strong ML/signal evidence without clearly explaining why. "
     "You have no ability to take any action on this email - you only explain "
     "and recommend. "
     "Respond ONLY with valid JSON, no markdown formatting, no extra text, "
     "using exactly these keys: "
     "recommended_classification (one of: SAFE, SUSPICIOUS, SPAM), "
     "assessment (a 2-3 sentence plain-English explanation), "
     "key_risk_signals (a short list of strings naming the most important signals)."
    ),
    ("human",
     "Sender: {sender}\n"
     "Sender domain: {sender_domain}\n"
     "Subject: {subject}\n"
     "Body preview: {body_preview}\n\n"
     "ML classifier prediction: {ml_prediction} (confidence: {ml_confidence:.2f}%)\n"
     "Deterministic risk level: {risk_level}\n"
     "Suspicious keywords found: {suspicious_keywords}\n"
     "Urgency language found: {urgency_language}\n"
     "Suspicious links found: {suspicious_links}\n\n"
     "Provide your assessment as JSON."
    ),
])


# ---------------------------------------------------------------------------
# Public function: run the LLM analysis
# ---------------------------------------------------------------------------

def get_llm_assessment(structured_analysis: dict) -> dict:
    """
    Send a structured email analysis (from email_analyzer.build_email_analysis)
    to the LLM and return its assessment.

    Args:
        structured_analysis: the dict produced by build_email_analysis()

    Returns:
        dict: {
            "recommended_classification": "SAFE" | "SUSPICIOUS" | "SPAM" | "UNAVAILABLE",
            "assessment": str,
            "key_risk_signals": list[str],
        }
        On any failure (missing key, network error, bad response), returns a
        graceful fallback instead of raising - the rest of the pipeline (ML
        prediction + deterministic risk level) still works without the LLM.
    """
    signals = structured_analysis.get("risk_signals", {})

    try:
        llm = _get_llm()
        chain = _PROMPT | llm

        response = chain.invoke({
            "sender": structured_analysis.get("sender", ""),
            "sender_domain": structured_analysis.get("sender_domain", ""),
            "subject": structured_analysis.get("subject", ""),
            "body_preview": structured_analysis.get("body_preview", ""),
            "ml_prediction": structured_analysis.get("prediction", ""),
            "ml_confidence": structured_analysis.get("confidence", 0.0),
            "risk_level": structured_analysis.get("risk_level", ""),
            "suspicious_keywords": signals.get("suspicious_keywords_found", []),
            "urgency_language": signals.get("urgency_language_found", []),
            "suspicious_links": signals.get("suspicious_links", []),
        })

        raw_text = _extract_text_from_content(response.content)
        # Gemini sometimes wraps JSON in ```json fences despite instructions -
        # strip them defensively rather than assuming perfect compliance.
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            raw_text = raw_text.replace("json", "", 1).strip()

        parsed = json.loads(raw_text)

        return {
            "recommended_classification": parsed.get("recommended_classification", "SUSPICIOUS"),
            "assessment": parsed.get("assessment", "(no explanation returned)"),
            "key_risk_signals": parsed.get("key_risk_signals", []),
        }

    except Exception as exc:
        # Graceful degradation: the pipeline must still work if the LLM is
        # down, the API key is missing, or the response wasn't valid JSON.
        return {
            "recommended_classification": "UNAVAILABLE",
            "assessment": f"LLM assessment unavailable ({exc}). Falling back to "
                           f"ML prediction and deterministic risk level only.",
            "key_risk_signals": [],
        }