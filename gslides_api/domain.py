from typing import List, Dict, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from pydantic.json import pydantic_encoder


class GSlidesBaseModel(BaseModel):
    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        return self.model_dump(exclude_none=True)


class SizeWithUnit(BaseModel):
    """Represents a size dimension with magnitude and unit."""

    magnitude: float
    unit: str = "EMU"  # Engineering Measurement Unit

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        return {"magnitude": self.magnitude, "unit": self.unit}

    @classmethod
    def from_api_format(cls, data: Dict[str, Any]) -> "SizeWithUnit":
        """Create a SizeWithUnit from API format."""
        if isinstance(data, dict) and "magnitude" in data:
            return cls(magnitude=data["magnitude"], unit=data.get("unit", "EMU"))
        # If it's just a number, assume it's the magnitude
        if isinstance(data, (int, float)):
            return cls(magnitude=data)
        raise ValueError(f"Cannot convert {data} to SizeWithUnit")


class Size(BaseModel):
    """Represents a size with width and height."""

    width: Union[float, SizeWithUnit]
    height: Union[float, SizeWithUnit]
    unit: str = "EMU"  # Engineering Measurement Unit

    @model_validator(mode="after")
    def convert_dimensions(self) -> "Size":
        """Convert width and height to SizeWithUnit if they are floats."""
        if isinstance(self.width, float):
            self.width = SizeWithUnit(magnitude=self.width, unit=self.unit)
        if isinstance(self.height, float):
            self.height = SizeWithUnit(magnitude=self.height, unit=self.unit)
        return self

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        width_val = (
            self.width.to_api_format()
            if isinstance(self.width, SizeWithUnit)
            else {"magnitude": self.width, "unit": self.unit}
        )
        height_val = (
            self.height.to_api_format()
            if isinstance(self.height, SizeWithUnit)
            else {"magnitude": self.height, "unit": self.unit}
        )
        return {"width": width_val, "height": height_val}


class Transform(BaseModel):
    """Represents a transformation applied to an element."""

    # Use Dict[str, Any] to capture all fields from the original JSON
    model_config = {"extra": "allow"}

    translateX: float
    translateY: float
    scaleX: float
    scaleY: float
    unit: Optional[str] = None  # Make optional to preserve original JSON exactly

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Start with a copy of any extra fields
        result = {
            k: v
            for k, v in self.__dict__.items()
            if k not in ["translateX", "translateY", "scaleX", "scaleY", "unit"]
        }

        # Add the standard fields
        result["translateX"] = self.translateX
        result["translateY"] = self.translateY
        result["scaleX"] = self.scaleX
        result["scaleY"] = self.scaleY

        # Only include unit if it was in the original
        if self.unit is not None:
            result["unit"] = self.unit

        return result


class ShapeType(Enum):
    """Enumeration of possible shape types."""

    TEXT_BOX = "TEXT_BOX"
    RECTANGLE = "RECTANGLE"
    ROUND_RECTANGLE = "ROUND_RECTANGLE"
    ELLIPSE = "ELLIPSE"
    LINE = "LINE"
    IMAGE = "IMAGE"
    UNKNOWN = "UNKNOWN"


class PlaceholderType(Enum):
    """Enumeration of possible placeholder types."""

    TITLE = "TITLE"
    BODY = "BODY"
    SUBTITLE = "SUBTITLE"
    CENTERED_TITLE = "CENTERED_TITLE"
    SLIDE_IMAGE = "SLIDE_IMAGE"
    UNKNOWN = "UNKNOWN"


class TextStyle(BaseModel):
    """Represents styling for text."""

    # We'll use Optional for all fields and only include them in the output if they're present in the original
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    strikethrough: Optional[bool] = None
    fontFamily: Optional[str] = None
    fontSize: Optional[Dict[str, Any]] = None  # Keep as dict to preserve original structure
    foregroundColor: Optional[Dict[str, Any]] = None
    link: Optional[Dict[str, str]] = None
    weightedFontFamily: Optional[Dict[str, Any]] = None
    baselineOffset: Optional[str] = None
    smallCaps: Optional[bool] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Only include fields that are not None
        return {k: v for k, v in self.model_dump(exclude_none=True).items()}


class ParagraphStyle(BaseModel):
    """Represents styling for paragraphs."""

    direction: str = "LEFT_TO_RIGHT"
    indentStart: Optional[Dict[str, Any]] = None
    indentFirstLine: Optional[Dict[str, Any]] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        return self.model_dump(exclude_none=True)


class BulletStyle(BaseModel):
    """Represents styling for bullets in lists."""

    glyph: Optional[str] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    fontFamily: Optional[str] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        return self.model_dump(exclude_none=True, exclude_defaults=True)


class ParagraphMarker(BaseModel):
    """Represents a paragraph marker with styling."""

    style: ParagraphStyle = Field(default_factory=ParagraphStyle)
    bullet: Optional[Dict[str, Any]] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {"style": self.style.to_api_format()}
        if self.bullet is not None:
            result["bullet"] = self.bullet
        return result


class TextRun(BaseModel):
    """Represents a run of text with consistent styling."""

    content: str
    style: TextStyle = Field(default_factory=TextStyle)

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        return {"content": self.content, "style": self.style.to_api_format()}


class TextElement(BaseModel):
    """Represents an element within text content."""

    endIndex: int
    startIndex: int = 0
    paragraphMarker: Optional[ParagraphMarker] = None
    textRun: Optional[TextRun] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {"endIndex": self.endIndex}

        if self.startIndex > 0:
            result["startIndex"] = self.startIndex

        if self.paragraphMarker is not None:
            result["paragraphMarker"] = self.paragraphMarker.to_api_format()

        if self.textRun is not None:
            result["textRun"] = self.textRun.to_api_format()

        return result


class Text(BaseModel):
    """Represents text content with its elements and lists."""

    textElements: List[TextElement]
    lists: Optional[Dict[str, Any]] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {"textElements": [element.to_api_format() for element in self.textElements]}

        if self.lists is not None:
            result["lists"] = self.lists

        return result


class ShapeProperties(BaseModel):
    """Represents properties of a shape."""

    shapeBackgroundFill: Optional[Dict[str, str]] = None
    outline: Optional[Dict[str, str]] = None
    shadow: Optional[Dict[str, str]] = None
    autofit: Optional[Dict[str, Any]] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        return self.model_dump(exclude_none=True)


class Placeholder(BaseModel):
    """Represents a placeholder in a slide."""

    type: PlaceholderType
    parentObjectId: str
    index: int = 0

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {"type": self.type.value, "parentObjectId": self.parentObjectId}

        if self.index != 0:
            result["index"] = self.index

        return result


class Shape(BaseModel):
    """Represents a shape in a slide."""

    # Use Dict[str, Any] to capture all fields from the original JSON
    model_config = {"extra": "allow"}

    shapeProperties: ShapeProperties
    shapeType: Optional[ShapeType] = None  # Make optional to preserve original JSON exactly
    text: Optional[Text] = None
    placeholder: Optional[Placeholder] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Start with a copy of any extra fields
        result = {
            k: v
            for k, v in self.__dict__.items()
            if k not in ["shapeProperties", "shapeType", "text", "placeholder"]
        }

        # Add the standard fields
        result["shapeProperties"] = self.shapeProperties.to_api_format()

        if self.shapeType is not None:
            result["shapeType"] = self.shapeType.value

        if self.text is not None:
            result["text"] = self.text.to_api_format()

        if self.placeholder is not None:
            result["placeholder"] = self.placeholder.to_api_format()

        return result


class Table(BaseModel):
    """Represents a table in a slide."""

    # Use Dict[str, Any] to capture all fields from the original JSON
    model_config = {"extra": "allow"}

    rows: Optional[int] = None
    columns: Optional[int] = None
    tableRows: Optional[List[Dict[str, Any]]] = None
    tableColumns: Optional[List[Dict[str, Any]]] = None
    horizontalBorderRows: Optional[List[Dict[str, Any]]] = None
    verticalBorderRows: Optional[List[Dict[str, Any]]] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Include all fields, including extra ones captured by model_config
        return self.model_dump(exclude_none=True)


class Image(BaseModel):
    """Represents an image in a slide."""

    # Use Dict[str, Any] to capture all fields from the original JSON
    model_config = {"extra": "allow"}

    contentUrl: Optional[str] = None
    imageProperties: Optional[Dict[str, Any]] = None
    sourceUrl: Optional[str] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Include all fields, including extra ones captured by model_config
        return self.model_dump(exclude_none=True)


class VideoSourceType(Enum):
    """Enumeration of possible video source types."""

    YOUTUBE = "YOUTUBE"
    DRIVE = "DRIVE"
    UNKNOWN = "UNKNOWN"


class VideoSource(BaseModel):
    """Represents a video source with type and optional ID."""

    type: VideoSourceType
    id: Optional[str] = None

    @classmethod
    def from_api_format(cls, data: Union[Dict[str, Any], str]) -> "VideoSource":
        """Create a VideoSource from API format."""
        if isinstance(data, str):
            # If it's just a string, assume it's the type
            return cls(type=VideoSourceType(data))
        elif isinstance(data, dict) and "type" in data:
            return cls(type=VideoSourceType(data["type"]), id=data.get("id"))
        raise ValueError(f"Cannot convert {data} to VideoSource")

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {"type": self.type.value}
        if self.id is not None:
            result["id"] = self.id
        return result


class Video(BaseModel):
    """Represents a video in a slide."""

    # Use Dict[str, Any] to capture all fields from the original JSON
    model_config = {"extra": "allow"}

    url: Optional[str] = None
    videoProperties: Optional[Dict[str, Any]] = None
    source: Optional[Union[Dict[str, Any], VideoSource, str]] = None
    id: Optional[str] = None

    @model_validator(mode="after")
    def convert_source(self) -> "Video":
        """Convert source to VideoSource if it's a dict or string."""
        if self.source is not None and not isinstance(self.source, VideoSource):
            # Track the original source type
            if isinstance(self.source, str):
                self._original_source_type = "str"
            elif isinstance(self.source, dict):
                self._original_source_type = "dict"
            else:
                self._original_source_type = type(self.source).__name__

            try:
                self.source = VideoSource.from_api_format(self.source)
            except (ValueError, TypeError):
                # Keep as is if conversion fails
                pass
        return self

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = self.model_dump(exclude={"source"}, exclude_none=True)

        if self.source is not None:
            if isinstance(self.source, VideoSource):
                # Special case: if the original source was a string, return it as a string
                if hasattr(self, "_original_source_type") and self._original_source_type == "str":
                    result["source"] = self.source.type.value
                else:
                    result["source"] = self.source.to_api_format()
            else:
                result["source"] = self.source

        return result


class PageElement(BaseModel):
    """Represents an element on a slide."""

    # Use Dict[str, Any] to capture all fields from the original JSON
    model_config = {"extra": "allow"}

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


class PageProperties(BaseModel):
    """Represents properties of a page."""

    pageBackgroundFill: Dict[str, Any]

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        return {"pageBackgroundFill": self.pageBackgroundFill}


class NotesProperties(BaseModel):
    """Represents properties of notes."""

    speakerNotesObjectId: str

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        return {"speakerNotesObjectId": self.speakerNotesObjectId}


class NotesPage(BaseModel):
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


class SlideProperties(BaseModel):
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
