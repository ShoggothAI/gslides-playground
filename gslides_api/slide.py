from typing import Optional, List, Dict, Any
import logging

from jupyter_client.session import new_id
from pydantic import BaseModel

from gslides_api.domain import PageProperties, GSlidesBaseModel
from gslides_api.element import PageElement
from gslides_api.execute import slides_batch_update
from gslides_api.notes import NotesPage

logger = logging.getLogger(__name__)


class SlideProperties(GSlidesBaseModel):
    """Represents properties of a slide."""

    layoutObjectId: str
    masterObjectId: str
    notesPage: Optional[NotesPage] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {"layoutObjectId": self.layoutObjectId, "masterObjectId": self.masterObjectId}

        if self.notesPage is not None:
            result["notesPage"] = self.notesPage.to_api_format()

        return result


class Slide(BaseModel):
    """Represents a slide in a presentation."""

    objectId: Optional[str] = None
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

    def create_blank(self, presentation_id: str, insertion_index: Optional[int] = None) -> str:
        """Create a blank slide in a Google Slides presentation.

        Args:
            presentation_id: The ID of the presentation to create the slide in.
            insertion_index: The index to insert the slide at. If not provided, the slide will be added at the end.
        """
        base = {} if insertion_index is None else {"insertionIndex": insertion_index}

        out = slides_batch_update([{"createSlide": base}], presentation_id)
        new_slide_id = out["replies"][0]["createSlide"]["objectId"]
        return new_slide_id

    def write(
        self,
        presentation_id: str,
        insertion_index: Optional[int] = None,
        slide_id: Optional[str] = None,
    ) -> None:
        """Write the slide to a Google Slides presentation.

        Args:
            presentation_id: The ID of the presentation to write to.
            insertion_index: The index to insert the slide at. If not provided, the slide will be added at the end.
            slide_id: The ID of the slide to write to. If not provided, a new slide will be created.
        """
        assert (
            slide_id is None or insertion_index is None
        ), "Cannot specify both slide_id and insertion_index"

        if slide_id is None:
            slide_id = self.create_blank(presentation_id, insertion_index)
            create_new = True
        else:
            create_new = False
        # TODO: this raises an InternalError, need to debug
        # request = [
        #     {
        #         "updatePageProperties": {
        #             "objectId": slide_id,
        #             "pageProperties": self.pageProperties.to_api_format(),
        #             "fields": "*",
        #         }
        #     }
        # ]
        # slides_batch_update(request, presentation_id)
        # TODO: how about SlideProperties?
        if self.pageElements is not None:
            for element in self.pageElements:
                if create_new:
                    element_id = element.create(slide_id, presentation_id)
                else:
                    element_id = element.objectId

                element.update(presentation_id, element_id)

        print("Slide created successfully!")
