"""
test_windows_notifier.py
---------------------------
Tests windows_notifier.py without needing a real Windows toast to appear,
so this costs no Gmail/Gemini calls and runs on any OS.

_build_message() is pure and tested directly.
send_notification() is tested by injecting a FAKE winotify module into
sys.modules before calling it, so the calling logic (title/sound selection,
show() being invoked, exceptions being swallowed) is verified without a
real `winotify` install.
"""

import sys
import unittest
from unittest.mock import MagicMock

from windows_notifier import _build_message, send_notification


class TestBuildMessage(unittest.TestCase):

    def test_includes_sender_subject_and_risk(self):
        decision = {
            "risk": "HIGH", "ml_prediction": "SPAM", "ml_confidence": 97.5,
            "assessment": "Looks like a prize scam.",
        }
        message = _build_message("scammer@example.com", "You won!", decision)
        self.assertIn("scammer@example.com", message)
        self.assertIn("You won!", message)
        self.assertIn("HIGH", message)
        self.assertIn("SPAM", message)
        self.assertIn("Looks like a prize scam.", message)

    def test_truncates_long_assessment(self):
        decision = {
            "risk": "LOW", "ml_prediction": "NOT SPAM", "ml_confidence": 90.0,
            "assessment": "x" * 200,
        }
        message = _build_message("a@b.com", "Subject", decision)
        self.assertIn("...", message)
        self.assertLess(len(message), 300)


class TestSendNotification(unittest.TestCase):

    def setUp(self):
        # Inject a fake winotify module so the lazy `from winotify import
        # Notification, audio` inside send_notification() succeeds even
        # though the real package isn't usable on this machine.
        self.fake_winotify = MagicMock()
        self.mock_toast = MagicMock()
        self.fake_winotify.Notification.return_value = self.mock_toast
        sys.modules["winotify"] = self.fake_winotify

    def tearDown(self):
        del sys.modules["winotify"]

    def test_spam_uses_reminder_sound_and_shows(self):
        decision = {
            "classification": "SPAM", "risk": "HIGH",
            "ml_prediction": "SPAM", "ml_confidence": 97.5,
            "assessment": "Prize scam pattern detected.",
        }
        send_notification("scammer@example.com", "You won!", decision)

        self.fake_winotify.Notification.assert_called_once()
        self.mock_toast.set_audio.assert_called_once_with(
            self.fake_winotify.audio.Reminder, loop=False
        )
        self.mock_toast.show.assert_called_once()

    def test_safe_uses_default_sound(self):
        decision = {
            "classification": "SAFE", "risk": "LOW",
            "ml_prediction": "NOT SPAM", "ml_confidence": 91.0,
            "assessment": "Looks fine.",
        }
        send_notification("a@b.com", "Hello", decision)

        self.mock_toast.set_audio.assert_called_once_with(
            self.fake_winotify.audio.Default, loop=False
        )

    def test_notification_failure_does_not_raise(self):
        self.fake_winotify.Notification.side_effect = RuntimeError("simulated toast failure")

        decision = {
            "classification": "SAFE", "risk": "LOW",
            "ml_prediction": "NOT SPAM", "ml_confidence": 91.0,
            "assessment": "Looks fine.",
        }
        try:
            send_notification("a@b.com", "Hello", decision)  # must not raise
        except Exception:
            self.fail("send_notification() raised despite internal try/except")
    def test_report_path_becomes_file_uri_launch(self):
        decision = {"classification": "SPAM", "risk": "HIGH", "ml_prediction": "SPAM",
                    "ml_confidence": 97.5, "assessment": "Prize scam pattern detected."}
        send_notification("a@b.com", "Hi", decision, report_path="C:\\Users\\DELL\\reports\\abc123.html")

        called_kwargs = self.fake_winotify.Notification.call_args.kwargs
        self.assertEqual(called_kwargs["launch"], "file:///C:/Users/DELL/reports/abc123.html")

if __name__ == "__main__":
    unittest.main()