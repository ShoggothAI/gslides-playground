"""
Authentication module for Google Slides Templater.
"""

import json
import os
from pathlib import Path
from typing import Optional, Union, List

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuth2Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Default scopes needed for Google Slides operations
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive",
]


class Credentials:
    """Manages Google API credentials for authentication."""

    def __init__(self,
                 credentials: Union[OAuth2Credentials, ServiceAccountCredentials],
                 scopes: List[str] = None):
        """
        Initialize with Google API credentials.

        Args:
            credentials: The Google API credentials object.
            scopes: The OAuth scopes to request.
        """
        self.credentials = credentials
        self.scopes = scopes or DEFAULT_SCOPES
        self._slides_service = None
        self._drive_service = None

    @property
    def slides_service(self):
        """Get the Google Slides API service."""
        if self._slides_service is None:
            self._slides_service = build('slides', 'v1', credentials=self.credentials)
        return self._slides_service

    @property
    def drive_service(self):
        """Get the Google Drive API service."""
        if self._drive_service is None:
            self._drive_service = build('drive', 'v3', credentials=self.credentials)
        return self._drive_service

    def refresh(self) -> bool:
        """
        Refresh the credentials if they are expired.

        Returns:
            bool: True if credentials were refreshed, False otherwise.
        """
        if not hasattr(self.credentials, 'expired'):
            return False

        if self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())
            # Reset services to force rebuild with new credentials
            self._slides_service = None
            self._drive_service = None
            return True
        return False

    def to_json(self) -> str:
        """
        Convert credentials to JSON string.

        Returns:
            str: JSON string representation of the credentials.
        """
        if hasattr(self.credentials, 'to_json'):
            return self.credentials.to_json()
        return json.dumps({})

    def save(self, path: Union[str, Path]) -> None:
        """
        Save credentials to a file.

        Args:
            path: Path to save the credentials to.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            f.write(self.to_json())


def authenticate(
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
        service_account_file: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        auth_local_webserver: bool = True
) -> Credentials:
    """
    Authenticate with Google API.

    This function supports multiple authentication methods:
    1. Service account authentication
    2. OAuth2 with saved refresh token
    3. OAuth2 interactive flow

    Args:
        credentials_path: Path to OAuth client credentials JSON file.
        token_path: Path to save/load OAuth tokens.
        service_account_file: Path to service account JSON file.
        scopes: OAuth scopes to request.
        auth_local_webserver: Whether to use a local webserver for OAuth flow.

    Returns:
        Credentials object with authenticated credentials.

    Raises:
        FileNotFoundError: If required credential files are not found.
        ValueError: If no authentication method is provided.
    """
    scopes = scopes or DEFAULT_SCOPES

    # Method 1: Service account authentication
    if service_account_file:
        if not os.path.exists(service_account_file):
            raise FileNotFoundError(f"Service account file not found: {service_account_file}")

        credentials = ServiceAccountCredentials.from_service_account_file(
            service_account_file, scopes=scopes)
        return Credentials(credentials, scopes)

    # Method 2: OAuth with saved refresh token
    if token_path and os.path.exists(token_path):
        try:
            creds = OAuth2Credentials.from_authorized_user_info(
                json.load(open(token_path)), scopes)

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            return Credentials(creds, scopes)
        except Exception as e:
            print(f"Warning: Could not load token from {token_path}: {e}")
            # Fall through to next method

    # Method 3: OAuth interactive flow
    if credentials_path:
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"OAuth credentials file not found: {credentials_path}")

        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path, scopes)

        if auth_local_webserver:
            creds = flow.run_local_server(port=0)
        else:
            creds = flow.run_console()

        # Save credentials to token path if provided
        if token_path:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        return Credentials(creds, scopes)

    # Try application default credentials as a fallback
    try:
        credentials, _ = google.auth.default(scopes=scopes)
        return Credentials(credentials, scopes)
    except Exception:
        pass

    raise ValueError(
        "No authentication method provided. Please specify either "
        "credentials_path, token_path, or service_account_file."
    )
