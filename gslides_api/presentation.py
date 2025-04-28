import copy
import logging
from typing import List, Optional, Dict, Any

from pydantic import BaseModel

from gslides_api import Size, SizeWithUnit
from gslides_api.execute import create_presentation, get_presentation_json
from gslides_api.slide import Slide

logger = logging.getLogger(__name__)


class Presentation(BaseModel):
    """Represents a Google Slides presentation."""

    # Use Dict[str, Any] to capture all fields from the original JSON
    model_config = {"extra": "allow"}

    presentationId: str
    pageSize: Size
    slides: List[Slide]
    title: Optional[str] = None
    locale: Optional[str] = None
    revisionId: Optional[str] = None
    masters: Optional[List[Dict[str, Any]]] = None
    layouts: Optional[List[Dict[str, Any]]] = None
    notesMaster: Optional[Dict[str, Any]] = None

    @classmethod
    def create_blank(cls, title: str = "New Presentation") -> "Presentation":
        """Create a blank presentation in Google Slides."""
        new_id = create_presentation({"title": title})
        return cls.from_id(new_id)

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "Presentation":
        """
        Convert a JSON representation of a presentation into a Presentation object.

        Args:
            json_data: The JSON data representing a Google Slides presentation

        Returns:
            A Presentation object populated with the data from the JSON
        """
        # Make a deep copy of the input data to avoid modifying it
        processed_data = copy.deepcopy(json_data)

        # Process the pageSize which has a nested structure
        if "pageSize" in processed_data:
            processed_data["pageSize"] = {
                "width": SizeWithUnit.from_api_format(processed_data["pageSize"]["width"]),
                "height": SizeWithUnit.from_api_format(processed_data["pageSize"]["height"]),
                "unit": processed_data["pageSize"]["width"]["unit"],
            }

        # Use Pydantic's model_validate to parse the processed JSON
        out = cls.model_validate(processed_data)
        for s in out.slides:
            s.presentation_id = out.presentationId
        return out

    @classmethod
    def from_id(cls, presentation_id: str) -> "Presentation":
        presentation_json = get_presentation_json(presentation_id)
        return cls.from_json(presentation_json)

    def clone(self) -> "Presentation":
        """Clone a presentation in Google Slides."""
        config = self.to_api_format()
        config.pop("presentationId", None)
        config.pop("revisionId", None)
        new_id = create_presentation(config)
        return self.from_id(new_id)

    def sync_from_cloud(self):
        re_p = Presentation.from_id(self.presentationId)
        self.__dict__ = re_p.__dict__

    def slide_from_id(self, slide_id: str) -> Optional[Slide]:
        match = [s for s in self.slides if s.objectId == slide_id]
        if len(match) == 0:
            logger.error(
                f"Slide with id {slide_id} not found in presentation {self.presentationId}"
            )
            return None
        return match[0]

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Start with a copy of any extra fields
        result = {
            k: v
            for k, v in self.__dict__.items()
            if k
            not in [
                "presentationId",
                "pageSize",
                "slides",
                "title",
                "locale",
                "revisionId",
                "masters",
                "layouts",
                "notesMaster",
            ]
        }

        # Add the standard fields
        result["presentationId"] = self.presentationId

        # Convert pageSize back to the original nested structure
        width_val = (
            self.pageSize.width.to_api_format()
            if isinstance(self.pageSize.width, SizeWithUnit)
            else {"magnitude": self.pageSize.width, "unit": self.pageSize.unit}
        )
        height_val = (
            self.pageSize.height.to_api_format()
            if isinstance(self.pageSize.height, SizeWithUnit)
            else {"magnitude": self.pageSize.height, "unit": self.pageSize.unit}
        )

        result["pageSize"] = {"width": width_val, "height": height_val}

        # Add slides
        result["slides"] = [slide.to_api_format() for slide in self.slides]

        # Add optional fields if they exist
        if self.title is not None:
            result["title"] = self.title

        if self.locale is not None:
            result["locale"] = self.locale

        if self.revisionId is not None:
            result["revisionId"] = self.revisionId

        if self.masters is not None:
            result["masters"] = self.masters

        if self.layouts is not None:
            result["layouts"] = self.layouts

        if self.notesMaster is not None:
            result["notesMaster"] = self.notesMaster

        return result
