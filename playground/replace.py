import logging
from typing import Any

import gslides
from gslides import creds as re_creds

from gslides_api import Presentation, initialize_credentials


presentation_id = "1bj3qEcf1P6NhShY8YC0UyEwpc_bFdrxxtijqz8hBbXM"

# If modifying these scopes, delete the file token.json.

credential_location = "/home/james/Dropbox/PyCharmProjects/gslides-playground/"


logger = logging.getLogger(__name__)

initialize_credentials(credential_location)

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
presentation = Presentation.from_json(output)
print(f"\nSuccessfully converted presentation with ID: {presentation.presentationId}")
print(f"Number of slides: {len(presentation.slides)}")
print(
    f"First slide title: {presentation.slides[0].pageElements[0].shape.text.textElements[1].textRun.content if presentation.slides[0].pageElements[0].shape.text else 'No title'}"
)

slide = presentation.slides[7]
new_slide = slide.duplicate(presentation_id=presentation_id)
new_slide.delete(presentation_id=presentation_id)
slide.move(presentation_id=presentation_id, insertion_index=10)
new_slide_2 = slide.write(presentation_id=presentation_id, insertion_index=8)
new_slide_2.delete(presentation_id=presentation_id)
print("Slide written successfully")
