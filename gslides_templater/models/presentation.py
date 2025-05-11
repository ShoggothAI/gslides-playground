"""
Presentation model for Google Slides Templater.
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from pydantic import Field

from gslides_templater.models.base import APIObject
from gslides_templater.models.slide import Slide

if TYPE_CHECKING:
    from gslides_templater.client import SlidesClient


class Size(APIObject):
    """Represents the size of a presentation or element."""

    width: Dict[str, Any] = Field({}, alias="width")
    height: Dict[str, Any] = Field({}, alias="height")


class Presentation(APIObject):
    """
    Represents a Google Slides presentation.

    This class provides methods for accessing and manipulating the presentation
    and its slides.
    """

    presentation_id: Optional[str] = Field(None, alias="presentationId")
    title: Optional[str] = None
    locale: Optional[str] = None
    slides: List['Slide'] = Field(default_factory=list)
    masters: List[Dict[str, Any]] = Field(default_factory=list)
    layouts: List[Dict[str, Any]] = Field(default_factory=list)
    page_size: Optional[Size] = Field(None, alias="pageSize")
    revision_id: Optional[str] = Field(None, alias="revisionId")

    # Client reference for operations - not part of the API model
    _client: Optional['SlidesClient'] = None

    def with_client(self, client: 'SlidesClient') -> 'Presentation':
        """
        Set the client for this presentation.

        Args:
            client: The client to use for operations on this presentation.

        Returns:
            self for method chaining.
        """
        self._client = client

        # Propagate client to slides
        for slide in self.slides:
            slide._presentation_id = self.presentation_id
            slide._client = client

        return self

    @property
    def url(self) -> Optional[str]:
        """
        Get the URL to view the presentation in a browser.

        Returns:
            The URL to the presentation, or None if presentation_id is not set.
        """
        if not self.presentation_id:
            return None
        return f"https://docs.google.com/presentation/d/{self.presentation_id}/edit"

    @property
    def num_slides(self) -> int:
        """
        Get the number of slides in the presentation.

        Returns:
            The number of slides.
        """
        return len(self.slides)

    def get_slide(self, slide_id: str) -> Optional[Slide]:
        """
        Get a slide by ID.

        Args:
            slide_id: The ID of the slide to get.

        Returns:
            The slide with the specified ID, or None if not found.
        """
        for slide in self.slides:
            if slide.object_id == slide_id:
                return slide
        return None

    def get_slide_by_index(self, index: int) -> Optional[Slide]:
        """
        Get a slide by index.

        Args:
            index: The index of the slide to get.

        Returns:
            The slide at the specified index, or None if index is out of bounds.
        """
        if 0 <= index < len(self.slides):
            return self.slides[index]
        return None

    def create_slide(self, **kwargs) -> Optional[Slide]:
        """
        Create a new slide in the presentation.

        Args:
            **kwargs: Additional arguments to pass to the create_slide method of the client.

        Returns:
            The newly created slide, or None if creation fails.

        Raises:
            ValueError: If the client is not set.
        """
        if not self._client:
            raise ValueError("Client not set. Use with_client() to set a client.")

        if not self.presentation_id:
            raise ValueError("Presentation ID not set.")

        slide = self._client.create_slide(self.presentation_id, **kwargs)

        # Update the local slides list
        if slide:
            slide._client = self._client
            slide._presentation_id = self.presentation_id
            self.slides.append(slide)

        return slide

    def duplicate_slide(self, slide_id: str) -> Optional[Slide]:
        """
        Duplicate a slide in the presentation.

        Args:
            slide_id: The ID of the slide to duplicate.

        Returns:
            The duplicated slide, or None if duplication fails.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the slide with the specified ID is not found.
        """
        if not self._client:
            raise ValueError("Client not set. Use with_client() to set a client.")

        if not self.presentation_id:
            raise ValueError("Presentation ID not set.")

        # Check if the slide exists
        if not self.get_slide(slide_id):
            raise ValueError(f"Slide with ID {slide_id} not found.")

        # Duplicate the slide
        slide = self._client.duplicate_slide(self.presentation_id, slide_id)

        # Update the local slides list
        if slide:
            slide._client = self._client
            slide._presentation_id = self.presentation_id
            self.slides.append(slide)

        return slide

    def delete_slide(self, slide_id: str) -> None:
        """
        Delete a slide from the presentation.

        Args:
            slide_id: The ID of the slide to delete.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the slide with the specified ID is not found.
        """
        if not self._client:
            raise ValueError("Client not set. Use with_client() to set a client.")

        if not self.presentation_id:
            raise ValueError("Presentation ID not set.")

        # Check if the slide exists
        slide_to_delete = self.get_slide(slide_id)
        if not slide_to_delete:
            raise ValueError(f"Slide with ID {slide_id} not found.")

        # Delete the slide
        self._client.delete_slide(self.presentation_id, slide_id)

        # Update the local slides list
        self.slides = [slide for slide in self.slides if slide.object_id != slide_id]

    def move_slide(self, slide_id: str, insertion_index: int) -> None:
        """
        Move a slide to a new position in the presentation.

        Args:
            slide_id: The ID of the slide to move.
            insertion_index: The index to move the slide to.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the slide with the specified ID is not found.
            ValueError: If the insertion index is out of bounds.
        """
        if not self._client:
            raise ValueError("Client not set. Use with_client() to set a client.")

        if not self.presentation_id:
            raise ValueError("Presentation ID not set.")

        # Check if the slide exists
        slide_to_move = self.get_slide(slide_id)
        if not slide_to_move:
            raise ValueError(f"Slide with ID {slide_id} not found.")

        # Check if the insertion index is valid
        if insertion_index < 0 or insertion_index > len(self.slides):
            raise ValueError(f"Insertion index {insertion_index} is out of bounds.")

        # Move the slide
        self._client.move_slide(self.presentation_id, slide_id, insertion_index)

        # Update the local slides list
        # Remove the slide from its current position
        self.slides = [slide for slide in self.slides if slide.object_id != slide_id]

        # Insert the slide at the new position
        self.slides.insert(insertion_index, slide_to_move)

    def refresh(self) -> 'Presentation':
        """
        Refresh the presentation data from the API.

        Returns:
            self for method chaining.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set. Use with_client() to set a client.")

        if not self.presentation_id:
            raise ValueError("Presentation ID not set.")

        # Get the presentation from the API
        updated = self._client.get_presentation(self.presentation_id)

        # Update the local presentation
        self.title = updated.title
        self.locale = updated.locale
        self.slides = updated.slides
        self.masters = updated.masters
        self.layouts = updated.layouts
        self.page_size = updated.page_size
        self.revision_id = updated.revision_id

        # Set the client and presentation ID on the slides
        for slide in self.slides:
            slide._client = self._client
            slide._presentation_id = self.presentation_id

        return self

    def copy(self, new_title: Optional[str] = None) -> Optional['Presentation']:
        """
        Create a copy of the presentation.

        Args:
            new_title: The title for the new presentation.
                If None, a default title will be used.

        Returns:
            The copied presentation, or None if copying fails.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set. Use with_client() to set a client.")

        if not self.presentation_id:
            raise ValueError("Presentation ID not set.")

        # Create a copy of the presentation
        copied = self._client.copy_presentation(self.presentation_id, title=new_title)

        # Set the client on the copied presentation
        if copied:
            copied = copied.with_client(self._client)

        return copied

    def create_batch_request(self):
        """
        Create a batch request for this presentation.

        Returns:
            A BatchRequest object for this presentation.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set. Use with_client() to set a client.")

        if not self.presentation_id:
            raise ValueError("Presentation ID not set.")

        return self._client.create_batch_request(self.presentation_id)