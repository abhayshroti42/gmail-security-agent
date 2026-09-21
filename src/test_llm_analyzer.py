"""
test_llm_analyzer.py
-----------------------
Standalone test for llm_analyzer.py using hardcoded structured analyses
(the same shape email_analyzer.build_email_analysis() produces).
Does NOT call Gmail or the ML model - only tests the LLM layer.
"""

from llm_analyzer import get_llm_assessment


SAMPLES = [
    # 1. Obvious spam/prize email
    {
        "sender": "Prize Team <promo@bit.ly-rewards.com>",
        "sender_domain": "bit.ly-rewards.com",
        "subject": "Congratulations! You are a WINNER",
        "body_preview": "You have won a free cash prize! Click here immediately...",
        "prediction": "SPAM",
        "confidence": 97.5,
        "risk_level": "HIGH",
        "risk_signals": {
            "suspicious_keywords_found": ["free", "winner", "cash prize", "click here"],
            "urgency_language_found": ["act now"],
            "link_count": 1,
            "suspicious_links": ["http://bit.ly/claim-now"],
        },
    },
    # 2. Suspicious account-verification email
    {
        "sender": "IT Security <security@192.168.1.5.evil-corp.net>",
        "sender_domain": "192.168.1.5.evil-corp.net",
        "subject": "Your account has been suspended",
        "body_preview": "Verify your account immediately or it will be suspended...",
        "prediction": "SPAM",
        "confidence": 61.2,
        "risk_level": "HIGH",
        "risk_signals": {
            "suspicious_keywords_found": ["verify your account", "suspended"],
            "urgency_language_found": ["immediately"],
            "link_count": 1,
            "suspicious_links": ["http://203.0.113.5/login"],
        },
    },
    # 3. Normal work email
    {
        "sender": "Priya Sharma <priya.sharma@company.com>",
        "sender_domain": "company.com",
        "subject": "Meeting notes from today",
        "body_preview": "Hi, attaching notes from today's sync. Let me know if I missed anything.",
        "prediction": "NOT SPAM",
        "confidence": 92.3,
        "risk_level": "LOW",
        "risk_signals": {
            "suspicious_keywords_found": [],
            "urgency_language_found": [],
            "link_count": 0,
            "suspicious_links": [],
        },
    },
    # 4. Ambiguous email
    {
        "sender": "Kaggle <no-reply@kaggle.com>",
        "sender_domain": "kaggle.com",
        "subject": "Your competition submission results are in",
        "body_preview": "Your score has been updated. View your leaderboard position now.",
        "prediction": "SPAM",
        "confidence": 50.15,
        "risk_level": "MEDIUM",
        "risk_signals": {
            "suspicious_keywords_found": [],
            "urgency_language_found": ["now"],
            "link_count": 1,
            "suspicious_links": [],
        },
    },
]


def main():
    for i, analysis in enumerate(SAMPLES, start=1):
        result = get_llm_assessment(analysis)

        print("=" * 40)
        print(f"Sample {i}: {analysis['subject']}")
        print(f"ML prediction: {analysis['prediction']} ({analysis['confidence']:.2f}%) | "
              f"Risk level: {analysis['risk_level']}")
        print(f"LLM recommended classification: {result['recommended_classification']}")
        print(f"LLM assessment: {result['assessment']}")
        print(f"LLM key risk signals: {result['key_risk_signals']}")
        print("=" * 40 + "\n")


if __name__ == "__main__":
    main()