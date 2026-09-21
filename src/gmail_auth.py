"""
gmail_auth.py
-------------
Authenticates with the Gmail API using OAuth 2.0 (read-only scope) and
lists all labels in the authenticated user's mailbox as a connectivity test.

Expected files in the project root (one level above this src/ directory):
  - credentials.json   : OAuth 2.0 client secrets downloaded from Google Cloud Console
  - token.json         : Created automatically after the first successful login;
                         refreshed automatically on subsequent runs
"""

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Resolve paths relative to the project root (one level above src/)
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)

CREDENTIALS_FILE = os.path.join(_PROJECT_ROOT, "credentials.json")
TOKEN_FILE = os.path.join(_PROJECT_ROOT, "token.json")


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def get_credentials() -> Credentials:
    """
    Load credentials from token.json if available and valid.
    If the token is missing, expired, or invalid, run the OAuth flow using
    credentials.json and save the resulting token to token.json.

    Returns:
        google.oauth2.credentials.Credentials: Valid, scoped credentials.

    Raises:
        FileNotFoundError: If credentials.json is not found in the project root.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        print(
            f"[ERROR] credentials.json not found at: {CREDENTIALS_FILE}\n"
            "Please download your OAuth 2.0 client secrets from the Google Cloud "
            "Console and place the file as 'credentials.json' in the project root.",
            file=sys.stderr,
        )
        raise FileNotFoundError(f"Missing file: {CREDENTIALS_FILE}")

    creds = None

    # 1. Try loading an existing token
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as exc:
            print(f"[WARNING] Could not load token.json ({exc}). Re-authenticating...")
            creds = None

    # 2. Refresh if expired but a refresh token is available
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("[INFO] Access token refreshed successfully.")
        except Exception as exc:
            print(f"[WARNING] Token refresh failed ({exc}). Re-authenticating...")
            creds = None

    # 3. Run the full OAuth flow if we still don't have valid credentials
    if not creds or not creds.valid:
        print("[INFO] Opening browser for OAuth 2.0 login...")
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        print("[INFO] Authentication successful.")

    # 4. Persist the (possibly new/refreshed) token for next time
    with open(TOKEN_FILE, "w", encoding="utf-8") as token_fh:
        token_fh.write(creds.to_json())
    print(f"[INFO] Token saved to: {TOKEN_FILE}")

    return creds


# ---------------------------------------------------------------------------
# Gmail service factory
# ---------------------------------------------------------------------------

def build_gmail_service(creds: Credentials):
    """
    Build and return an authenticated Gmail API service object.

    Args:
        creds: Valid Google OAuth 2.0 credentials.

    Returns:
        googleapiclient.discovery.Resource: Gmail v1 service.
    """
    return build("gmail", "v1", credentials=creds)


# ---------------------------------------------------------------------------
# Connectivity test - list all Gmail labels
# ---------------------------------------------------------------------------

def list_labels(service) -> None:
    """
    Call the Gmail API to list all labels and print their names.
    Wraps the call in a try/except to surface clear error messages.

    Args:
        service: Authenticated Gmail v1 service resource.
    """
    try:
        response = service.users().labels().list(userId="me").execute()
        labels = response.get("labels", [])

        if not labels:
            print("No labels found in this Gmail account.")
            return

        separator = "-" * 40
        print(f"\n{separator}")
        print(f"  Gmail Labels ({len(labels)} found)")
        print(separator)
        for label in labels:
            print(f"  - {label['name']}")
        print(f"{separator}\n")

    except HttpError as http_err:
        print(
            f"[ERROR] Gmail API request failed.\n"
            f"  Status : {http_err.status_code}\n"
            f"  Reason : {http_err.reason}\n"
            f"  Details: {http_err.error_details}",
            file=sys.stderr,
        )
    except Exception as exc:
        print(f"[ERROR] Unexpected error while calling the Gmail API: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    creds = get_credentials()
    service = build_gmail_service(creds)
    list_labels(service)


if __name__ == "__main__":
    main()
