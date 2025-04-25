import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import gslides


def initialize_credentials(credential_location: str):
    """

    :param credential_location:
    :return:
    """

    SCOPES = [
        "https://www.googleapis.com/auth/presentations",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(credential_location + "token.json"):
        creds = Credentials.from_authorized_user_file(credential_location + "token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_location + "credentials.json", SCOPES
            )
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(credential_location + "token.json", "w") as token:
            token.write(creds.to_json())
    gslides.initialize_credentials(creds)
