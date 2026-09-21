"""
gmail_monitor.py
------------------
Day 8: background polling monitor that periodically checks Gmail for
new unread emails, skips any already processed, and sends each new
one through the existing LangGraph security agent from Day 7.

Reuses WITHOUT duplication:
  - gmail_auth.get_credentials(), build_gmail_service()   (Day 1)
  - gmail_reader.list_unread_messages(), get_message(),
    extract_email_data()                                    (Day 2)
  - email_agent.run_email_security_agent()                  (Day 7)

READ-ONLY: this file never calls anything that modifies, labels,
deletes, or sends Gmail messages.

LIMITATION (explained further in the Day 8 report): processed message
IDs are kept only in an in-memory Python set. Restarting this script
loses that history, so already-seen emails could be reprocessed after
a restart. That's an accepted limitation for Day 8 - persistent
storage is future work.
"""

import argparse
import sys
import time
from windows_notifier import send_notification
from gmail_auth import get_credentials, build_gmail_service
from gmail_reader import list_unread_messages, get_message, extract_email_data
from email_agent import run_email_security_agent
from report_generator import build_report
# ---------------------------------------------------------------------------
# Configuration - single source of truth, not scattered through the code
# ---------------------------------------------------------------------------

POLL_INTERVAL_SECONDS = 30
MAX_EMAILS_PER_POLL = 5


# ---------------------------------------------------------------------------
# Pure, side-effect-free duplicate-prevention logic.
# Kept separate from Gmail/Gemini calls so it can be unit-tested with no
# network access and no wasted Gemini quota.
# ---------------------------------------------------------------------------
def process_single_email(service, msg_id):
    message = get_message(service, msg_id)
    if message is None:
        raise RuntimeError(f"get_message returned None for {msg_id}")

    email_data = extract_email_data(message)
    result_state = run_email_security_agent(email_data)
    decision = result_state["final_decision"]
    security_analysis = result_state["security_analysis"]
    separator = "=" * 40
    print(f"\n{separator}")
    print("NEW EMAIL ANALYZED")
    print(separator)
    print(f"From: {email_data['sender']}")
    print(f"Subject: {email_data['subject']}")
    print(f"\nClassification: {decision['classification']}")
    print(f"Risk: {decision['risk']}")
    print(f"ML Prediction: {decision['ml_prediction']}")
    print(f"ML Confidence: {decision['ml_confidence']:.2f}%")
    print(f"\nAssessment:\n{decision['assessment']}")
    print(f"\nKey Risk Signals:")
    for signal in decision.get("key_risk_signals", []):
        print(f"  - {signal}")
    print(separator)

    # Day 9: fire a Windows toast with the same result already computed
    # above. No extra Gmail/Gemini calls - this only consumes `decision`.
    report_path = build_report(msg_id, email_data, decision, security_analysis)
    send_notification(email_data["sender"], email_data["subject"], decision, report_path=report_path)
    send_notification(email_data["sender"], email_data["subject"], decision)
def filter_unprocessed(messages, processed_ids):
    """
    Given a list of Gmail message refs (each a dict with an 'id') and a set
    of already-processed message IDs, return only the ones not yet seen.

    This is the entire "duplicate prevention" concept: check the ID against
    a set before doing any real work.
    """
    return [msg for msg in messages if msg["id"] not in processed_ids]


# ---------------------------------------------------------------------------
# One email, one clear responsibility: fetch -> extract -> run agent -> print
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# One polling cycle: get unread mail, skip duplicates, process the rest
# ---------------------------------------------------------------------------

def check_for_new_emails(service, processed_ids, max_results=MAX_EMAILS_PER_POLL):
    """
    Runs ONE polling cycle:
      1. Ask Gmail for unread messages (existing Day 2 function - already
         limits scope to unread mail, not the whole inbox)
      2. Filter out anything already in processed_ids
      3. Process each new one, continuing past any single failure
      4. Mark each successfully-attempted email as processed
    """
    print("Checking Gmail...")
    messages = list_unread_messages(service, max_results=max_results)

    new_messages = filter_unprocessed(messages, processed_ids)

    if not new_messages:
        print("No new emails.")
        return

    print(f"Found {len(new_messages)} new email(s). Processing...")

    for msg_ref in new_messages:
        msg_id = msg_ref["id"]
        try:
            process_single_email(service, msg_id)
        except Exception as exc:
            # One bad email must not kill the monitor - log and continue.
            print(f"Error processing message {msg_id}: {exc}")
        finally:
            # Mark as processed even on failure, so a permanently-broken
            # email (e.g. malformed MIME) doesn't get retried every poll.
            processed_ids.add(msg_id)

    print("Analysis complete.")


# ---------------------------------------------------------------------------
# Entry points: run-once (quota-safe testing) vs. continuous monitor
# ---------------------------------------------------------------------------

def run_once(service):
    """Test mode: check Gmail exactly once, process at most a small batch, then exit."""
    processed_ids = set()
    check_for_new_emails(service, processed_ids, max_results=2)


def run_monitor(service):
    """Continuous mode: poll forever until Ctrl+C."""
    processed_ids = set()
    print(f"Monitor started. Polling every {POLL_INTERVAL_SECONDS} seconds.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            check_for_new_emails(service, processed_ids)
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopping Gmail security agent...")
        print("Monitor stopped.")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Gmail security monitor (Day 8)")
    parser.add_argument(
        "--once", action="store_true",
        help="Process a small batch once and exit, instead of polling continuously."
    )
    args = parser.parse_args()

    creds = get_credentials()
    service = build_gmail_service(creds)

    if args.once:
        run_once(service)
    else:
        run_monitor(service)


if __name__ == "__main__":
    main()