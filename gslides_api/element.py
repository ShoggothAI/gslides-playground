from typing import Optional, Dict, Any

from gslides_api.domain import GSlidesBaseModel, Transform, Shape, Table, Image, Size, Video


class PageElement(GSlidesBaseModel):
    """Represents an element on a slide."""

    objectId: str
    size: Size
    transform: Transform
    shape: Optional[Shape] = None
    table: Optional[Table] = None
    image: Optional[Image] = None
    video: Optional[Video] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Start with a copy of any extra fields
        result = {
            k: v
            for k, v in self.__dict__.items()
            if k not in ["objectId", "size", "transform", "shape", "table", "image", "video"]
        }

        # Add the standard fields
        result["objectId"] = self.objectId
        result["size"] = self.size.to_api_format()
        result["transform"] = self.transform.to_api_format()

        if self.shape is not None:
            result["shape"] = self.shape.to_api_format()

        if self.table is not None:
            result["table"] = self.table.to_api_format()

        if self.image is not None:
            result["image"] = self.image.to_api_format()

        if self.video is not None:
            result["video"] = self.video.to_api_format()

        return result
