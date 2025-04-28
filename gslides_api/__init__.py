from .domain import (
    Size,
    Dimension,
    TextElement,
    Video,
    VideoSourceType,
    RgbColor,
    Color,
    ThemeColorType,
    SolidFill,
    ShapeBackgroundFill,
    OutlineFill,
    Weight,
    Outline,
    DashStyle,
    ShadowTransform,
    BlurRadius,
    Shadow,
    ShadowType,
    RectanglePosition,
    ShapeProperties,
    CropProperties,
    ColorStop,
    RecolorName,
    Recolor,
    ImageProperties,
    PropertyState,
    StretchedPictureFill,
    PageBackgroundFill,
    AutoText,
    AutoTextType,
    MasterProperties,
    NotesProperties,
    PageType,
    ColorScheme,
    ThemeColorPair,
)
from .presentation import Presentation
from .page import Page, LayoutProperties, SlidePageProperties
from .credentials import initialize_credentials

# Import SlidePageProperties as PageProperties for backward compatibility
PageProperties = SlidePageProperties
