"""
classify_inbox.py
------------------
Day 4: fetches unread Gmail messages, classifies each with the ML model,
then builds a structured analysis (ML result + deterministic risk signals)
via email_analyzer.py.

READ-ONLY: does not modify, label, or mark any Gmail message.
"""

from gmail_auth import get_credentials, build_gmail_service
from gmail_reader import list_unread_messages, get_message, extract_email_data
from spam_classifier import classify_email
from email_analyzer import build_email_analysis


def main():
    creds = get_credentials()
    service = build_gmail_service(creds)

    messages = list_unread_messages(service, max_results=5)

    if not messages:
        print("No unread emails found.")
        return

    for index, msg_ref in enumerate(messages, start=1):
        message = get_message(service, msg_ref["id"])
        if message is None:
            continue

        email_data = extract_email_data(message)
        classification_result = classify_email(email_data["subject"], email_data["body"])
        analysis = build_email_analysis(email_data, classification_result)

        separator = "=" * 40
        print(f"\n{separator}")
        print(f"Email {index}")
        print(f"From: {analysis['sender']}  (domain: {analysis['sender_domain']})")
        print(f"Subject: {analysis['subject']}")
        print(f"Prediction: {analysis['prediction']}  ({analysis['confidence']:.2f}%)")
        print(f"Risk level: {analysis['risk_level']}")
        signals = analysis["risk_signals"]
        if signals["suspicious_keywords_found"]:
            print(f"  Suspicious keywords: {signals['suspicious_keywords_found']}")
        if signals["urgency_language_found"]:
            print(f"  Urgency language: {signals['urgency_language_found']}")
        if signals["suspicious_links"]:
            print(f"  Suspicious links: {signals['suspicious_links']}")
        print(separator)


if __name__ == "__main__":
    main()