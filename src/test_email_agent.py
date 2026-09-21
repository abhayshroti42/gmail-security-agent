"""
test_email_agent.py
----------------------
Standalone test for the Day 7 LangGraph agent. No Gmail calls - runs the
full graph against hardcoded sample emails and prints the final decision
plus a look at how many tool round-trips actually happened.
"""

from langchain_core.messages import AIMessage, ToolMessage

from email_agent import run_email_security_agent


SAMPLES = [
    {
        "label": "Prize scam",
        "sender": "Prize Team <promo@bit.ly-rewards.com>",
        "subject": "Congratulations! You are a WINNER",
        "body": "You have won a free cash prize! Click here immediately: "
                "http://bit.ly/claim-now before it expires. Act now!",
    },
    {
        "label": "Phishing/security scam",
        "sender": "IT Security <security@192.168.1.5.evil-corp.net>",
        "subject": "Your account has been suspended",
        "body": "Verify your account immediately or it will be suspended. "
                "Login here: http://203.0.113.5/login",
    },
    {
        "label": "Normal business email",
        "sender": "Priya Sharma <priya.sharma@company.com>",
        "subject": "Meeting notes",
        "body": "Hi, attaching notes from today's sync. Let me know if I missed anything.",
    },
    {
        "label": "LinkedIn-style legitimate email",
        "sender": "LinkedIn <jobs-noreply@linkedin.com>",
        "subject": "New jobs matching your profile",
        "body": "Check out these new job postings: https://linkedin.com/jobs/view/12345",
    },
]


def describe_tool_activity(messages):
    """Walk the message history and report which tools were called, if any."""
    calls = []
    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for call in msg.tool_calls:
                calls.append(call["name"])
    return calls


def main():
    for sample in SAMPLES:
        print("=" * 40)
        print(sample["label"])
        print("-" * 40)

        try:
            result_state = run_email_security_agent({
                "sender": sample["sender"],
                "subject": sample["subject"],
                "body": sample["body"],
            })

            decision = result_state["final_decision"]
            tools_called = describe_tool_activity(result_state["messages"])

            print(f"ML prediction: {decision['ml_prediction']} ({decision['ml_confidence']:.2f}%)")
            print(f"Deterministic risk: {decision['risk']}")
            print(f"Final classification: {decision['classification']}")
            print(f"Assessment: {decision['assessment']}")
            print(f"Key risk signals: {decision['key_risk_signals']}")
            print(f"Tools called during this run: {tools_called or 'none'}")
            print(f"Tool rounds used: {result_state['tool_call_count']} / limit 2")

        except Exception as exc:
            print(f"[TEST ERROR] Graph run failed entirely: {exc}")

        print("=" * 40 + "\n")


if __name__ == "__main__":
    main()