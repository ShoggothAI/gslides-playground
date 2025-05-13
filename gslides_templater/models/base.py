"""
Base models for Google Slides Templater.
"""

from typing import Dict, Any, Optional, ClassVar, Type, TypeVar, cast
from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict

T = TypeVar('T', bound='BaseModel')


class BaseModel(PydanticBaseModel):
    """Base model for all models in the library."""

    model_config = ConfigDict(
        extra='ignore',  # Ignore extra fields from the API
        populate_by_name=True,  # Allow populating by field name
        validate_assignment=True,  # Validate fields when values are assigned
        arbitrary_types_allowed=True,  # Allow arbitrary types
    )

    def to_api_format(self) -> Dict[str, Any]:
        """Convert the model to the format expected by the Google Slides API."""
        return self.model_dump(exclude_none=True, by_alias=True)

    @classmethod
    def from_api_format(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an instance from API format data."""
        return cls.model_validate(data)


class APIObject(BaseModel):
    """Base class for objects that have an ID and can be retrieved from the API."""

    object_id: Optional[str] = Field(None, alias="objectId")

    # Type to use for API object creation - override in subclasses
    _api_creation_type: ClassVar[str] = ""

    def _get_self_link(self, presentation_id: str) -> str:
        """
        Get a link to this object in the Google Slides UI.

        Args:
            presentation_id: The ID of the presentation containing this object.

        Returns:
            A URL to this object in the Google Slides UI.
        """
        if not self.object_id:
            return f"https://docs.google.com/presentation/d/{presentation_id}/edit"

        return f"https://docs.google.com/presentation/d/{presentation_id}/edit#slide={self.object_id}"

    @property
    def has_id(self) -> bool:
        """Check if this object has an ID."""
        return self.object_id is not None
