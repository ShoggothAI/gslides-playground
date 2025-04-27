from typing import List, Optional, Dict, Any

from gslides_api.domain import GSlidesBaseModel, PageProperties, NotesProperties
from gslides_api.element import PageElement


class NotesPage(GSlidesBaseModel):
    """Represents a notes page associated with a slide."""

    objectId: str
    pageType: str
    pageElements: List[PageElement]
    pageProperties: PageProperties
    notesProperties: Optional[NotesProperties] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {
            "objectId": self.objectId,
            "pageType": self.pageType,
            "pageElements": [element.to_api_format() for element in self.pageElements],
            "pageProperties": self.pageProperties.to_api_format(),
        }

        if self.notesProperties is not None:
            result["notesProperties"] = self.notesProperties.to_api_format()

        return result
