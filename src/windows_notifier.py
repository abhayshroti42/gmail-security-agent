"""
windows_notifier.py
----------------------
Windows toast notifications for the email security agent.

Now includes:
  - An emoji indicator (🔴/🟡/🟢) matching the classification, for quick
    visual scanning in the Windows notification area.
  - A `launch` URL (file:// path to that email's HTML report) so clicking
    the toast opens the corresponding Email Security Report.

Import of `winotify` stays lazy so this module remains importable/testable
on non-Windows systems.
"""

import os

APP_ID = "Gmail Security Agent"

_EMOJI = {
    "SPAM": "\U0001F534",        # 🔴
    "SUSPICIOUS": "\U0001F7E1",  # 🟡
    "SAFE": "\U0001F7E2",        # 🟢
}
_DEFAULT_EMOJI = "\u26AA"  # ⚪


def _build_message(sender, subject, decision):
    assessment = decision.get("assessment", "")
    if len(assessment) > 120:
        assessment = assessment[:117] + "..."

    lines = [
        f"From: {sender}",
        f"Subject: {subject}",
        f"Risk: {decision.get('risk', 'UNKNOWN')} | "
        f"ML: {decision.get('ml_prediction', '?')} "
        f"({decision.get('ml_confidence', 0):.1f}%)",
        assessment,
    ]
    return "\n".join(lines)


def send_notification(sender, subject, decision, report_path=None):
    """
    Show a Windows toast notification summarizing one email's security
    analysis. If report_path is given, clicking the toast opens that
    HTML report in the default browser. Never raises - any failure is
    caught and logged so the calling monitor loop keeps running.
    """
    try:
        from winotify import Notification, audio

        classification = decision.get("classification", "UNKNOWN")
        emoji = _EMOJI.get(classification, _DEFAULT_EMOJI)
        title = f"{emoji} Email Security Agent: {classification}"
        message = _build_message(sender, subject, decision)

        launch_url = ""
        if report_path:
            # file:// URI so clicking the toast opens this exact email's
            # report in the default browser.
            launch_url = "file:///" + report_path.replace(os.sep, "/")

        toast = Notification(
            app_id=APP_ID,
            title=title,
            msg=message,
            duration="short",
            launch=launch_url,
        )

        if classification in ("SPAM", "SUSPICIOUS"):
            toast.set_audio(audio.Reminder, loop=False)
        else:
            toast.set_audio(audio.Default, loop=False)

        toast.show()

    except Exception as exc:
        print(f"[WARNING] Failed to show Windows notification: {exc}")