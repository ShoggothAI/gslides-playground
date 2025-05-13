"""
Google Slides Templater
======================

A modern Python library for creating and filling Google Slides templates.
"""

__version__ = "0.1.0"

from gslides_templater.client import SlidesClient
from gslides_templater.auth import authenticate, Credentials

__all__ = ["SlidesClient", "authenticate", "Credentials"]