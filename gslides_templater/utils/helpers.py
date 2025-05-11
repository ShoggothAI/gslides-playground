"""
Helper functions for Google Slides Templater.
"""

import uuid
import re
from typing import Dict, Any, Optional, Tuple, Union, List


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID suitable for use in Google Slides API.

    Args:
        prefix: Optional prefix for the ID.

    Returns:
        A unique ID string.
    """
    uid = str(uuid.uuid4()).replace("-", "")
    return f"{prefix}{uid}"


def get_slide_position(slides: List[Dict[str, Any]], slide_id: str) -> Optional[int]:
    """
    Find the position of a slide in a presentation.

    Args:
        slides: List of slides in a presentation.
        slide_id: The ID of the slide to find.

    Returns:
        The index of the slide, or None if not found.
    """
    for i, slide in enumerate(slides):
        if slide.get("objectId") == slide_id:
            return i
    return None


def convert_unit(value: Union[int, float], from_unit: str, to_unit: str) -> float:
    """
    Convert between different units used in Google Slides.

    Supported units:
    - EMU (English Metric Unit): The base unit for the Slides API
    - PT (Point): 1/72 of an inch
    - PX (Pixel): Based on 96 DPI
    - IN (Inch)
    - CM (Centimeter)
    - MM (Millimeter)

    Args:
        value: The value to convert.
        from_unit: The source unit (EMU, PT, PX, IN, CM, MM).
        to_unit: The target unit (EMU, PT, PX, IN, CM, MM).

    Returns:
        The converted value.

    Raises:
        ValueError: If unsupported units are specified.
    """
    # Conversion to EMU (English Metric Unit, the base unit for Slides API)
    to_emu = {
        "EMU": lambda x: x,
        "PT": lambda x: x * 12700,  # 1 pt = 12700 EMU
        "PX": lambda x: x * 9525,  # 1 px = 9525 EMU (at 96 DPI)
        "IN": lambda x: x * 914400,  # 1 in = 914400 EMU
        "CM": lambda x: x * 360000,  # 1 cm = 360000 EMU
        "MM": lambda x: x * 36000,  # 1 mm = 36000 EMU
    }

    # Conversion from EMU to other units
    from_emu = {
        "EMU": lambda x: x,
        "PT": lambda x: x / 12700,
        "PX": lambda x: x / 9525,
        "IN": lambda x: x / 914400,
        "CM": lambda x: x / 360000,
        "MM": lambda x: x / 36000,
    }

    # Convert to uppercase for case-insensitive comparison
    from_unit = from_unit.upper()
    to_unit = to_unit.upper()

    # Validate units
    if from_unit not in to_emu or to_unit not in from_emu:
        valid_units = list(to_emu.keys())
        raise ValueError(f"Unsupported units. Valid units are: {valid_units}")

    # Convert to EMU first, then to the target unit
    emu_value = to_emu[from_unit](value)
    return from_emu[to_unit](emu_value)


def parse_color(color_str: str) -> Tuple[int, int, int]:
    """
    Parse a color string into RGB components.

    Supported formats:
    - Hex: #RGB, #RRGGBB
    - RGB: rgb(R, G, B)
    - Named colors: red, green, blue, etc.

    Args:
        color_str: The color string to parse.

    Returns:
        A tuple of (red, green, blue) values (0-255).

    Raises:
        ValueError: If the color string is invalid.
    """
    # Dictionary of named colors
    named_colors = {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
        "gray": (128, 128, 128),
        "grey": (128, 128, 128),
    }

    # Check for named colors
    color_str = color_str.lower().strip()
    if color_str in named_colors:
        return named_colors[color_str]

    # Check for hex format
    if color_str.startswith("#"):
        color_str = color_str[1:]  # Remove the # symbol

        if len(color_str) == 3:  # #RGB format
            r = int(color_str[0] + color_str[0], 16)
            g = int(color_str[1] + color_str[1], 16)
            b = int(color_str[2] + color_str[2], 16)
            return (r, g, b)

        elif len(color_str) == 6:  # #RRGGBB format
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            return (r, g, b)

    # Check for rgb() format
    rgb_match = re.match(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color_str)
    if rgb_match:
        r = int(rgb_match.group(1))
        g = int(rgb_match.group(2))
        b = int(rgb_match.group(3))
        return (r, g, b)

    # Invalid color format
    raise ValueError(f"Invalid color format: {color_str}")


def color_to_rgb(color: Union[str, Tuple[int, int, int]]) -> Dict[str, Any]:
    """
    Convert a color to the RGB format expected by the Google Slides API.

    Args:
        color: A color string or RGB tuple.

    Returns:
        A dictionary with the RGB color in the format expected by the API.
    """
    if isinstance(color, str):
        r, g, b = parse_color(color)
    else:
        r, g, b = color

    # The API expects RGB values in the range 0-1
    return {
        "rgbColor": {
            "red": r / 255.0,
            "green": g / 255.0,
            "blue": b / 255.0
        }
    }


def extract_placeholders(text: str) -> List[str]:
    """
    Extract placeholder variables from a text string.

    Placeholders are expected to be in the format {{variable_name}}.

    Args:
        text: The text to extract placeholders from.

    Returns:
        A list of placeholder variable names.
    """
    placeholder_pattern = r"{{([^{}]+)}}"
    return re.findall(placeholder_pattern, text)


def is_url(string: str) -> bool:
    """
    Check if a string is a valid URL.

    Args:
        string: The string to check.

    Returns:
        True if the string is a valid URL, False otherwise.
    """
    url_pattern = re.compile(
        r'^(?:http|https)://'  # http:// or https://
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?'  # domain
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return bool(url_pattern.match(string))


def is_image_url(url: str) -> bool:
    """
    Check if a URL points to an image.

    Args:
        url: The URL to check.

    Returns:
        True if the URL likely points to an image, False otherwise.
    """
    if not is_url(url):
        return False

    # Check if the URL has an image extension
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg')
    return url.lower().endswith(image_extensions)


def format_dimension(value: Union[int, float], unit: str = "PT") -> Dict[str, Any]:
    """
    Format a dimension value in the format expected by the Google Slides API.

    Args:
        value: The dimension value.
        unit: The unit of the dimension (e.g., "PT" for points).

    Returns:
        A dictionary with the dimension in the format expected by the API.
    """
    return {
        "magnitude": value,
        "unit": unit
    }
