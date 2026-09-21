"""
gmail_reader.py
---------------
Reads unread Gmail messages using the existing OAuth authentication from
gmail_auth.py. This module is READ-ONLY: it never marks messages as read,
labels them, moves them, or deletes them.

Reuses:
  - get_credentials()      from gmail_auth.py
  - build_gmail_service()  from gmail_auth.py
"""

import base64
import sys

from googleapiclient.errors import HttpError

from gmail_auth import get_credentials, build_gmail_service


# ---------------------------------------------------------------------------
# Step 1: List unread messages (IDs only — no content yet)
# ---------------------------------------------------------------------------

def list_unread_messages(service, max_results=5):
    """
    Search the mailbox for unread messages using Gmail's query syntax.

    This call is intentionally lightweight — it returns only message IDs
    and thread IDs, not subject/body/sender. Fetching full content for
    every match up front would be wasteful if you're just browsing results.

    Args:
        service: Authenticated Gmail v1 service resource.
        max_results: Maximum number of unread messages to retrieve.

    Returns:
        list[dict]: Each dict has 'id' and 'threadId'. Empty list if none found.
    """
    try:
        response = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=max_results)
            .execute()
        )
        return response.get("messages", [])
    except HttpError as http_err:
        print(
            f"[ERROR] Failed to list unread messages.\n"
            f"  Status : {http_err.status_code}\n"
            f"  Reason : {http_err.reason}",
            file=sys.stderr,
        )
        return []


# ---------------------------------------------------------------------------
# Step 2: Fetch full content for one message ID
# ---------------------------------------------------------------------------

def get_message(service, msg_id):
    """
    Retrieve the full message resource (headers + MIME payload + body)
    for a single message ID.

    Args:
        service: Authenticated Gmail v1 service resource.
        msg_id: The Gmail message ID to fetch.

    Returns:
        dict | None: The full message resource, or None on failure.
    """
    try:
        return (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
    except HttpError as http_err:
        print(
            f"[ERROR] Failed to fetch message {msg_id}.\n"
            f"  Status : {http_err.status_code}\n"
            f"  Reason : {http_err.reason}",
            file=sys.stderr,
        )
        return None


# ---------------------------------------------------------------------------
# Step 3: Extract a readable body from the MIME payload tree
# ---------------------------------------------------------------------------

def _decode_body_data(data):
    """
    Gmail encodes body content as Base64url before embedding it in the JSON
    API response, because raw email bytes (which can include arbitrary text
    encodings or binary-ish content) can't be safely represented inside JSON
    text as-is. Base64url makes the content ASCII-safe and URL-safe for
    transport, at the cost of needing to decode it back to real text here.

    Args:
        data: The Base64url-encoded string from payload["body"]["data"].

    Returns:
        str: Decoded plain text, or a fallback message on failure.
    """
    try:
        # Base64 requires the encoded string length to be a multiple of 4;
        # Gmail sometimes omits the trailing '=' padding, so we add it back.
        padded = data + "=" * (-len(data) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        return f"[Error decoding body: {exc}]"


def extract_body(payload):
    """
    Recursively search a Gmail message payload for a text/plain body.

    A simple email has payload["body"]["data"] directly. A multipart email
    instead has payload["parts"], a list where each part has its own
    mimeType and either its own body.data or further nested "parts"
    (e.g. multipart/alternative nested inside multipart/mixed for an email
    with both text and an attachment). This function walks that tree.

    Args:
        payload: The "payload" dict from a Gmail message resource.

    Returns:
        str: The decoded plain-text body, or a fallback string if none found.
    """
    if not payload:
        return "[No plain-text body found]"

    mime_type = payload.get("mimeType", "")

    # Case 1: this part IS a plain-text part with inline data
    if mime_type == "text/plain":
        body_data = payload.get("body", {}).get("data")
        if body_data:
            return _decode_body_data(body_data)

    # Case 2: this part has nested parts (multipart) — recurse into each
    parts = payload.get("parts")
    if parts:
        for part in parts:
            result = extract_body(part)
            if result and result != "[No plain-text body found]":
                return result

    # Case 3: no parts, not text/plain, and/or no usable data found
    return "[No plain-text body found]"


# ---------------------------------------------------------------------------
# Step 4: Extract sender/subject/date + body into one clean dict
# ---------------------------------------------------------------------------

def extract_email_data(message):
    """
    Pull sender, subject, date, and body out of a full Gmail message resource.

    Header order isn't guaranteed by Gmail, so headers are matched by name
    case-insensitively rather than by fixed list position.

    Args:
        message: Full message resource from get_message().

    Returns:
        dict: {"sender": ..., "subject": ..., "date": ..., "body": ...}
    """
    headers = message.get("payload", {}).get("headers", [])

    def find_header(name):
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value", "")
        return "(unknown)"

    return {
        "sender": find_header("From"),
        "subject": find_header("Subject"),
        "date": find_header("Date"),
        "body": extract_body(message.get("payload", {})),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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
            continue  # error already printed inside get_message()

        email_data = extract_email_data(message)

        separator = "=" * 40
        print(f"\n{separator}")
        print(f"Email {index}")
        print("-" * 40)
        print(f"From: {email_data['sender']}")
        print(f"Subject: {email_data['subject']}")
        print(f"Date: {email_data['date']}")
        print("Body:")
        print(email_data["body"])
        print(separator)


if __name__ == "__main__":
    main()