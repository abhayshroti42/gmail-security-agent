"""
email_tools.py
--------------
LangChain Tool wrappers around the existing deterministic email-security
functions already defined in email_analyzer.py.

KEY DISTINCTION THIS FILE DEMONSTRATES:
- email_analyzer.py's functions are plain Python functions: you call them
  directly, by name, with arguments YOU choose in your own code.
- The @tool-wrapped versions below are LangChain Tools: named, described
  capabilities that an LLM/agent can choose to invoke by name, deciding
  the arguments itself at runtime based on a prompt - not hardcoded by you.

No tool here can modify Gmail. These tools only operate on data already
fetched by gmail_reader.py - none of them call the Gmail API.
"""

import re

from langchain_core.tools import tool

from email_analyzer import (
    extract_urls,
    flag_suspicious_links,
    extract_sender_domain,
    build_email_analysis,
)

# Small additional deterministic check, specific to this tool only -
# doesn't belong in email_analyzer.py since nothing else there uses it.
_IP_DOMAIN_PATTERN = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


@tool
def analyze_sender_domain(sender: str) -> dict:
    """
    Extract and evaluate the domain of an email sender for basic red flags.
    Input is the raw 'From' header value, e.g. "Name <person@example.com>".
    Performs NO external network requests, DNS lookups, or WHOIS calls -
    purely offline string pattern checks on the domain text itself.
    """
    domain = extract_sender_domain(sender)
    is_ip_based = bool(_IP_DOMAIN_PATTERN.match(domain))
    return {
        "domain": domain,
        "is_ip_based": is_ip_based,
        "subdomain_count": domain.count(".") if domain != "(unknown)" else 0,
    }


@tool
def extract_links(email_body: str) -> list[str]:
    """
    Extract all http(s) URLs found in an email body using the existing
    regex-based extractor. Returns an empty list if none are found.
    Does not fetch, follow, or validate the URLs in any way.
    """
    return extract_urls(email_body)


@tool
def check_suspicious_links(links: list[str]) -> list[str]:
    """
    Given a list of URLs (e.g. from extract_links), return the subset that
    match known suspicious patterns: link-shortening services or raw
    IP-address-based URLs. Pattern matching only, not a live safety check
    or reputation lookup.
    """
    return flag_suspicious_links(links)


@tool
def get_email_security_analysis(
    sender: str,
    subject: str,
    body: str,
    ml_prediction: str,
    ml_confidence: float,
) -> dict:
    """
    Run the full existing deterministic security analysis (Day 4 logic)
    on an email, combined with an already-computed ML classifier result.
    Returns the same structured dict used elsewhere in the project:
    sender/domain, suspicious keywords, urgency language, link findings,
    ML prediction/confidence, and an overall LOW/MEDIUM/HIGH risk level.
    """
    email_data = {"sender": sender, "subject": subject, "body": body}
    classification_result = {"prediction": ml_prediction, "confidence": ml_confidence}
    return build_email_analysis(email_data, classification_result)