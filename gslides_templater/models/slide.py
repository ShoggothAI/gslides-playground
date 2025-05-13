"""
Slide model for Google Slides Templater.
"""

from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING
from pydantic import Field, model_validator

from gslides_templater.models.base import APIObject
from gslides_templater.models.enums import PageType

if TYPE_CHECKING:
    from gslides_templater.client import SlidesClient
    from gslides_templater.models.element import Element


class SlideProperties(APIObject):
    """Properties of a slide."""

    layout_object_id: Optional[str] = Field(None, alias="layoutObjectId")
    master_object_id: Optional[str] = Field(None, alias="masterObjectId")
    is_skipped: Optional[bool] = Field(None, alias="isSkipped")


class LayoutProperties(APIObject):
    """Properties of a layout."""

    master_object_id: Optional[str] = Field(None, alias="masterObjectId")
    name: Optional[str] = None
    display_name: Optional[str] = Field(None, alias="displayName")


class NotesProperties(APIObject):
    """Properties of notes."""

    speaker_notes_object_id: str = Field(..., alias="speakerNotesObjectId")


class MasterProperties(APIObject):
    """Properties of a master slide."""

    display_name: Optional[str] = Field(None, alias="displayName")


class Slide(APIObject):
    """
    Represents a slide in a Google Slides presentation.

    This class provides methods for accessing and manipulating the slide
    and its elements.
    """

    page_elements: List['Element'] = Field(default_factory=list, alias="pageElements")
    revision_id: Optional[str] = Field(None, alias="revisionId")
    slide_properties: Optional[SlideProperties] = Field(None, alias="slideProperties")
    layout_properties: Optional[LayoutProperties] = Field(None, alias="layoutProperties")
    notes_properties: Optional[NotesProperties] = Field(None, alias="notesProperties")
    master_properties: Optional[MasterProperties] = Field(None, alias="masterProperties")
    page_type: Optional[PageType] = Field(None, alias="pageType")
    page_background: Optional[Dict[str, Any]] = Field(None, alias="pageBackground")

    # References for operations - not part of the API model
    _client: Optional['SlidesClient'] = None
    _presentation_id: Optional[str] = None

    @model_validator(mode='after')
    def link_elements_to_slide(self) -> 'Slide':
        """Link elements to this slide."""
        for element in self.page_elements:
            element._slide = self
            element._presentation_id = self._presentation_id
            element._client = self._client
        return self

    @property
    def has_client(self) -> bool:
        """Check if this slide has a client associated with it."""
        return self._client is not None

    @property
    def url(self) -> Optional[str]:
        """
        Get the URL to view the slide in a browser.

        Returns:
            The URL to the slide, or None if presentation_id or object_id is not set.
        """
        if not self._presentation_id or not self.object_id:
            return None
        return f"https://docs.google.com/presentation/d/{self._presentation_id}/edit#slide={self.object_id}"

    def get_element(self, element_id: str) -> Optional['Element']:
        """
        Get an element by ID.

        Args:
            element_id: The ID of the element to get.

        Returns:
            The element with the specified ID, or None if not found.
        """
        for element in self.page_elements:
            if element.object_id == element_id:
                return element
        return None

    def get_elements_by_type(self, element_type: str) -> List['Element']:
        """
        Get all elements of a specific type.

        Args:
            element_type: The type of elements to get.

        Returns:
            A list of elements of the specified type.
        """
        return [element for element in self.page_elements
                if getattr(element, element_type, None) is not None]

    def refresh(self) -> 'Slide':
        """
        Refresh the slide data from the API.

        Returns:
            self for method chaining.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or slide ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Slide ID not set.")

        # Get the slide from the API
        updated = self._client.get_slide(self._presentation_id, self.object_id)

        # Update the local slide
        self.page_elements = updated.page_elements
        self.revision_id = updated.revision_id
        self.slide_properties = updated.slide_properties
        self.layout_properties = updated.layout_properties
        self.notes_properties = updated.notes_properties
        self.master_properties = updated.master_properties
        self.page_type = updated.page_type
        self.page_background = updated.page_background

        # Set the client and presentation ID on the elements
        for element in self.page_elements:
            element._slide = self
            element._presentation_id = self._presentation_id
            element._client = self._client

        return self

    def duplicate(self) -> Optional['Slide']:
        """
        Duplicate this slide in the same presentation.

        Returns:
            The duplicated slide, or None if duplication fails.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or slide ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Slide ID not set.")

        # Duplicate the slide
        return self._client.duplicate_slide(self._presentation_id, self.object_id)

    def delete(self) -> None:
        """
        Delete this slide from the presentation.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or slide ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Slide ID not set.")

        # Delete the slide
        self._client.delete_slide(self._presentation_id, self.object_id)

    def move(self, insertion_index: int) -> None:
        """
        Move this slide to a new position in the presentation.

        Args:
            insertion_index: The index to move the slide to.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or slide ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Slide ID not set.")

        # Move the slide
        self._client.move_slide(self._presentation_id, self.object_id, insertion_index)

    def replace_all_text(self, text: str, replacement: str,
                         match_case: bool = True) -> Dict[str, Any]:
        """
        Replace all occurrences of a text string in this slide.

        Args:
            text: The text to find.
            replacement: The text to replace it with.
            match_case: Whether to match case.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or slide ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Slide ID not set.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the replace text request, scoped to this slide
        batch.add_request({
            "replaceAllText": {
                "replaceText": replacement,
                "pageObjectIds": [self.object_id],
                "containsText": {
                    "text": text,
                    "matchCase": match_case
                }
            }
        })

        # Execute the batch request
        return batch.execute()

    def replace_placeholders(self, replacements: Dict[str, str]) -> Dict[str, Any]:
        """
        Replace placeholder text in this slide with actual content.

        Args:
            replacements: A dictionary mapping placeholder text to replacement text.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or slide ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Slide ID not set.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the replace text requests, scoped to this slide
        for placeholder, replacement in replacements.items():
            batch.add_request({
                "replaceAllText": {
                    "replaceText": replacement,
                    "pageObjectIds": [self.object_id],
                    "containsText": {
                        "text": f"{{{{{placeholder}}}}}",
                        "matchCase": True
                    }
                }
            })

        # Execute the batch request
        return batch.execute()

    def get_notes(self) -> Optional[str]:
        """
        Get the speaker notes for this slide.

        Returns:
            The speaker notes, or None if not available.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or slide ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Slide ID not set.")

        if not self.notes_properties:
            return None

        # Get the notes page
        notes_id = self.notes_properties.speaker_notes_object_id

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the get text request
        batch.add_request({
            "getPageObjectText": {
                "objectId": notes_id
            }
        })

        # Execute the batch request
        response = batch.execute()

        # Extract the text from the response
        if "replies" in response and len(response["replies"]) > 0:
            return response["replies"][0].get("getPageObjectText", {}).get("text", "")

        return None

    def set_notes(self, notes: str) -> Dict[str, Any]:
        """
        Set the speaker notes for this slide.

        Args:
            notes: The speaker notes to set.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or slide ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Slide ID not set.")

        if not self.notes_properties:
            return {}

        # Get the notes page
        notes_id = self.notes_properties.speaker_notes_object_id

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # First delete any existing text
        batch.add_request({
            "deleteText": {
                "objectId": notes_id,
                "textRange": {
                    "type": "ALL"
                }
            }
        })

        # Then insert the new text
        batch.add_request({
            "insertText": {
                "objectId": notes_id,
                "insertionIndex": 0,
                "text": notes
            }
        })

        # Execute the batch request
        return batch.execute()