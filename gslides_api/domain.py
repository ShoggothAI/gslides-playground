from typing import List, Dict, Optional, Any, Union
from enum import Enum
import json
from pydantic import BaseModel, Field, model_validator
from pydantic.json import pydantic_encoder

# from gslides_api.notes import NotesPage


class EnumEncoder(json.JSONEncoder):
    """JSON encoder that handles Enum types."""

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


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
    SLIDE_NUMBER = "SLIDE_NUMBER"
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


class ThemeColorType(Enum):
    """Enumeration of possible theme color types."""

    THEME_COLOR_TYPE_UNSPECIFIED = "THEME_COLOR_TYPE_UNSPECIFIED"
    DARK1 = "DARK1"
    LIGHT1 = "LIGHT1"
    DARK2 = "DARK2"
    LIGHT2 = "LIGHT2"
    ACCENT1 = "ACCENT1"
    ACCENT2 = "ACCENT2"
    ACCENT3 = "ACCENT3"
    ACCENT4 = "ACCENT4"
    ACCENT5 = "ACCENT5"
    ACCENT6 = "ACCENT6"
    HYPERLINK = "HYPERLINK"
    FOLLOWED_HYPERLINK = "FOLLOWED_HYPERLINK"
    TEXT1 = "TEXT1"
    BACKGROUND1 = "BACKGROUND1"
    TEXT2 = "TEXT2"
    BACKGROUND2 = "BACKGROUND2"


class Color(GSlidesBaseModel):
    """Represents a color with RGB values."""

    rgbColor: Optional[RgbColor] = None
    themeColor: Optional[ThemeColorType] = None

    @classmethod
    def from_api_format(cls, data: Dict[str, Any]) -> "Color":
        """Create a Color from API format."""
        if "rgbColor" in data:
            rgb_color = (
                RgbColor(**data["rgbColor"])
                if isinstance(data["rgbColor"], dict)
                else data["rgbColor"]
            )
            theme_color = None
            if "themeColor" in data:
                try:
                    theme_color = ThemeColorType(data["themeColor"])
                except (ValueError, TypeError):
                    # Keep as is if conversion fails
                    theme_color = data["themeColor"]
            return cls(rgbColor=rgb_color, themeColor=theme_color)
        elif "themeColor" in data:
            try:
                theme_color = ThemeColorType(data["themeColor"])
            except (ValueError, TypeError):
                # Keep as is if conversion fails
                theme_color = data["themeColor"]
            return cls(themeColor=theme_color)
        return cls()

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {}

        if self.rgbColor is not None:
            result["rgbColor"] = self.rgbColor.to_api_format()

        if self.themeColor is not None:
            result["themeColor"] = self.themeColor.value

        return result


class SolidFill(GSlidesBaseModel):
    """Represents a solid fill with color and alpha."""

    color: Optional[Color] = None
    alpha: Optional[float] = None

    @classmethod
    def from_api_format(cls, data: Dict[str, Any]) -> "SolidFill":
        """Create a SolidFill from API format."""
        color = None
        if "color" in data and isinstance(data["color"], dict):
            if "rgbColor" in data["color"] or "themeColor" in data["color"]:
                color = Color.from_api_format(data["color"])
            else:
                color = Color(**data["color"])

        return cls(color=color, alpha=data.get("alpha"))

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {}

        if self.color is not None:
            result["color"] = self.color.to_api_format()

        if self.alpha is not None:
            result["alpha"] = self.alpha

        return result


class ShapeBackgroundFill(GSlidesBaseModel):
    """Represents the background fill of a shape."""

    solidFill: Optional[SolidFill] = None
    propertyState: Optional[str] = None


class OutlineFill(GSlidesBaseModel):
    """Represents the fill of an outline."""

    solidFill: Optional[SolidFill] = None

    @classmethod
    def from_api_format(cls, data: Dict[str, Any]) -> "OutlineFill":
        """Create an OutlineFill from API format."""
        if "solidFill" in data and isinstance(data["solidFill"], dict):
            solid_fill = SolidFill(**data["solidFill"])
            return cls(solidFill=solid_fill)
        return cls()

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {}

        if self.solidFill is not None:
            result["solidFill"] = self.solidFill.to_api_format()

        return result


class Weight(GSlidesBaseModel):
    """Represents the weight of an outline."""

    magnitude: Optional[float] = None
    unit: Optional[str] = None


class DashStyle(Enum):
    """Enumeration of possible dash styles for outlines."""

    DASH_STYLE_UNSPECIFIED = "DASH_STYLE_UNSPECIFIED"
    SOLID = "SOLID"
    DOT = "DOT"
    DASH = "DASH"
    DASH_DOT = "DASH_DOT"
    LONG_DASH = "LONG_DASH"
    LONG_DASH_DOT = "LONG_DASH_DOT"


class Outline(GSlidesBaseModel):
    """Represents an outline of a shape."""

    outlineFill: Optional[OutlineFill] = None
    weight: Optional[Weight] = None
    propertyState: Optional[str] = None
    dashStyle: Optional[DashStyle] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = super().model_dump(
            exclude={"outlineFill", "weight", "dashStyle"}, exclude_none=True
        )

        if self.outlineFill is not None:
            result["outlineFill"] = self.outlineFill.to_api_format()

        if self.weight is not None:
            result["weight"] = (
                self.weight.to_api_format()
                if hasattr(self.weight, "to_api_format")
                else self.weight
            )

        if self.dashStyle is not None:
            result["dashStyle"] = self.dashStyle.value

        return result


class ShadowTransform(GSlidesBaseModel):
    """Represents a shadow transform."""

    scaleX: Optional[float] = None
    scaleY: Optional[float] = None
    unit: Optional[str] = None


class BlurRadius(GSlidesBaseModel):
    """Represents a blur radius."""

    magnitude: Optional[float] = None
    unit: Optional[str] = None


class ShadowType(Enum):
    """Enumeration of possible shadow types."""

    SHADOW_TYPE_UNSPECIFIED = "SHADOW_TYPE_UNSPECIFIED"
    OUTER = "OUTER"


class RectanglePosition(Enum):
    """Enumeration of possible rectangle positions."""

    RECTANGLE_POSITION_UNSPECIFIED = "RECTANGLE_POSITION_UNSPECIFIED"
    TOP_LEFT = "TOP_LEFT"
    TOP_CENTER = "TOP_CENTER"
    TOP_RIGHT = "TOP_RIGHT"
    LEFT_CENTER = "LEFT_CENTER"
    CENTER = "CENTER"
    RIGHT_CENTER = "RIGHT_CENTER"
    BOTTOM_LEFT = "BOTTOM_LEFT"
    BOTTOM_CENTER = "BOTTOM_CENTER"
    BOTTOM_RIGHT = "BOTTOM_RIGHT"


class Shadow(GSlidesBaseModel):
    """Represents a shadow."""

    transform: Optional[ShadowTransform] = None
    blurRadius: Optional[BlurRadius] = None
    color: Optional[Color] = None
    alpha: Optional[float] = None
    rotateWithShape: Optional[bool] = None
    propertyState: Optional[str] = None
    type: Optional[ShadowType] = None
    alignment: Optional[RectanglePosition] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = super().model_dump(
            exclude={"transform", "blurRadius", "color", "type", "alignment"}, exclude_none=True
        )

        if self.transform is not None:
            result["transform"] = self.transform.to_api_format()

        if self.blurRadius is not None:
            result["blurRadius"] = (
                self.blurRadius.to_api_format()
                if hasattr(self.blurRadius, "to_api_format")
                else self.blurRadius
            )

        if self.color is not None:
            result["color"] = self.color.to_api_format()

        if self.type is not None:
            result["type"] = self.type.value

        if self.alignment is not None:
            result["alignment"] = self.alignment.value

        return result


class ShapeProperties(GSlidesBaseModel):
    """Represents properties of a shape."""

    shapeBackgroundFill: Optional[ShapeBackgroundFill] = None
    outline: Optional[Outline] = None
    shadow: Optional[Shadow] = None
    autofit: Optional[Dict[str, Any]] = None


class Placeholder(GSlidesBaseModel):
    """Represents a placeholder in a slide."""

    type: PlaceholderType
    parentObjectId: Optional[str] = None
    index: Optional[int] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {"type": self.type.value}

        if self.parentObjectId is not None:
            result["parentObjectId"] = self.parentObjectId

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


class CropProperties(GSlidesBaseModel):
    """Represents crop properties of an image."""

    leftOffset: Optional[float] = None
    rightOffset: Optional[float] = None
    topOffset: Optional[float] = None
    bottomOffset: Optional[float] = None
    angle: Optional[float] = None


class ColorStop(GSlidesBaseModel):
    """Represents a color and position in a gradient."""

    color: Optional[Color] = None
    alpha: Optional[float] = 1.0
    position: Optional[float] = None


class RecolorName(Enum):
    """Enumeration of possible recolor effect names."""

    NONE = "NONE"
    LIGHT1 = "LIGHT1"
    LIGHT2 = "LIGHT2"
    LIGHT3 = "LIGHT3"
    LIGHT4 = "LIGHT4"
    LIGHT5 = "LIGHT5"
    LIGHT6 = "LIGHT6"
    LIGHT7 = "LIGHT7"
    LIGHT8 = "LIGHT8"
    LIGHT9 = "LIGHT9"
    LIGHT10 = "LIGHT10"
    DARK1 = "DARK1"
    DARK2 = "DARK2"
    DARK3 = "DARK3"
    DARK4 = "DARK4"
    DARK5 = "DARK5"
    DARK6 = "DARK6"
    DARK7 = "DARK7"
    DARK8 = "DARK8"
    DARK9 = "DARK9"
    DARK10 = "DARK10"
    GRAYSCALE = "GRAYSCALE"
    NEGATIVE = "NEGATIVE"
    SEPIA = "SEPIA"
    CUSTOM = "CUSTOM"


class Recolor(GSlidesBaseModel):
    """Represents a recolor effect applied to an image."""

    recolorStops: Optional[List[ColorStop]] = None
    name: Optional[RecolorName] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {}

        if self.recolorStops is not None:
            result["recolorStops"] = [stop.to_api_format() for stop in self.recolorStops]

        if self.name is not None:
            result["name"] = self.name.value

        return result


class ImageProperties(GSlidesBaseModel):
    """Represents properties of an image."""

    cropProperties: Optional[CropProperties] = None
    transparency: Optional[float] = None
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    recolor: Optional[Recolor] = None
    outline: Optional[Outline] = None
    shadow: Optional[Shadow] = None
    link: Optional[Dict[str, Any]] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = super().model_dump(
            exclude={"cropProperties", "recolor", "outline", "shadow"}, exclude_none=True
        )

        if self.cropProperties is not None:
            result["cropProperties"] = self.cropProperties.to_api_format()

        if self.recolor is not None:
            result["recolor"] = self.recolor.to_api_format()

        if self.outline is not None:
            result["outline"] = self.outline.to_api_format()

        if self.shadow is not None:
            result["shadow"] = self.shadow.to_api_format()

        return result


class Image(GSlidesBaseModel):
    """Represents an image in a slide."""

    contentUrl: Optional[str] = None
    imageProperties: Optional[Union[Dict[str, Any], ImageProperties]] = None
    sourceUrl: Optional[str] = None

    @model_validator(mode="after")
    def convert_image_properties(self) -> "Image":
        """Convert imageProperties to ImageProperties if it's a dict."""
        if self.imageProperties is not None and not isinstance(
            self.imageProperties, ImageProperties
        ):
            # Track the original type
            if isinstance(self.imageProperties, dict):
                self._original_properties_type = "dict"
            else:
                self._original_properties_type = type(self.imageProperties).__name__

            try:
                self.imageProperties = ImageProperties.model_validate(self.imageProperties)
            except (ValueError, TypeError):
                # Keep as is if conversion fails
                pass
        return self

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = super().model_dump(exclude={"imageProperties"}, exclude_none=True)

        if self.imageProperties is not None:
            if isinstance(self.imageProperties, ImageProperties):
                result["imageProperties"] = self.imageProperties.to_api_format()
            else:
                result["imageProperties"] = self.imageProperties

        return result


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


class PropertyState(Enum):
    """The possible states of a property."""

    RENDERED = "RENDERED"
    NOT_RENDERED = "NOT_RENDERED"
    INHERIT = "INHERIT"


class StretchedPictureFill(GSlidesBaseModel):
    """Represents a stretched picture fill for a page background."""

    contentUrl: str
    size: Optional[Size] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {"contentUrl": self.contentUrl}

        if self.size is not None:
            result["size"] = self.size.to_api_format()

        return result


class PageBackgroundFill(GSlidesBaseModel):
    """Represents the background fill of a page."""

    propertyState: Optional[PropertyState] = None
    solidFill: Optional[SolidFill] = None
    stretchedPictureFill: Optional[StretchedPictureFill] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {}

        if self.propertyState is not None:
            result["propertyState"] = self.propertyState.value

        if self.solidFill is not None:
            result["solidFill"] = self.solidFill.to_api_format()

        if self.stretchedPictureFill is not None:
            result["stretchedPictureFill"] = self.stretchedPictureFill.to_api_format()

        return result


class PageProperties(GSlidesBaseModel):
    """Represents properties of a page."""

    pageBackgroundFill: Optional[PageBackgroundFill] = None
    colorScheme: Optional[Dict[str, Any]] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        result = {}

        if self.pageBackgroundFill is not None:
            result["pageBackgroundFill"] = self.pageBackgroundFill.to_api_format()

        if self.colorScheme is not None:
            result["colorScheme"] = self.colorScheme

        return result


class NotesProperties(GSlidesBaseModel):
    """Represents properties of notes."""

    speakerNotesObjectId: str
