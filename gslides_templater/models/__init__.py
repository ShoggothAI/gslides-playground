# Импортируем базовые классы и перечисления
from gslides_templater.models.base import BaseModel, APIObject
from gslides_templater.models.enums import (
    ShapeType, ElementType, PlaceholderType,
    TextAlignment, ColorType, PageType
)

# Импортируем все необходимые модули сначала, но не классы
import gslides_templater.models.element
import gslides_templater.models.slide
import gslides_templater.models.presentation

# Теперь импортируем классы в правильном порядке
from gslides_templater.models.element import Element, Shape, Image, Table, TextBox, Video, Line, Group
from gslides_templater.models.slide import Slide, SlideProperties
from gslides_templater.models.presentation import Presentation

# В Pydantic 2.0 нам просто нужно вызвать model_rebuild для каждого класса
Element.model_rebuild()
Slide.model_rebuild()
Presentation.model_rebuild()
Shape.model_rebuild()
Image.model_rebuild()
Table.model_rebuild()
TextBox.model_rebuild()
Video.model_rebuild()
Line.model_rebuild()
Group.model_rebuild()

__all__ = [
    # Base models
    "BaseModel", "APIObject",

    # Enums
    "ShapeType", "ElementType", "PlaceholderType",
    "TextAlignment", "ColorType", "PageType",

    # Presentation models
    "Presentation",

    # Slide models
    "Slide", "SlideProperties",

    # Element models
    "Element", "Shape", "Image", "Table", "TextBox",
    "Video", "Line", "Group"
]