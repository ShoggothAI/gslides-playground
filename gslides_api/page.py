from typing import Optional, List, Union, ForwardRef

import logging

from pydantic import Field

from gslides_api import PageBackgroundFill, ColorScheme
from gslides_api.domain import (
    GSlidesBaseModel,
    MasterProperties,
    NotesProperties,
    PageType,
    LayoutReference,
)

# Import PageElement and ElementKind directly to avoid circular imports
from gslides_api.element import PageElement, ElementKind
from gslides_api.execute import slides_batch_update, get_slide_json
from gslides_api.utils import duplicate_object, delete_object, dict_to_dot_separated_field_list

logger = logging.getLogger(__name__)


class SlideProperties(GSlidesBaseModel):
    """Represents properties of a slide."""

    layoutObjectId: Optional[str] = None
    masterObjectId: Optional[str] = None
    notesPage: Optional[ForwardRef("Page")] = None
    isSkipped: Optional[bool] = None


class LayoutProperties(GSlidesBaseModel):
    """Represents properties of a layout."""

    masterObjectId: Optional[str] = None
    name: Optional[str] = None
    displayName: Optional[str] = None


# https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations.pages#pageproperties
# The page will inherit properties from the parent page.
# Depending on the page type the hierarchy is defined in either SlideProperties or LayoutProperties.


class SlidePageProperties(SlideProperties):
    """Represents properties of a page."""

    pageBackgroundFill: Optional[PageBackgroundFill] = None
    colorScheme: Optional[ColorScheme] = None


class LayoutPageProperties(LayoutProperties):
    """Represents properties of a page."""

    pageBackgroundFill: Optional[PageBackgroundFill] = None
    colorScheme: Optional[ColorScheme] = None


class Page(GSlidesBaseModel):
    """Represents a slide in a presentation."""

    objectId: Optional[str] = None
    pageElements: Optional[List[PageElement]] = (
        None  # Make optional to preserve original JSON exactly
    )
    revisionId: Optional[str] = None
    pageProperties: Optional[Union[SlidePageProperties, LayoutPageProperties]] = None
    pageType: Optional[PageType] = None

    # Union field properties - only one of these should be set
    slideProperties: Optional[SlideProperties] = None
    layoutProperties: Optional[LayoutProperties] = None
    notesProperties: Optional[NotesProperties] = None
    masterProperties: Optional[MasterProperties] = None

    # Store the presentation ID for reference but exclude from model_dump
    presentation_id: Optional[str] = Field(default=None, exclude=True)

    @classmethod
    def create_blank(
        cls,
        presentation_id: str,
        insertion_index: Optional[int] = None,
        slide_layout_reference: Optional[LayoutReference] = None,
        layoout_placeholder_id_mapping: Optional[dict] = None,
    ) -> "Page":
        """Create a blank slide in a Google Slides presentation.

        Args:
            presentation_id: The ID of the presentation to create the slide in.
            insertion_index: The index to insert the slide at. If not provided, the slide will be added at the end.
            slide_layout_reference: The layout reference to use for the slide.
            layoout_placeholder_id_mapping: The mapping of placeholder IDs to use for the slide.
        """

        # https://developers.google.com/slides/api/reference/rest/v1/presentations/request#CreateSlideRequest
        base = {} if insertion_index is None else {"insertionIndex": insertion_index}
        if slide_layout_reference is not None:
            base["slideLayoutReference"] = slide_layout_reference.to_api_format()

        out = slides_batch_update([{"createSlide": base}], presentation_id)
        new_slide_id = out["replies"][0]["createSlide"]["objectId"]

        return cls.from_ids(presentation_id, new_slide_id)

    @classmethod
    def from_ids(cls, presentation_id: str, slide_id: str) -> "Page":
        # To avoid circular imports
        json = get_slide_json(presentation_id, slide_id)
        new_slide = cls.model_validate(json)
        return new_slide

    def write_copy(
        self,
        insertion_index: Optional[int] = None,
        presentation_id: Optional[str] = None,
    ) -> "Page":
        """Write the slide to a Google Slides presentation.

        Args:
            presentation_id: The ID of the presentation to write to.
            insertion_index: The index to insert the slide at. If not provided, the slide will be added at the end.
        """
        presentation_id = presentation_id or self.presentation_id

        new_slide = self.create_blank(
            presentation_id,
            insertion_index,
            slide_layout_reference=LayoutReference(layoutId=self.slideProperties.layoutObjectId),
        )
        slide_id = new_slide.objectId

        # Set the page properties
        try:
            # TODO: this raises an InternalError sometimes, need to debug
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
        except Exception as e:
            logger.error(f"Error writing page properties: {e}")

        # Set the slid properties that hadn't been set when creating the slide
        slide_properties = self.slideProperties.to_api_format()
        # Not clear with which call this can be set, but updateSlideProperties rejects it
        slide_properties.pop("masterObjectId", None)
        # This has already been set when creating the slide
        slide_properties.pop("layoutObjectId", None)
        request = [
            {
                "updateSlideProperties": {
                    "objectId": slide_id,
                    "slideProperties": slide_properties,
                    "fields": ",".join(dict_to_dot_separated_field_list(slide_properties)),
                }
            }
        ]
        slides_batch_update(request, presentation_id)

        if self.pageElements is not None:
            # Some elements came from layout, some were created manually
            # Let's first match those that came from layout, before creating new ones
            for kind in ElementKind:
                my_elements = self.select_elements(kind)
                layout_elements = new_slide.select_elements(kind)
                for i, element in enumerate(my_elements):
                    if i < len(layout_elements):
                        element_id = layout_elements[i].objectId
                    else:
                        element_id = element.create_copy(slide_id, presentation_id)
                    element.update(presentation_id, element_id)

        return self.from_ids(presentation_id, slide_id)

    def select_elements(self, kind: ElementKind) -> List[PageElement]:
        if self.pageElements is None:
            return []
        return [e for e in self.pageElements if getattr(e, kind.value) is not None]

    @property
    def image_elements(self):
        if self.pageElements is None:
            return []
        return [e for e in self.pageElements if e.image is not None]

    def duplicate(self) -> "Page":
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


SlidePageProperties.model_rebuild()
Page.model_rebuild()
