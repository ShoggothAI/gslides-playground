"""
Markdown processing module for Google Slides Templater.
Provides conversion between Markdown and Google Slides formats.
"""

import html
import re
from typing import List, Dict, Any, Tuple

try:
    import markdown

    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


class MarkdownProcessor:
    """
    Processor for converting Markdown to Google Slides format and vice versa.

    Supports:
    - Headers (# ## ###)
    - Bold and italic text
    - Strikethrough text
    - Code (inline and blocks)
    - Lists
    - Links and images
    - Quotes
    """

    def __init__(self):
        """Initialize processor with default settings."""
        self.header_sizes = {
            1: 36,
            2: 28,
            3: 24,
            4: 20,
            5: 18,
            6: 16
        }

        if MARKDOWN_AVAILABLE:
            self.md = markdown.Markdown(
                extensions=['extra', 'codehilite', 'tables', 'fenced_code', 'nl2br'],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight',
                        'use_pygments': False
                    }
                }
            )
        else:
            self.md = None

    def is_markdown(self, text: str) -> bool:
        """
        Check if text contains Markdown markup.

        Args:
            text: Text to check

        Returns:
            True if text contains Markdown formatting
        """
        if not text or not text.strip():
            return False

        markdown_patterns = [
            r'^#{1,6}\s+',
            r'\*\*[^*]+\*\*',
            r'(?<!\*)\*[^*]+\*(?!\*)',
            r'`[^`]+`',
            r'```[\s\S]*?```',
            r'^\s*[-*+]\s+',
            r'^\s*\d+\.\s+',
            r'\[([^\]]+)\]\([^)]+\)',
            r'!\[([^\]]*)\]\([^)]+\)',
            r'~~[^~]+~~',
            r'^\s*>\s+',
            r'^\s*\|.*\|',
            r'^---+$',
        ]

        return any(re.search(pattern, text, re.MULTILINE) for pattern in markdown_patterns)

    def markdown_to_slides_elements(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Convert Markdown to Google Slides elements.

        Args:
            markdown_text: Source Markdown text

        Returns:
            List of elements for Google Slides API
        """
        if not markdown_text:
            return []

        elements = []
        lines = markdown_text.split('\n')

        for line_idx, line in enumerate(lines):
            if not line.strip():
                if line_idx > 0:
                    elements.append({
                        "textRun": {
                            "content": "\n",
                            "style": {}
                        }
                    })
                continue

            line_elements = self._process_markdown_line(line)
            elements.extend(line_elements)

            if line_idx < len(lines) - 1:
                elements.append({
                    "textRun": {
                        "content": "\n",
                        "style": {}
                    }
                })

        return elements

    def slides_elements_to_markdown(self, elements: List[Dict[str, Any]]) -> str:
        """
        Convert Google Slides elements back to Markdown.

        Args:
            elements: List of elements from Google Slides API

        Returns:
            Markdown text
        """
        if not elements:
            return ""

        markdown_parts = []

        for element in elements:
            if "textRun" in element:
                text_run = element["textRun"]
                content = text_run.get("content", "")
                style = text_run.get("style", {})

                formatted_content = self._style_to_markdown(content, style)
                markdown_parts.append(formatted_content)

            elif "paragraphMarker" in element:
                if markdown_parts and not markdown_parts[-1].endswith("\n"):
                    markdown_parts.append("\n")

        return "".join(markdown_parts)

    def create_slides_requests(self, element_id: str, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Create requests for Google Slides API from Markdown text.
        Uses a simple approach: insert clean text, then apply formatting.

        Args:
            element_id: Element ID for text insertion
            markdown_text: Markdown text

        Returns:
            List of requests for batch update
        """
        requests = []

        if not markdown_text.strip():
            return requests

        # Step 1: Clean the text from Markdown symbols
        clean_text = self._clean_markdown_text(markdown_text)

        # Step 2: Insert clean text
        requests.append({
            "insertText": {
                "objectId": element_id,
                "insertionIndex": 0,
                "text": clean_text
            }
        })

        # Step 3: Apply formatting to the clean text
        if self.is_markdown(markdown_text):
            formatting_requests = self._apply_markdown_formatting(element_id, markdown_text, clean_text)
            requests.extend(formatting_requests)

        return requests

    def _clean_markdown_text(self, markdown_text: str) -> str:
        """
        Remove Markdown formatting symbols and return clean text.

        Args:
            markdown_text: Original Markdown text

        Returns:
            Clean text without Markdown symbols
        """
        clean_text = markdown_text

        # Remove header symbols
        clean_text = re.sub(r'^#{1,6}\s+', '', clean_text, flags=re.MULTILINE)

        # Remove bold formatting
        clean_text = re.sub(r'\*\*([^*]+?)\*\*', r'\1', clean_text)

        # Remove italic formatting
        clean_text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', clean_text)

        # Remove strikethrough
        clean_text = re.sub(r'~~([^~]+?)~~', r'\1', clean_text)

        # Remove code formatting
        clean_text = re.sub(r'`([^`]+?)`', r'\1', clean_text)

        return clean_text.strip()

    def _apply_markdown_formatting(self, element_id: str, original_markdown: str, clean_text: str) -> List[
        Dict[str, Any]]:
        """
        Apply formatting to clean text based on original Markdown.

        Args:
            element_id: Element ID for formatting
            original_markdown: Original Markdown text
            clean_text: Clean text without Markdown symbols

        Returns:
            List of formatting requests
        """
        requests = []

        # Handle headers first
        header_match = re.match(r'^(#{1,6})\s+(.+)', original_markdown.strip())
        if header_match:
            level = len(header_match.group(1))
            header_text = header_match.group(2)

            # Find where this text appears in clean text
            clean_header = self._clean_markdown_text(header_text)
            start_index = clean_text.find(clean_header)

            if start_index >= 0:
                requests.append({
                    "updateTextStyle": {
                        "objectId": element_id,
                        "style": {
                            "fontSize": {"magnitude": self.header_sizes.get(level, 16), "unit": "PT"},
                            "bold": True
                        },
                        "fields": "fontSize,bold",
                        "textRange": {
                            "type": "FIXED_RANGE",
                            "startIndex": start_index,
                            "endIndex": start_index + len(clean_header)
                        }
                    }
                })
            return requests

        # Handle inline formatting
        current_offset = 0

        # Bold text
        for match in re.finditer(r'\*\*([^*]+?)\*\*', original_markdown):
            bold_text = match.group(1)
            clean_bold = self._clean_markdown_text(bold_text)

            # Find position in clean text
            start_pos = clean_text.find(clean_bold, current_offset)
            if start_pos >= 0:
                requests.append({
                    "updateTextStyle": {
                        "objectId": element_id,
                        "style": {"bold": True},
                        "fields": "bold",
                        "textRange": {
                            "type": "FIXED_RANGE",
                            "startIndex": start_pos,
                            "endIndex": start_pos + len(clean_bold)
                        }
                    }
                })
                current_offset = start_pos + len(clean_bold)

        # Reset offset for italic
        current_offset = 0

        # Italic text (avoid double-processing bold+italic)
        for match in re.finditer(r'(?<!\*)\*([^*]+?)\*(?!\*)', original_markdown):
            italic_text = match.group(1)
            clean_italic = self._clean_markdown_text(italic_text)

            start_pos = clean_text.find(clean_italic, current_offset)
            if start_pos >= 0:
                requests.append({
                    "updateTextStyle": {
                        "objectId": element_id,
                        "style": {"italic": True},
                        "fields": "italic",
                        "textRange": {
                            "type": "FIXED_RANGE",
                            "startIndex": start_pos,
                            "endIndex": start_pos + len(clean_italic)
                        }
                    }
                })
                current_offset = start_pos + len(clean_italic)

        # Reset offset for strikethrough
        current_offset = 0

        # Strikethrough text
        for match in re.finditer(r'~~([^~]+?)~~', original_markdown):
            strike_text = match.group(1)
            clean_strike = self._clean_markdown_text(strike_text)

            start_pos = clean_text.find(clean_strike, current_offset)
            if start_pos >= 0:
                requests.append({
                    "updateTextStyle": {
                        "objectId": element_id,
                        "style": {"strikethrough": True},
                        "fields": "strikethrough",
                        "textRange": {
                            "type": "FIXED_RANGE",
                            "startIndex": start_pos,
                            "endIndex": start_pos + len(clean_strike)
                        }
                    }
                })
                current_offset = start_pos + len(clean_strike)

        # Reset offset for code
        current_offset = 0

        # Code formatting
        for match in re.finditer(r'`([^`]+?)`', original_markdown):
            code_text = match.group(1)

            start_pos = clean_text.find(code_text, current_offset)
            if start_pos >= 0:
                requests.append({
                    "updateTextStyle": {
                        "objectId": element_id,
                        "style": {
                            "fontFamily": "Courier New",
                            "foregroundColor": {"rgbColor": {"red": 0.8, "green": 0.2, "blue": 0.2}}
                        },
                        "fields": "fontFamily,foregroundColor",
                        "textRange": {
                            "type": "FIXED_RANGE",
                            "startIndex": start_pos,
                            "endIndex": start_pos + len(code_text)
                        }
                    }
                })
                current_offset = start_pos + len(code_text)

        return requests

    def parse_to_components(self, markdown_content: str) -> List[Dict[str, Any]]:
        """
        Parse Markdown into components for slide creation.

        Args:
            markdown_content: Markdown content

        Returns:
            List of components (headers, text, images)
        """
        components = []
        lines = markdown_content.split('\n')
        current_text = []

        for line in lines:
            line = line.strip()

            if not line:
                if current_text:
                    components.append({
                        'type': 'text',
                        'content': '\n'.join(current_text)
                    })
                    current_text = []
                continue

            header_match = re.match(r'^(#{1,6})\s*(.+)', line)
            if header_match:
                if current_text:
                    components.append({
                        'type': 'text',
                        'content': '\n'.join(current_text)
                    })
                    current_text = []

                level = len(header_match.group(1))
                content = header_match.group(2)
                components.append({
                    'type': 'header',
                    'level': level,
                    'content': f"{'#' * level} {content}"
                })
                continue

            image_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line)
            if image_match:
                if current_text:
                    components.append({
                        'type': 'text',
                        'content': '\n'.join(current_text)
                    })
                    current_text = []

                alt_text = image_match.group(1)
                url = image_match.group(2)
                components.append({
                    'type': 'image',
                    'alt': alt_text,
                    'url': url
                })
                continue

            current_text.append(line)

        if current_text:
            components.append({
                'type': 'text',
                'content': '\n'.join(current_text)
            })

        return components

    def clean_text_for_slides(self, text: str) -> str:
        """
        Clean text for use in Google Slides.
        Removes complex markup, leaving only supported elements.

        Args:
            text: Source text (may contain Markdown or HTML)

        Returns:
            Cleaned text suitable for Google Slides
        """
        if not text:
            return ""

        if self.is_markdown(text):
            clean_text = text

            clean_text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', clean_text)
            clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)
            clean_text = re.sub(r'```[\s\S]*?```', '[Code Block]', clean_text)
            clean_text = re.sub(r'`([^`]+)`', r'\1', clean_text)

            clean_text = re.sub(r'^\s*[-*+]\s+', '• ', clean_text, flags=re.MULTILINE)
            clean_text = re.sub(r'^\s*\d+\.\s+', '• ', clean_text, flags=re.MULTILINE)

            clean_text = re.sub(r'^\s*>\s+', '', clean_text, flags=re.MULTILINE)

            return clean_text.strip()

        if '<' in text and '>' in text:
            clean_text = re.sub('<[^>]+>', '', text)
            return html.unescape(clean_text).strip()

        return text.strip()

    def validate_markdown(self, markdown_text: str) -> List[str]:
        """
        Validate Markdown text for common formatting issues.

        Args:
            markdown_text: Markdown text to check

        Returns:
            List of found issues (empty list if no issues)
        """
        issues = []

        if not markdown_text:
            return issues

        bold_count = len(re.findall(r'\*\*', markdown_text))
        if bold_count % 2 != 0:
            issues.append("Unclosed bold formatting (**)")

        italic_count = len(re.findall(r'(?<!\*)\*(?!\*)', markdown_text))
        if italic_count % 2 != 0:
            issues.append("Unclosed italic formatting (*)")

        strikethrough_count = len(re.findall(r'~~', markdown_text))
        if strikethrough_count % 2 != 0:
            issues.append("Unclosed strikethrough (~~)")

        code_count = len(re.findall(r'(?<!`)`(?!`)', markdown_text))
        if code_count % 2 != 0:
            issues.append("Unclosed inline code (`)")

        broken_links = re.findall(r'\[[^\]]*\]\([^)]*$', markdown_text)
        if broken_links:
            issues.append("Unclosed links")

        broken_images = re.findall(r'!\[[^\]]*\]\([^)]*$', markdown_text)
        if broken_images:
            issues.append("Unclosed images")

        return issues

    def extract_images(self, markdown_text: str) -> List[Dict[str, str]]:
        """
        Extract images from Markdown text.

        Args:
            markdown_text: Markdown text

        Returns:
            List of dictionaries with image information
        """
        if not markdown_text:
            return []

        images = []

        image_pattern = r'!\[([^\]]*)\]\(([^)]+)(?:\s+"([^"]*)")?\)'

        for match in re.finditer(image_pattern, markdown_text):
            alt_text = match.group(1) or ""
            url = match.group(2)
            title = match.group(3) or ""

            images.append({
                'alt': alt_text,
                'url': url,
                'title': title,
                'markdown': match.group(0)
            })

        return images

    def extract_links(self, markdown_text: str) -> List[Dict[str, str]]:
        """
        Extract links from Markdown text.

        Args:
            markdown_text: Markdown text

        Returns:
            List of dictionaries with link information
        """
        if not markdown_text:
            return []

        links = []

        link_pattern = r'\[([^\]]+)\]\(([^)]+)(?:\s+"([^"]*)")?\)'

        for match in re.finditer(link_pattern, markdown_text):
            text = match.group(1)
            url = match.group(2)
            title = match.group(3) or ""

            links.append({
                'text': text,
                'url': url,
                'title': title,
                'markdown': match.group(0)
            })

        return links

    def _process_markdown_line(self, line: str) -> List[Dict[str, Any]]:
        """
        Process one Markdown line and convert to Slides elements.

        Args:
            line: Single line of Markdown text

        Returns:
            List of Slides elements
        """
        elements = []

        header_match = re.match(r'^(#{1,6})\s*(.+)', line.strip())
        if header_match:
            level = len(header_match.group(1))
            text_content = header_match.group(2)

            elements.append({
                "textRun": {
                    "content": text_content,
                    "style": {
                        "fontSize": {
                            "magnitude": self.header_sizes.get(level, 16),
                            "unit": "PT"
                        },
                        "bold": True
                    }
                }
            })
            return elements

        list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)', line)
        if list_match:
            indent = len(list_match.group(1))
            content = list_match.group(3)

            prefix = "  " * (indent // 2) + "• "
            full_text = prefix + content

            elements.append({
                "textRun": {
                    "content": full_text,
                    "style": {}
                }
            })
            return elements

        quote_match = re.match(r'^>\s*(.+)', line)
        if quote_match:
            content = quote_match.group(1)
            quoted_text = f'"{content}"'

            elements.append({
                "textRun": {
                    "content": quoted_text,
                    "style": {"italic": True}
                }
            })
            return elements

        return self._process_inline_formatting(line)

    def _process_inline_formatting(self, text: str) -> List[Dict[str, Any]]:
        """
        Process inline formatting in text.

        Args:
            text: Text with potential inline formatting

        Returns:
            List of text elements with formatting
        """
        elements = []
        current_pos = 0

        patterns = [
            (r'\*\*\*([^*]+)\*\*\*', {'bold': True, 'italic': True}),
            (r'\*\*([^*]+)\*\*', {'bold': True}),
            (r'(?<!\*)\*([^*]+)\*(?!\*)', {'italic': True}),
            (r'~~([^~]+)~~', {'strikethrough': True}),
            (r'`([^`]+)`', {'fontFamily': 'Courier New'}),
            (r'\[([^\]]+)\]\([^)]+\)', {'foregroundColor': {'rgbColor': {'blue': 1.0}}, 'underline': True}),
        ]

        while current_pos < len(text):
            earliest_match = None
            earliest_pos = len(text)
            earliest_style = None

            for pattern, style in patterns:
                match = re.search(pattern, text[current_pos:])
                if match and match.start() + current_pos < earliest_pos:
                    earliest_match = match
                    earliest_pos = match.start() + current_pos
                    earliest_style = style

            if earliest_match:
                if earliest_pos > current_pos:
                    plain_text = text[current_pos:earliest_pos]
                    elements.append({
                        "textRun": {
                            "content": plain_text,
                            "style": {}
                        }
                    })

                formatted_text = earliest_match.group(1)
                elements.append({
                    "textRun": {
                        "content": formatted_text,
                        "style": earliest_style
                    }
                })

                current_pos = earliest_pos + earliest_match.end()
            else:
                remaining_text = text[current_pos:]
                if remaining_text:
                    elements.append({
                        "textRun": {
                            "content": remaining_text,
                            "style": {}
                        }
                    })
                break

        return elements

    def _create_line_requests(self, element_id: str, line: str, start_index: int) -> Tuple[List[Dict[str, Any]], int]:
        """
        Create requests for one Markdown line.

        Args:
            element_id: Element ID for text insertion
            line: Markdown line
            start_index: Starting index for insertion

        Returns:
            Tuple of (requests list, text length added)
        """
        requests = []

        header_match = re.match(r'^(#{1,6})\s*(.+)', line.strip())
        if header_match:
            level = len(header_match.group(1))
            text_content = header_match.group(2).strip()

            requests.append({
                "insertText": {
                    "objectId": element_id,
                    "insertionIndex": start_index,
                    "text": text_content
                }
            })

            requests.append({
                "updateTextStyle": {
                    "objectId": element_id,
                    "style": {
                        "fontSize": {"magnitude": self.header_sizes.get(level, 16), "unit": "PT"},
                        "bold": True
                    },
                    "fields": "fontSize,bold",
                    "textRange": {
                        "type": "FIXED_RANGE",
                        "startIndex": start_index,
                        "endIndex": start_index + len(text_content)
                    }
                }
            })

            return requests, len(text_content)

        list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)', line)
        if list_match:
            indent_level = len(list_match.group(1)) // 2
            content = list_match.group(3)

            prefix = "  " * indent_level + "• "
            full_text = prefix + content

            requests.append({
                "insertText": {
                    "objectId": element_id,
                    "insertionIndex": start_index,
                    "text": full_text
                }
            })

            return requests, len(full_text)

        quote_match = re.match(r'^>\s*(.+)', line)
        if quote_match:
            content = quote_match.group(1)
            quoted_text = f'"{content}"'

            requests.append({
                "insertText": {
                    "objectId": element_id,
                    "insertionIndex": start_index,
                    "text": quoted_text
                }
            })

            requests.append({
                "updateTextStyle": {
                    "objectId": element_id,
                    "style": {"italic": True},
                    "fields": "italic",
                    "textRange": {
                        "type": "FIXED_RANGE",
                        "startIndex": start_index,
                        "endIndex": start_index + len(quoted_text)
                    }
                }
            })

            return requests, len(quoted_text)

        return self._create_inline_requests(element_id, line, start_index)

    def _create_inline_requests(self, element_id: str, text: str, start_index: int) -> Tuple[List[Dict[str, Any]], int]:
        """
        Create requests for inline formatting.

        Args:
            element_id: Element ID for text insertion
            text: Text with inline formatting
            start_index: Starting index for insertion

        Returns:
            Tuple of (requests list, text length added)
        """
        requests = []
        current_pos = 0
        text_index = start_index

        patterns = [
            (r'\*\*\*([^*]+?)\*\*\*', {'bold': True, 'italic': True}),
            (r'\*\*([^*]+?)\*\*', {'bold': True}),
            (r'(?<!\*)\*([^*]+?)\*(?!\*)', {'italic': True}),
            (r'~~([^~]+?)~~', {'strikethrough': True}),
            (r'`([^`]+?)`',
             {'fontFamily': 'Courier New', 'foregroundColor': {'rgbColor': {'red': 0.8, 'green': 0.2, 'blue': 0.2}}}),
            (r'\[([^\]]+?)\]\([^)]+?\)', {'foregroundColor': {'rgbColor': {'blue': 1.0}}, 'underline': True}),
        ]

        while current_pos < len(text):
            earliest_match = None
            earliest_pos = len(text)
            earliest_style = None

            for pattern, style in patterns:
                match = re.search(pattern, text[current_pos:])
                if match and match.start() + current_pos < earliest_pos:
                    earliest_match = match
                    earliest_pos = match.start() + current_pos
                    earliest_style = style

            if earliest_match:
                if earliest_pos > current_pos:
                    plain_text = text[current_pos:earliest_pos]
                    requests.append({
                        "insertText": {
                            "objectId": element_id,
                            "insertionIndex": text_index,
                            "text": plain_text
                        }
                    })
                    text_index += len(plain_text)

                formatted_text = earliest_match.group(1)

                requests.append({
                    "insertText": {
                        "objectId": element_id,
                        "insertionIndex": text_index,
                        "text": formatted_text
                    }
                })

                if earliest_style:
                    requests.append({
                        "updateTextStyle": {
                            "objectId": element_id,
                            "style": earliest_style,
                            "fields": ",".join(earliest_style.keys()),
                            "textRange": {
                                "type": "FIXED_RANGE",
                                "startIndex": text_index,
                                "endIndex": text_index + len(formatted_text)
                            }
                        }
                    })

                text_index += len(formatted_text)
                current_pos = earliest_pos + earliest_match.end()
            else:
                remaining_text = text[current_pos:]
                if remaining_text:
                    requests.append({
                        "insertText": {
                            "objectId": element_id,
                            "insertionIndex": text_index,
                            "text": remaining_text
                        }
                    })
                    text_index += len(remaining_text)
                break

        return requests, text_index - start_index

    def _style_to_markdown(self, content: str, style: Dict[str, Any]) -> str:
        """
        Convert Google Slides style back to Markdown.

        Args:
            content: Text content
            style: Google Slides style dictionary

        Returns:
            Markdown formatted text
        """
        if not content:
            return content

        text = content.rstrip('\n')
        trailing_newlines = content[len(text):]

        font_size = style.get("fontSize", {})
        if font_size and "magnitude" in font_size:
            size = font_size["magnitude"]
            for level, header_size in self.header_sizes.items():
                if size >= header_size:
                    text = f"{'#' * level} {text}"
                    break

        is_bold = style.get("bold", False)
        is_italic = style.get("italic", False)
        is_strikethrough = style.get("strikethrough", False)
        font_family = style.get("fontFamily", "")

        if font_family and "courier" in font_family.lower():
            text = f"`{text}`"

        if is_bold and is_italic:
            text = f"***{text}***"
        elif is_bold:
            text = f"**{text}**"
        elif is_italic:
            text = f"*{text}*"

        if is_strikethrough:
            text = f"~~{text}~~"

        return text + trailing_newlines


def markdown_to_slides_elements(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Quick conversion of Markdown to Google Slides elements.

    Args:
        markdown_text: Markdown text

    Returns:
        List of elements for Google Slides API
    """
    processor = MarkdownProcessor()
    return processor.markdown_to_slides_elements(markdown_text)


def slides_elements_to_markdown(elements: List[Dict[str, Any]]) -> str:
    """
    Quick conversion of Google Slides elements to Markdown.

    Args:
        elements: Elements from Google Slides API

    Returns:
        Markdown text
    """
    processor = MarkdownProcessor()
    return processor.slides_elements_to_markdown(elements)


def clean_markdown_for_slides(text: str) -> str:
    """
    Quick text cleaning for Google Slides.

    Args:
        text: Source text

    Returns:
        Cleaned text suitable for Google Slides
    """
    processor = MarkdownProcessor()
    return processor.clean_text_for_slides(text)
