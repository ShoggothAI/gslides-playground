"""
Google Slides Templater
"""

from .core import SlidesTemplater, create_templater
from .markdown_processor import (
    MarkdownProcessor,
    markdown_to_slides_elements,
    slides_elements_to_markdown,
    clean_markdown_for_slides
)
from .auth import (
    authenticate,
    CredentialManager,
    Credentials,
    setup_oauth_flow,
    validate_credentials,
    get_credentials_info,
    create_service_account_template,
    create_oauth_template,
    check_credentials_file
)


__all__ = [
    'SlidesTemplater',
    'MarkdownProcessor',
    'CredentialManager',
    'Credentials',
    'create_templater',
    'authenticate',
    'setup_oauth_flow',
    'markdown_to_slides_elements',
    'slides_elements_to_markdown',
    'clean_markdown_for_slides',
    'validate_credentials',
    'get_credentials_info',
    'create_service_account_template',
    'create_oauth_template',
    'check_credentials_file',
]