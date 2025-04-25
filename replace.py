import os
import os.path
import logging
from typing import Any, Dict, List, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import gslides_api.presentation

try:
    import gslides
except ModuleNotFoundError:
    import sys

    gslides_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "../gslides"))
    print("yay")
    sys.path.append(gslides_path)

    import gslides
#
# from gslides import Frame, Spreadsheet, Table, Series, Chart

presentation_id = "1bj3qEcf1P6NhShY8YC0UyEwpc_bFdrxxtijqz8hBbXM"

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/spreadsheets",
]

credential_location = "/home/james/Dropbox/PyCharmProjects/gslides-playground/"

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

logger = logging.getLogger(__name__)

from gslides import creds as re_creds

service: Any = re_creds.slide_service
logger.info("Retrieving presentation")
output = service.presentations().get(presentationId=presentation_id).execute()

import json
import pprint

# Print the structure of the output JSON
print("Output keys:", output.keys())
print("\nSample of the output structure:")
pprint.pprint({k: type(output[k]) for k in output.keys()})

# Save the output to a file for inspection
with open("presentation_output.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nOutput JSON saved to presentation_output.json")

# Convert the JSON output to domain objects
# Use the from_json method to convert the JSON to a Presentation object
presentation = gslides_api.presentation.Presentation.from_json(output)
print(f"\nSuccessfully converted presentation with ID: {presentation.presentationId}")
print(f"Number of slides: {len(presentation.slides)}")
print(
    f"First slide title: {presentation.slides[0].pageElements[0].shape.text.textElements[1].textRun.content if presentation.slides[0].pageElements[0].shape.text else 'No title'}"
)

# Convert the Presentation object back to the API format
reconstructed_json = presentation.to_api_format()

# Save the reconstructed JSON for comparison
with open("reconstructed_output.json", "w") as f:
    json.dump(reconstructed_json, f, indent=2)

print("\nReconstructed JSON saved to reconstructed_output.json")
print(f"Original JSON keys: {output.keys()}")
print(f"Reconstructed JSON keys: {reconstructed_json.keys()}")

# Compare the original and reconstructed JSON
print("\nComparing original and reconstructed JSON...")
if output == reconstructed_json:
    print("The original and reconstructed JSON are identical!")
else:
    print("The original and reconstructed JSON are different.")
