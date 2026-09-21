"""
email_analyzer.py
------------------
Takes raw Gmail email data + the ML spam classifier's result and combines
them into one structured analysis dict.

This layer adds ONLY deterministic, rule-based signals (keyword matching,
regex link detection) - no LLM, no external calls, no Gmail actions.

IMPORTANT: These signals are heuristics, not proof. A "suspicious keyword"
match does not mean an email IS malicious - it means it shares surface
patterns with common spam/phishing wording, worth a closer look.
"""

import re


# ---------------------------------------------------------------------------
# Deterministic signal definitions
# ---------------------------------------------------------------------------

# Common wording seen in spam/phishing - NOT proof of anything on its own
SUSPICIOUS_KEYWORDS = [
    "free", "winner", "congratulations", "claim your prize", "click here",
    "verify your account", "suspended", "password", "act now", "limited time",
    "risk-free", "guaranteed", "no cost", "cash prize", "you have won",
]

URGENCY_PHRASES = [
    "urgent", "immediately", "act now", "expires", "expiring",
    "within 24 hours", "verify now", "final notice", "last chance",
]

# Known shorteners - hide the real destination, common in phishing
SUSPICIOUS_LINK_DOMAINS = [
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly",
]

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
IP_IN_URL_PATTERN = re.compile(r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
EMAIL_ADDRESS_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+")


# ---------------------------------------------------------------------------
# Individual signal detectors (each one small and independently testable)
# ---------------------------------------------------------------------------

def find_suspicious_keywords(text: str) -> list:
    """Return which known suspicious phrases appear in the text (case-insensitive)."""
    text_lower = text.lower()
    return [kw for kw in SUSPICIOUS_KEYWORDS if kw in text_lower]


def find_urgency_language(text: str) -> list:
    """Return which urgency-style phrases appear in the text."""
    text_lower = text.lower()
    return [phrase for phrase in URGENCY_PHRASES if phrase in text_lower]


def extract_urls(text: str) -> list:
    """Find all http(s) URLs in the text using a simple regex."""
    return URL_PATTERN.findall(text)


def flag_suspicious_links(urls: list) -> list:
    """
    Flag URLs that match simple suspicious patterns:
      - known link-shortening services (hide the real destination)
      - raw IP addresses instead of a domain name
    This is NOT a real-time malicious-URL check - just cheap pattern matching.
    """
    flagged = []
    for url in urls:
        is_shortener = any(domain in url for domain in SUSPICIOUS_LINK_DOMAINS)
        is_ip_based = bool(IP_IN_URL_PATTERN.match(url))
        if is_shortener or is_ip_based:
            flagged.append(url)
    return flagged


def extract_sender_domain(sender: str) -> str:
    """
    Pull the domain out of a "From" header, which may look like:
      "Some Name <person@example.com>"  or  "person@example.com"
    Returns "(unknown)" if no email address pattern is found.
    """
    match = EMAIL_ADDRESS_PATTERN.search(sender or "")
    if not match:
        return "(unknown)"
    address = match.group(0)
    return address.split("@")[-1].lower()


# ---------------------------------------------------------------------------
# Risk level: a simple, explainable combination of ML + heuristic signals
# ---------------------------------------------------------------------------

def determine_risk_level(prediction: str, confidence: float, signal_count: int) -> str:
    """
    Combine the ML verdict with how many rule-based signals fired into one
    simple LOW / MEDIUM / HIGH label.

    This is intentionally simple and transparent (not a second ML model):
      - HIGH: ML says SPAM with high confidence, or SPAM + supporting signals
      - MEDIUM: ML is uncertain, or NOT SPAM but multiple suspicious signals present
      - LOW: NOT SPAM with few/no suspicious signals

    This is a risk indicator, not a verdict of malicious intent.
    """
    if prediction == "SPAM" and confidence >= 80:
        return "HIGH"
    if prediction == "SPAM":
        return "MEDIUM" if signal_count == 0 else "HIGH"
    # prediction == NOT SPAM
    if signal_count >= 2:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Main entry point: build one structured analysis result
# ---------------------------------------------------------------------------

def build_email_analysis(email_data: dict, classification_result: dict) -> dict:
    """
    Combine Gmail email data + ML classification into one structured dict.

    Args:
        email_data: {"sender", "subject", "date", "body"} from extract_email_data()
        classification_result: {"prediction", "confidence"} from classify_email()

    Returns:
        dict: structured analysis result (see fields below)
    """
    subject = email_data.get("subject", "") or ""
    body = email_data.get("body", "") or ""
    sender = email_data.get("sender", "") or ""
    combined_text = f"{subject} {body}"

    keywords_found = find_suspicious_keywords(combined_text)
    urgency_found = find_urgency_language(combined_text)
    urls = extract_urls(body)
    suspicious_links = flag_suspicious_links(urls)

    signal_count = sum([
        1 if keywords_found else 0,
        1 if urgency_found else 0,
        1 if suspicious_links else 0,
    ])

    prediction = classification_result.get("prediction", "NOT SPAM")
    confidence = classification_result.get("confidence", 0.0)

    return {
        "sender": sender,
        "sender_domain": extract_sender_domain(sender),
        "subject": subject,
        # Body is truncated here - this structured result may later get logged
        # or passed to an LLM prompt, so we avoid carrying huge raw bodies around.
        "body_preview": body[:200] + ("..." if len(body) > 200 else ""),
        "prediction": prediction,
        "confidence": confidence,
        "risk_signals": {
            "suspicious_keywords_found": keywords_found,
            "urgency_language_found": urgency_found,
            "link_count": len(urls),
            "suspicious_links": suspicious_links,
        },
        "risk_level": determine_risk_level(prediction, confidence, signal_count),
    }