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
