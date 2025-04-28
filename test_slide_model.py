#!/usr/bin/env python3
"""
Test script to verify that the Slide class conforms to the Page data model.
"""

from gslides_api.slide import Page, SlideProperties, Layout
from gslides_api.domain import (
    PageProperties,
    PageBackgroundFill,
    PageType,
    MasterProperties,
    NotesProperties,
    ColorScheme,
    ThemeColorPair,
    ThemeColorType,
    RgbColor,
)

# Create a test slide with all the required properties
slide = Page(
    objectId="test-slide-id",
    slideProperties=SlideProperties(
        layoutObjectId="test-layout-id", masterObjectId="test-master-id"
    ),
    pageProperties=PageProperties(
        pageBackgroundFill=PageBackgroundFill(),
        colorScheme=ColorScheme(
            colors=[
                ThemeColorPair(
                    type=ThemeColorType.DARK1, color=RgbColor(red=0.0, green=0.0, blue=0.0)
                ),
                ThemeColorPair(
                    type=ThemeColorType.LIGHT1, color=RgbColor(red=1.0, green=1.0, blue=1.0)
                ),
            ]
        ),
    ),
    pageType=PageType.SLIDE,
    presentation_id="test-presentation-id",
)

# Create a test layout
layout = Layout(
    objectId="test-layout-id",
    layoutProperties={
        "masterObjectId": "test-master-id",
        "name": "Test Layout",
        "displayName": "Test Layout",
    },
    pageProperties=PageProperties(pageBackgroundFill=PageBackgroundFill()),
    presentation_id="test-presentation-id",
)

# Print the model_dump of the slide
print("Slide model_dump:")
slide_dump = slide.model_dump()
print(f"pageType in model_dump: {slide_dump.get('pageType')}")
print(f"presentation_id in model_dump: {'presentation_id' in slide_dump}")

# Print the to_api_format of the slide
print("\nSlide to_api_format:")
slide_api = slide.to_api_format()
print(f"pageType in to_api_format: {slide_api.get('pageType')}")
print(f"presentation_id in to_api_format: {'presentation_id' in slide_api}")

# Print the model_dump of the layout
print("\nLayout model_dump:")
layout_dump = layout.model_dump()
print(f"pageType in model_dump: {layout_dump.get('pageType')}")
print(f"layoutProperties in model_dump: {layout_dump.get('layoutProperties')}")

# Print the to_api_format of the layout
print("\nLayout to_api_format:")
layout_api = layout.to_api_format()
print(f"pageType in to_api_format: {layout_api.get('pageType')}")
print(f"layoutProperties in to_api_format: {layout_api.get('layoutProperties')}")
