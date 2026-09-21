"""
email_agent.py
---------------
Day 7: LangGraph orchestration of the existing email-security pipeline.

Reuses, without modification:
  - spam_classifier.classify_email()          (Day 3)
  - email_analyzer.build_email_analysis()     (Day 4)
  - llm_analyzer._get_llm(), _extract_text_from_content()  (Day 5)
  - email_tools.py's four @tool functions     (Day 6)

IMPORTANT DISTINCTION THIS FILE DEMONSTRATES:
  The LLM (Gemini) never executes Python. It only ever returns a structured
  "please call this tool with these arguments" request (a tool_call).
  LangGraph's ToolNode is what actually runs the Python function and feeds
  the result back into the conversation.

No node in this file can modify Gmail - all tools operate on data already
fetched by gmail_reader.py, none call the Gmail API.
"""

import json
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from spam_classifier import classify_email
from email_analyzer import build_email_analysis
from llm_analyzer import _get_llm, _extract_text_from_content
from email_tools import (
    analyze_sender_domain,
    extract_links,
    check_suspicious_links,
    get_email_security_analysis,
)

# ---------------------------------------------------------------------------
# Safety limit: prevents an accidental infinite tool-call loop
# ---------------------------------------------------------------------------
MAX_TOOL_ROUNDS = 2

TOOLS = [analyze_sender_domain, extract_links, check_suspicious_links, get_email_security_analysis]


# ---------------------------------------------------------------------------
# State: the single shared dict every node reads from and writes to
# ---------------------------------------------------------------------------

class EmailSecurityState(TypedDict):
    email: dict                                          # {sender, subject, body}
    ml_result: dict                                       # from classify_email()
    security_analysis: dict                                # from build_email_analysis()
    messages: Annotated[List[BaseMessage], add_messages]    # conversation with Gemini
    tool_call_count: int                                    # loop-safety counter
    final_decision: dict                                     # this graph's output


# ---------------------------------------------------------------------------
# Node 1: normalize the raw email input
# ---------------------------------------------------------------------------

def prepare_email(state: EmailSecurityState) -> dict:
    """One job: make sure the email dict has all expected keys, safely."""
    email = state.get("email", {})
    return {
        "email": {
            "sender": email.get("sender", ""),
            "subject": email.get("subject", ""),
            "body": email.get("body", ""),
        }
    }


# ---------------------------------------------------------------------------
# Node 2: run EXISTING ML classifier + Day 4 deterministic analysis
# ---------------------------------------------------------------------------

def initial_analysis(state: EmailSecurityState) -> dict:
    """One job: produce ml_result + security_analysis, and seed the LLM conversation."""
    email = state["email"]

    ml_result = classify_email(email["subject"], email["body"])
    security_analysis = build_email_analysis(email, ml_result)

    system_message = SystemMessage(content=(
        "You are a security assistant investigating one email. An ML spam "
        "classifier and deterministic rule-based signals have ALREADY analyzed "
        "it - treat their output as your primary evidence. You have tools "
        "available if you need more detail (e.g. re-checking links or the "
        "sender domain) before giving your final answer. You have NO ability "
        "to take any action on Gmail - you can only investigate and explain. "
        "Once you are ready to conclude, respond with ONLY valid JSON (no "
        "markdown fences, no extra text) using exactly these keys: "
        "recommended_classification (SAFE, SUSPICIOUS, or SPAM), "
        "assessment (2-3 sentence plain-English explanation), "
        "key_risk_signals (a short list of strings)."
    ))

    signals = security_analysis.get("risk_signals", {})
    human_message = HumanMessage(content=(
        f"Sender: {email['sender']}\n"
        f"Subject: {email['subject']}\n"
        f"Body preview: {security_analysis.get('body_preview', '')}\n\n"
        f"ML classifier prediction: {ml_result['prediction']} "
        f"(confidence: {ml_result['confidence']:.2f}%)\n"
        f"Deterministic risk level: {security_analysis.get('risk_level')}\n"
        f"Suspicious keywords: {signals.get('suspicious_keywords_found', [])}\n"
        f"Urgency language: {signals.get('urgency_language_found', [])}\n"
        f"Suspicious links: {signals.get('suspicious_links', [])}\n\n"
        f"Investigate further with tools if useful, then give your final JSON assessment."
    ))

    return {
        "ml_result": ml_result,
        "security_analysis": security_analysis,
        "messages": [system_message, human_message],
        "tool_call_count": 0,
    }


# ---------------------------------------------------------------------------
# Node 3: call Gemini, with tools bound so it CAN request one (not required to)
# ---------------------------------------------------------------------------

def llm_analysis(state: EmailSecurityState) -> dict:
    """
    One job: ask Gemini to reason over the conversation so far. Gemini may
    respond with plain text/JSON, OR with a request to call a tool - it
    never executes anything itself either way.
    """
    try:
        llm = _get_llm()
        llm_with_tools = llm.bind_tools(TOOLS)
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}
    except Exception as exc:
        # Gemini itself is unreachable (503, network error, etc.) - inject a
        # synthetic AIMessage with no tool_calls so the graph routes straight
        # to finalize, which will report the LLM as unavailable rather than
        # crashing the whole graph. Preserves Day 5's fallback philosophy.
        fallback_json = json.dumps({
            "recommended_classification": "UNAVAILABLE",
            "assessment": f"LLM call failed: {exc}. Falling back to ML + "
                           f"deterministic analysis only.",
            "key_risk_signals": [],
        })
        return {"messages": [AIMessage(content=fallback_json)]}


# ---------------------------------------------------------------------------
# Conditional edge: decide whether to run tools or finish
# ---------------------------------------------------------------------------

def route_after_llm(state: EmailSecurityState) -> str:
    """
    Looks at the LAST message only. If Gemini requested tool call(s) AND
    we haven't hit the safety limit, go execute them. Otherwise, finish.
    """
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None)

    if tool_calls and state.get("tool_call_count", 0) < MAX_TOOL_ROUNDS:
        return "tools"
    return "finalize"


# ---------------------------------------------------------------------------
# Node 4 (after ToolNode): bump the loop-safety counter
# ---------------------------------------------------------------------------

def after_tools(state: EmailSecurityState) -> dict:
    """One job: prevent an accidental infinite tool-calling loop."""
    return {"tool_call_count": state.get("tool_call_count", 0) + 1}


# ---------------------------------------------------------------------------
# Node 5: parse Gemini's final answer, merge with ML + deterministic evidence
# ---------------------------------------------------------------------------

def finalize(state: EmailSecurityState) -> dict:
    """
    One job: produce final_decision. The ML prediction and deterministic
    risk_level are ALWAYS included from state, regardless of what the LLM
    said - the LLM's JSON only supplies the classification/explanation on
    top of that existing evidence, it never silently replaces it.
    """
    last_message = state["messages"][-1]
    ml_result = state["ml_result"]
    security_analysis = state["security_analysis"]

    try:
        raw_text = _extract_text_from_content(last_message.content)
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json", "", 1).strip()
        parsed = json.loads(raw_text)

        recommended_classification = parsed.get("recommended_classification", "SUSPICIOUS")
        assessment = parsed.get("assessment", "(no explanation returned)")
        key_risk_signals = parsed.get("key_risk_signals", [])

    except Exception as exc:
        recommended_classification = "UNAVAILABLE"
        assessment = (f"Could not parse LLM final response ({exc}). "
                      f"Falling back to ML + deterministic analysis only.")
        key_risk_signals = []

    final_decision = {
        "classification": recommended_classification,
        "risk": security_analysis.get("risk_level", "UNKNOWN"),
        "ml_prediction": ml_result.get("prediction"),
        "ml_confidence": ml_result.get("confidence"),
        "assessment": assessment,
        "key_risk_signals": key_risk_signals,
    }
    return {"final_decision": final_decision}


# ---------------------------------------------------------------------------
# Build and compile the graph
# ---------------------------------------------------------------------------

_graph = StateGraph(EmailSecurityState)

_graph.add_node("prepare_email", prepare_email)
_graph.add_node("initial_analysis", initial_analysis)
_graph.add_node("llm_analysis", llm_analysis)
_graph.add_node("tools", ToolNode(TOOLS))
_graph.add_node("after_tools", after_tools)
_graph.add_node("finalize", finalize)

_graph.add_edge(START, "prepare_email")
_graph.add_edge("prepare_email", "initial_analysis")
_graph.add_edge("initial_analysis", "llm_analysis")
_graph.add_conditional_edges(
    "llm_analysis",
    route_after_llm,
    {"tools": "tools", "finalize": "finalize"},
)
_graph.add_edge("tools", "after_tools")
_graph.add_edge("after_tools", "llm_analysis")
_graph.add_edge("finalize", END)

email_security_app = _graph.compile()


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

def run_email_security_agent(email: dict) -> dict:
    """
    Run the full graph on one email dict {sender, subject, body}.
    Returns the final state (includes final_decision, ml_result,
    security_analysis, and the full message history for inspection).
    """
    initial_state = {
        "email": email,
        "ml_result": {},
        "security_analysis": {},
        "messages": [],
        "tool_call_count": 0,
        "final_decision": {},
    }
    return email_security_app.invoke(initial_state)