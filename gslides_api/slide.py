from typing import Optional, List, Dict, Any
import logging

from jupyter_client.session import new_id
from pydantic import BaseModel

from gslides_api.create import element_to_create_request, element_to_update_request
from gslides_api.domain import PageElement, SlideProperties, PageProperties
from gslides_api.execute import slides_batch_update

logger = logging.getLogger(__name__)


class Slide(BaseModel):
    """Represents a slide in a presentation."""

    # Use Dict[str, Any] to capture all fields from the original JSON
    model_config = {"extra": "allow"}

    objectId: str
    pageElements: Optional[List[PageElement]] = (
        None  # Make optional to preserve original JSON exactly
    )
    slideProperties: SlideProperties
    pageProperties: PageProperties

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Start with a copy of any extra fields
        result = {
            k: v
            for k, v in self.__dict__.items()
            if k not in ["objectId", "pageElements", "slideProperties", "pageProperties"]
        }

        # Add the standard fields
        result["objectId"] = self.objectId
        result["slideProperties"] = self.slideProperties.to_api_format()
        result["pageProperties"] = self.pageProperties.to_api_format()

        # Only include pageElements if it exists in the original
        if self.pageElements is not None:
            result["pageElements"] = [element.to_api_format() for element in self.pageElements]

        return result

    def write(self, presentation_id: str, insertion_index: Optional[int] = None) -> None:
        """Write the slide to a Google Slides presentation.

        Args:
            presentation_id: The ID of the presentation to write to.
        """

        base = {} if insertion_index is None else {"insertionIndex": insertion_index}

        return_values = []
        out = slides_batch_update([{"createSlide": base}], presentation_id)
        new_slide_id = out["replies"][0]["createSlide"]["objectId"]
        return_values.append(out)
        requests = []
        # requests.append(
        #     {
        #         "updatePageProperties": {
        #             "objectId": self.objectId,
        #             "properties": self.pageProperties.to_api_format(),
        #         }
        #     }
        # )
        # TODO: how about SlideProperties?
        if self.pageElements is not None:
            for element in self.pageElements:
                create_request = element_to_create_request(element, new_slide_id)
                out = slides_batch_update(create_request, presentation_id)
                return_values.append(out)
                if out is not None and "createShape" in out["replies"][0]:
                    new_element_id = out["replies"][0]["createShape"]["objectId"]
                    update_request = element_to_update_request(element, new_element_id)
                    if update_request is not None and len(update_request):
                        out = slides_batch_update(update_request, presentation_id)
                        return_values.append(out)

        print("Slide created successfully!")
