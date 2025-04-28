from typing import Optional, List, Dict, Any
import logging
import copy

from pydantic import BaseModel


from gslides_api.domain import PageProperties, GSlidesBaseModel
from gslides_api.element import PageElement
from gslides_api.execute import slides_batch_update
from gslides_api.notes import NotesPage
from gslides_api.utils import duplicate_object, delete_object, dict_to_dot_separated_field_list

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
    slideProperties: Optional[SlideProperties] = None
    pageProperties: Optional[PageProperties] = None
    presentation_id: Optional[str] = None  # Store the presentation ID for reference

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Start with a copy of any extra fields
        result = {
            k: v
            for k, v in self.__dict__.items()
            if k
            not in [
                "objectId",
                "pageElements",
                "slideProperties",
                "pageProperties",
                "presentation_id",
            ]
        }

        # Add the standard fields
        if self.objectId is not None:
            result["objectId"] = self.objectId

        if self.slideProperties is not None:
            result["slideProperties"] = self.slideProperties.to_api_format()

        if self.pageProperties is not None:
            result["pageProperties"] = self.pageProperties.to_api_format()

        # Only include pageElements if it exists in the original
        if self.pageElements is not None:
            result["pageElements"] = [element.to_api_format() for element in self.pageElements]

        return result

    @classmethod
    def create_blank(
        cls,
        presentation_id: str,
        insertion_index: Optional[int] = None,
    ) -> "Slide":
        """Create a blank slide in a Google Slides presentation.

        Args:
            presentation_id: The ID of the presentation to create the slide in.
            insertion_index: The index to insert the slide at. If not provided, the slide will be added at the end.
        """
        base = {} if insertion_index is None else {"insertionIndex": insertion_index}

        out = slides_batch_update([{"createSlide": base}], presentation_id)
        new_slide_id = out["replies"][0]["createSlide"]["objectId"]

        return cls.from_ids(presentation_id, new_slide_id)

    @classmethod
    def from_ids(cls, presentation_id: str, slide_id: str) -> "Slide":
        # To avoid circular imports
        from gslides_api.presentation import Presentation

        # If there is a way to just read a single slide, I haven't found it
        p = Presentation.from_id(presentation_id)
        new_slide = p.slide_from_id(slide_id)
        return new_slide

    def write_copy(
        self,
        insertion_index: Optional[int] = None,
        presentation_id: Optional[str] = None,
    ) -> "Slide":
        """Write the slide to a Google Slides presentation.

        Args:
            presentation_id: The ID of the presentation to write to.
            insertion_index: The index to insert the slide at. If not provided, the slide will be added at the end.
        """
        presentation_id = presentation_id or self.presentation_id

        new_slide = self.create_blank(presentation_id, insertion_index)
        slide_id = new_slide.objectId

        # TODO: this raises an InternalError, need to debug
        page_properties = self.pageProperties.to_api_format()
        request = [
            {
                "updatePageProperties": {
                    "objectId": slide_id,
                    "pageProperties": page_properties,
                    "fields": ",".join(dict_to_dot_separated_field_list(page_properties)),
                }
            }
        ]
        slides_batch_update(request, presentation_id)
        # TODO: how about SlideProperties?
        if self.pageElements is not None:
            for element in self.pageElements:
                element_id = element.create(slide_id, presentation_id)
                element.update(presentation_id, element_id)

        return self.from_ids(presentation_id, slide_id)

    def duplicate(self) -> "Slide":
        """
        Duplicates the slide in the same presentation.

        :return:
        """
        assert (
            self.presentation_id is not None
        ), "self.presentation_id must be set when calling duplicate()"
        new_id = duplicate_object(self.objectId, self.presentation_id)
        return self.from_ids(self.presentation_id, new_id)

    def delete(self) -> None:
        assert (
            self.presentation_id is not None
        ), "self.presentation_id must be set when calling delete()"

        return delete_object(self.objectId, self.presentation_id)

    def move(self, insertion_index: int) -> None:
        """
        Move the slide to a new position in the presentation.

        Args:
            insertion_index: The index to insert the slide at.
        """
        request = [
            {
                "updateSlidesPosition": {
                    "slideObjectIds": [self.objectId],
                    "insertionIndex": insertion_index,
                }
            }
        ]
        slides_batch_update(request, self.presentation_id)
