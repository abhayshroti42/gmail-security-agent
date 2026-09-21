"""
test_gmail_monitor.py
------------------------
Tests the duplicate-prevention and error-handling logic in gmail_monitor.py
WITHOUT calling Gmail or Gemini - everything Gmail/Gemini-related is mocked,
so this test costs zero API quota and needs no network access.

Test E (graceful Ctrl+C shutdown) is NOT automated here - see the note
at the bottom of this file for why, and how to verify it manually.
"""

import unittest
from unittest.mock import patch, MagicMock

from gmail_monitor import filter_unprocessed, check_for_new_emails


class TestFilterUnprocessed(unittest.TestCase):
    """Pure logic tests - no mocking needed, this function has no side effects."""

    def test_a_new_email_is_kept(self):
        messages = [{"id": "A"}]
        processed = set()
        result = filter_unprocessed(messages, processed)
        self.assertEqual(result, [{"id": "A"}])

    def test_b_duplicate_is_skipped(self):
        messages = [{"id": "A"}]
        processed = {"A"}
        result = filter_unprocessed(messages, processed)
        self.assertEqual(result, [])

    def test_c_new_plus_old_only_new_kept(self):
        messages = [{"id": "A"}, {"id": "B"}]
        processed = {"A"}
        result = filter_unprocessed(messages, processed)
        self.assertEqual(result, [{"id": "B"}])


class TestCheckForNewEmails(unittest.TestCase):
    """
    Tests the full polling-cycle function with Gmail/Gemini mocked out,
    including Test D: one failing email must not stop the others.
    """

    @patch("gmail_monitor.process_single_email")
    @patch("gmail_monitor.list_unread_messages")
    def test_d_one_failure_does_not_stop_others(self, mock_list, mock_process):
        mock_list.return_value = [{"id": "A"}, {"id": "B"}, {"id": "C"}]

        def side_effect(service, msg_id):
            if msg_id == "B":
                raise ValueError("simulated processing failure")
            return None  # A and C succeed silently

        mock_process.side_effect = side_effect

        processed_ids = set()
        fake_service = MagicMock()

        # Should not raise, despite B failing
        check_for_new_emails(fake_service, processed_ids, max_results=3)

        # All three should be marked processed (A, C succeeded; B failed but
        # is still marked so a permanently-broken email isn't retried forever)
        self.assertEqual(processed_ids, {"A", "B", "C"})
        self.assertEqual(mock_process.call_count, 3)

    @patch("gmail_monitor.process_single_email")
    @patch("gmail_monitor.list_unread_messages")
    def test_second_poll_skips_already_processed(self, mock_list, mock_process):
        # First poll: A and B arrive
        mock_list.return_value = [{"id": "A"}, {"id": "B"}]
        processed_ids = set()
        fake_service = MagicMock()

        check_for_new_emails(fake_service, processed_ids, max_results=5)
        self.assertEqual(mock_process.call_count, 2)

        # Second poll: A, B, C arrive - only C is new
        mock_list.return_value = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
        check_for_new_emails(fake_service, processed_ids, max_results=5)

        # Only ONE additional call should have happened (for C)
        self.assertEqual(mock_process.call_count, 3)
        self.assertEqual(processed_ids, {"A", "B", "C"})


if __name__ == "__main__":
    unittest.main()

# ---------------------------------------------------------------------------
# Test E - graceful shutdown (Ctrl+C) is NOT automated in this file.
# Simulating a real KeyboardInterrupt mid-loop reliably in a unit test is
# fragile and low-value compared to just trying it. To verify manually:
#
#   python src\gmail_monitor.py
#   (wait for at least one "Checking Gmail..." line, then press Ctrl+C)
#
# Expected output: "Stopping Gmail security agent..." then "Monitor stopped."
# with no raw traceback.
# ---------------------------------------------------------------------------