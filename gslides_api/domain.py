from typing import List, Dict, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from pydantic.json import pydantic_encoder


class GSlidesBaseModel(BaseModel):
    """Base class for all models in the Google Slides API."""

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        return super().model_dump(exclude_none=True)


class SizeWithUnit(GSlidesBaseModel):
    """Represents a size dimension with magnitude and unit."""

    magnitude: float
    unit: str = "EMU"  # Engineering Measurement Unit

    @classmethod
    def from_api_format(cls, data: Dict[str, Any]) -> "SizeWithUnit":
        """Create a SizeWithUnit from API format."""
        if isinstance(data, dict) and "magnitude" in data:
            return cls(magnitude=data["magnitude"], unit=data.get("unit", "EMU"))
        # If it's just a number, assume it's the magnitude
        if isinstance(data, (int, float)):
            return cls(magnitude=data)
        raise ValueError(f"Cannot convert {data} to SizeWithUnit")


class Size(GSlidesBaseModel):
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


class Transform(GSlidesBaseModel):
    """Represents a transformation applied to an element."""

    translateX: float
    translateY: float
    scaleX: float
    scaleY: float
    unit: Optional[str] = None  # Make optional to preserve original JSON exactly


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


class TextStyle(GSlidesBaseModel):
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


class ParagraphStyle(GSlidesBaseModel):
    """Represents styling for paragraphs."""

    direction: str = "LEFT_TO_RIGHT"
    indentStart: Optional[Dict[str, Any]] = None
    indentFirstLine: Optional[Dict[str, Any]] = None


class BulletStyle(GSlidesBaseModel):
    """Represents styling for bullets in lists."""

    glyph: Optional[str] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    fontFamily: Optional[str] = None


class ParagraphMarker(GSlidesBaseModel):
    """Represents a paragraph marker with styling."""

    style: ParagraphStyle = Field(default_factory=ParagraphStyle)
    bullet: Optional[Dict[str, Any]] = None


class TextRun(GSlidesBaseModel):
    """Represents a run of text with consistent styling."""

    content: str
    style: TextStyle = Field(default_factory=TextStyle)


class TextElement(GSlidesBaseModel):
    """Represents an element within text content."""

    endIndex: int
    startIndex: Optional[int] = None
    paragraphMarker: Optional[ParagraphMarker] = None
    textRun: Optional[TextRun] = None


class Text(GSlidesBaseModel):
    """Represents text content with its elements and lists."""

    textElements: List[TextElement]
    lists: Optional[Dict[str, Any]] = None


class RgbColor(GSlidesBaseModel):
    """Represents an RGB color."""

    red: Optional[float] = None
    green: Optional[float] = None
    blue: Optional[float] = None


class Color(GSlidesBaseModel):
    """Represents a color with RGB values."""

    rgbColor: Optional[RgbColor] = None


class SolidFill(GSlidesBaseModel):
    """Represents a solid fill with color and alpha."""

    color: Optional[Color] = None
    alpha: Optional[float] = None


class ShapeBackgroundFill(GSlidesBaseModel):
    """Represents the background fill of a shape."""

    solidFill: Optional[SolidFill] = None
    propertyState: Optional[str] = None


class OutlineFill(GSlidesBaseModel):
    """Represents the fill of an outline."""

    solidFill: Optional[SolidFill] = None


class Weight(GSlidesBaseModel):
    """Represents the weight of an outline."""

    magnitude: Optional[float] = None
    unit: Optional[str] = None


class Outline(GSlidesBaseModel):
    """Represents an outline of a shape."""

    outlineFill: Optional[OutlineFill] = None
    weight: Optional[Weight] = None
    propertyState: Optional[str] = None


class ShadowTransform(GSlidesBaseModel):
    """Represents a shadow transform."""

    scaleX: Optional[float] = None
    scaleY: Optional[float] = None
    unit: Optional[str] = None


class BlurRadius(GSlidesBaseModel):
    """Represents a blur radius."""

    magnitude: Optional[float] = None
    unit: Optional[str] = None


class Shadow(GSlidesBaseModel):
    """Represents a shadow."""

    transform: Optional[ShadowTransform] = None
    blurRadius: Optional[BlurRadius] = None
    color: Optional[Color] = None
    alpha: Optional[float] = None
    rotateWithShape: Optional[bool] = None
    propertyState: Optional[str] = None


class ShapeProperties(GSlidesBaseModel):
    """Represents properties of a shape."""

    shapeBackgroundFill: Optional[ShapeBackgroundFill] = None
    outline: Optional[Outline] = None
    shadow: Optional[Shadow] = None
    autofit: Optional[Dict[str, Any]] = None


class Placeholder(GSlidesBaseModel):
    """Represents a placeholder in a slide."""

    type: PlaceholderType
    parentObjectId: str
    index: Optional[int] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {"type": self.type.value, "parentObjectId": self.parentObjectId}

        if self.index is not None:
            result["index"] = self.index

        return result


class Shape(GSlidesBaseModel):
    """Represents a shape in a slide."""

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


class Table(GSlidesBaseModel):
    """Represents a table in a slide."""

    rows: Optional[int] = None
    columns: Optional[int] = None
    tableRows: Optional[List[Dict[str, Any]]] = None
    tableColumns: Optional[List[Dict[str, Any]]] = None
    horizontalBorderRows: Optional[List[Dict[str, Any]]] = None
    verticalBorderRows: Optional[List[Dict[str, Any]]] = None


class Image(GSlidesBaseModel):
    """Represents an image in a slide."""

    contentUrl: Optional[str] = None
    imageProperties: Optional[Dict[str, Any]] = None
    sourceUrl: Optional[str] = None


class VideoSourceType(Enum):
    """Enumeration of possible video source types."""

    YOUTUBE = "YOUTUBE"
    DRIVE = "DRIVE"
    UNKNOWN = "UNKNOWN"


class VideoSource(GSlidesBaseModel):
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


class Video(GSlidesBaseModel):
    """Represents a video in a slide."""

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
        result = super().model_dump(exclude={"source"}, exclude_none=True)

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


class PageProperties(GSlidesBaseModel):
    """Represents properties of a page."""

    pageBackgroundFill: Dict[str, Any]


class NotesProperties(GSlidesBaseModel):
    """Represents properties of notes."""

    speakerNotesObjectId: str


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
