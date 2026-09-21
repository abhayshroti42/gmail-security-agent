"""
test_email_tools.py
---------------------
Standalone test for email_tools.py. No Gmail calls, no LLM calls -
proves each tool executes correctly and reuses existing Day 4 logic.

Also includes an OPTIONAL demonstration of how an LLM would be shown
these tools (via bind_tools) and would choose which one(s) to call -
without actually letting it execute anything. This is NOT the Day 7
agent - just a look at tool-selection in isolation.
"""

from email_tools import (
    analyze_sender_domain,
    extract_links,
    check_suspicious_links,
    get_email_security_analysis,
)

SAMPLES = [
    {
        "label": "Suspicious prize/scam email",
        "sender": "Prize Team <promo@bit.ly-rewards.com>",
        "subject": "Congratulations! You are a WINNER",
        "body": "You have won a free cash prize! Click here immediately: "
                "http://bit.ly/claim-now before it expires. Act now!",
        "ml_prediction": "SPAM",
        "ml_confidence": 97.5,
    },
    {
        "label": "Account-security/phishing email",
        "sender": "IT Security <security@192.168.1.5.evil-corp.net>",
        "subject": "Your account has been suspended",
        "body": "Verify your account immediately or it will be suspended. "
                "Login here: http://203.0.113.5/login",
        "ml_prediction": "SPAM",
        "ml_confidence": 61.2,
    },
    {
        "label": "Normal business email",
        "sender": "Priya Sharma <priya.sharma@company.com>",
        "subject": "Meeting notes from today",
        "body": "Hi, attaching notes from today's sync. Let me know if I missed anything.",
        "ml_prediction": "NOT SPAM",
        "ml_confidence": 92.3,
    },
    {
        "label": "Email containing a legitimate link",
        "sender": "LinkedIn <jobs-noreply@linkedin.com>",
        "subject": "New jobs matching your profile",
        "body": "Check out these new job postings: https://linkedin.com/jobs/view/12345",
        "ml_prediction": "NOT SPAM",
        "ml_confidence": 84.9,
    },
]


def run_tools_directly():
    """
    Demonstrates calling LangChain Tools the way normal code calls them:
    via .invoke(dict_of_args) - not agent-driven, just proving each tool
    works and returns structured, predictable output.
    """
    for sample in SAMPLES:
        print("=" * 40)
        print(sample["label"])
        print("-" * 40)

        domain_info = analyze_sender_domain.invoke({"sender": sample["sender"]})
        print(f"analyze_sender_domain -> {domain_info}")

        links = extract_links.invoke({"email_body": sample["body"]})
        print(f"extract_links -> {links}")

        suspicious = check_suspicious_links.invoke({"links": links})
        print(f"check_suspicious_links -> {suspicious}")

        analysis = get_email_security_analysis.invoke({
            "sender": sample["sender"],
            "subject": sample["subject"],
            "body": sample["body"],
            "ml_prediction": sample["ml_prediction"],
            "ml_confidence": sample["ml_confidence"],
        })
        print(f"get_email_security_analysis -> risk_level: {analysis['risk_level']}, "
              f"prediction: {analysis['prediction']}")
        print("=" * 40 + "\n")


def demonstrate_llm_tool_selection():
    """
    OPTIONAL: shows an LLM being given the tool DEFINITIONS (name +
    description + schema) and asked what it would call - without actually
    executing anything. This is tool-CALLING (the model deciding), not
    tool EXECUTION (which still happens in your own code, as above).

    This is intentionally NOT an agent loop - no LangGraph, no automatic
    execution of what the model chooses. Just observing model.tool_calls.
    """
    try:
        from llm_analyzer import _get_llm  # reuse Day 5's loaded Gemini instance

        llm = _get_llm()
        llm_with_tools = llm.bind_tools([
            analyze_sender_domain, extract_links, check_suspicious_links,
            get_email_security_analysis,
        ])

        sample = SAMPLES[0]
        prompt = (
            f"An email arrived from '{sample['sender']}' with body: "
            f"'{sample['body']}'. Which tool(s) would you call to investigate it, "
            f"and with what arguments?"
        )
        response = llm_with_tools.invoke(prompt)

        print("=" * 40)
        print("LLM tool-selection demonstration (NOT executed)")
        print("-" * 40)
        if response.tool_calls:
            for call in response.tool_calls:
                print(f"Model chose tool: {call['name']}")
                print(f"  with arguments: {call['args']}")
        else:
            print("Model did not choose to call any tool for this prompt.")
        print("=" * 40)

    except Exception as exc:
        print(f"[INFO] Skipping LLM tool-selection demo ({exc}). "
              f"This is optional and does not affect Day 6 pass/fail.")


if __name__ == "__main__":
    run_tools_directly()
    demonstrate_llm_tool_selection()