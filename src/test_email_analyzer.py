"""
test_email_analyzer.py
------------------------
Standalone test for email_analyzer.py using hardcoded sample data.
Does NOT call Gmail or the ML model - lets you verify the analysis layer
in isolation, fast.
"""

from email_analyzer import build_email_analysis


SAMPLES = [
    (
        {
            "sender": "Prize Team <promo@bit.ly-rewards.com>",
            "subject": "Congratulations! You are a WINNER",
            "date": "Wed, 16 Sep 2026 10:00:00 +0530",
            "body": "You have won a free cash prize! Click here immediately: "
                    "http://bit.ly/claim-now before it expires. Act now!",
        },
        {"prediction": "SPAM", "confidence": 97.5},
    ),
    (
        {
            "sender": "IT Security <security@192.168.1.5.evil-corp.net>",
            "subject": "Your account has been suspended",
            "date": "Wed, 16 Sep 2026 10:05:00 +0530",
            "body": "Verify your account immediately or it will be suspended. "
                    "Login here: http://203.0.113.5/login",
        },
        {"prediction": "SPAM", "confidence": 61.2},
    ),
    (
        {
            "sender": "Priya Sharma <priya.sharma@company.com>",
            "subject": "Meeting notes from today",
            "date": "Wed, 16 Sep 2026 14:00:00 +0530",
            "body": "Hi, attaching notes from today's sync. Let me know if I missed anything.",
        },
        {"prediction": "NOT SPAM", "confidence": 92.3},
    ),
    (
        {
            "sender": "LinkedIn <jobs-noreply@linkedin.com>",
            "subject": "New jobs matching your profile",
            "date": "Wed, 16 Sep 2026 08:00:00 +0530",
            "body": "Check out these new job postings: https://linkedin.com/jobs/view/12345",
        },
        {"prediction": "NOT SPAM", "confidence": 84.9},
    ),
]


def main():
    for i, (email_data, classification_result) in enumerate(SAMPLES, start=1):
        analysis = build_email_analysis(email_data, classification_result)

        print("=" * 40)
        print(f"Sample {i}")
        print(f"Sender: {analysis['sender']}  (domain: {analysis['sender_domain']})")
        print(f"Subject: {analysis['subject']}")
        print(f"Prediction: {analysis['prediction']}  ({analysis['confidence']:.2f}%)")
        print(f"Risk level: {analysis['risk_level']}")
        print(f"Suspicious keywords: {analysis['risk_signals']['suspicious_keywords_found']}")
        print(f"Urgency language: {analysis['risk_signals']['urgency_language_found']}")
        print(f"Links found: {analysis['risk_signals']['link_count']} "
              f"(suspicious: {analysis['risk_signals']['suspicious_links']})")
        print("=" * 40 + "\n")


if __name__ == "__main__":
    main()