"""
Core functionality for Google Slides Templater.
Main module providing Google Slides API integration and template system.
"""

import json
import time
import uuid
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .auth import authenticate
from .markdown_processor import MarkdownProcessor


class SlidesTemplater:
    """
    Main class for working with Google Slides API and template system.

    Supports:
    - Creating and editing presentations
    - Full Markdown ↔ Google Slides conversion
    - Smart template system with automatic placeholder detection
    - Preserving all formatting styles
    """

    def __init__(self, credentials, scopes: Optional[List[str]] = None):
        """
        Initialize SlidesTemplater.

        Args:
            credentials: Google API credentials
            scopes: OAuth scopes for API access
        """
        if hasattr(credentials, 'credentials'):
            self.credentials = credentials.credentials
        else:
            self.credentials = credentials

        self.scopes = scopes or [
            'https://www.googleapis.com/auth/presentations',
            'https://www.googleapis.com/auth/drive'
        ]

        self.slides_service = build('slides', 'v1', credentials=self.credentials)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)

        self.markdown_processor = MarkdownProcessor()

        self.last_request_time = 0
        self.min_request_interval = 0.1

        self.header_sizes = {1: 36, 2: 28, 3: 24, 4: 20, 5: 18, 6: 16}

    @classmethod
    def from_credentials(cls, service_account_path: str = None,
                        oauth_credentials_path: str = None,
                        token_path: str = None) -> 'SlidesTemplater':
        """
        Create SlidesTemplater from credentials files.

        Args:
            service_account_path: Path to service account JSON
            oauth_credentials_path: Path to OAuth credentials JSON
            token_path: Path to saved token

        Returns:
            Configured SlidesTemplater instance
        """
        credentials = authenticate(
            service_account_file=service_account_path,
            credentials_path=oauth_credentials_path,
            token_path=token_path
        )
        return cls(credentials)

    def _rate_limit(self):
        """Apply rate limiting to API requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, func, *args, **kwargs):
        """Execute request with retry on errors."""
        self._rate_limit()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs).execute()
            except HttpError as e:
                if e.resp.status == 429:
                    wait_time = (2 ** attempt) + 1
                    time.sleep(wait_time)
                    continue
                elif e.resp.status in [500, 502, 503, 504]:
                    wait_time = (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        raise Exception(f"Maximum retry attempts exceeded ({max_retries})")

    def create_presentation(self, title: str = "New Presentation") -> str:
        """
        Create new presentation.

        Args:
            title: Presentation title

        Returns:
            ID of created presentation
        """
        body = {'title': title}
        result = self._make_request(
            self.slides_service.presentations().create,
            body=body
        )
        return result['presentationId']

    def get_presentation(self, presentation_id: str) -> Dict[str, Any]:
        """
        Get presentation data.

        Args:
            presentation_id: Presentation ID

        Returns:
            Presentation data from Google Slides API
        """
        return self._make_request(
            self.slides_service.presentations().get,
            presentationId=presentation_id
        )

    def copy_presentation(self, presentation_id: str, title: str) -> str:
        """
        Copy presentation.

        Args:
            presentation_id: Source presentation ID
            title: New presentation title

        Returns:
            ID of copied presentation
        """
        body = {'name': title}
        result = self._make_request(
            self.drive_service.files().copy,
            fileId=presentation_id,
            body=body
        )
        return result['id']

    def batch_update(self, presentation_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute batch update with automatic chunking.

        Args:
            presentation_id: Presentation ID
            requests: List of requests to execute

        Returns:
            Results of all request executions
        """
        if not requests:
            return {'replies': []}

        batch_size = 50
        all_replies = []

        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            body = {'requests': batch}

            result = self._make_request(
                self.slides_service.presentations().batchUpdate,
                presentationId=presentation_id,
                body=body
            )

            all_replies.extend(result.get('replies', []))

        return {'replies': all_replies}

    def get_presentation_url(self, presentation_id: str) -> str:
        """
        Get presentation view URL.

        Args:
            presentation_id: Presentation ID

        Returns:
            Presentation URL
        """
        return f"https://docs.google.com/presentation/d/{presentation_id}/edit"

    def add_markdown_slide(self, presentation_id: str, markdown_content: str,
                          slide_index: Optional[int] = None) -> str:
        """
        Add new slide with Markdown content.

        Args:
            presentation_id: Presentation ID
            markdown_content: Markdown text to add
            slide_index: Slide position (None = at end)

        Returns:
            Created slide ID
        """
        slide_id = f"slide_{uuid.uuid4().hex[:8]}"

        create_slide_request = {
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {
                    "predefinedLayout": "BLANK"
                }
            }
        }

        if slide_index is not None:
            create_slide_request["createSlide"]["insertionIndex"] = slide_index

        self.batch_update(presentation_id, [create_slide_request])

        components = self.markdown_processor.parse_to_components(markdown_content)

        y_position = 50

        for component in components:
            if component['type'] == 'header':
                self.add_text_box(
                    presentation_id, slide_id,
                    text=component['content'],
                    x=50, y=y_position,
                    width=650, height=80
                )
                y_position += 100

            elif component['type'] == 'text':
                text_height = min(300, max(150, len(component['content']) // 3))
                self.add_text_box(
                    presentation_id, slide_id,
                    text=component['content'],
                    x=50, y=y_position,
                    width=650, height=text_height
                )
                y_position += text_height + 20

            elif component['type'] == 'image':
                self.add_text_box(
                    presentation_id, slide_id,
                    text=f"[Image: {component.get('alt', 'No description')}]\nURL: {component.get('url', '')}",
                    x=50, y=y_position,
                    width=650, height=100
                )
                y_position += 120

        return slide_id

    def create_presentation_from_markdown(self, markdown_content: str, title: str = "Presentation from Markdown") -> str:
        """
        Create entire presentation from Markdown content.
        Automatically splits into slides by level 1 headers.

        Args:
            markdown_content: Full Markdown content
            title: Presentation title

        Returns:
            Created presentation ID
        """
        presentation_id = self.create_presentation(title)

        slides_content = self._split_markdown_to_slides(markdown_content)

        presentation = self.get_presentation(presentation_id)
        if presentation.get('slides'):
            first_slide_id = presentation['slides'][0]['objectId']
            delete_request = {"deleteObject": {"objectId": first_slide_id}}
            self.batch_update(presentation_id, [delete_request])

        for slide_content in slides_content:
            if slide_content.strip():
                self.add_markdown_slide(presentation_id, slide_content)

        return presentation_id

    def _split_markdown_to_slides(self, markdown_content: str) -> List[str]:
        """
        Split Markdown content into slides by level 1 headers.

        Args:
            markdown_content: Source Markdown

        Returns:
            List of content for each slide
        """
        lines = markdown_content.split('\n')
        slides = []
        current_slide = []

        for line in lines:
            if line.strip().startswith('# ') and current_slide:
                slides.append('\n'.join(current_slide))
                current_slide = [line]
            else:
                current_slide.append(line)

        if current_slide:
            slides.append('\n'.join(current_slide))

        return slides

    def add_text_box(self, presentation_id: str, slide_id: str,
                    text: str = "", x: float = 100, y: float = 100,
                    width: float = 400, height: float = 200) -> str:
        """
        Add text box with Markdown support.

        Args:
            presentation_id: Presentation ID
            slide_id: Slide ID
            text: Text (supports Markdown)
            x, y: Position in points
            width, height: Dimensions in points

        Returns:
            Created element ID
        """
        element_id = f"textbox_{uuid.uuid4().hex[:8]}"

        create_request = {
            "createShape": {
                "objectId": element_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": width, "unit": "PT"},
                        "height": {"magnitude": height, "unit": "PT"}
                    },
                    "transform": {
                        "translateX": x,
                        "translateY": y,
                        "scaleX": 1.0,
                        "scaleY": 1.0,
                        "unit": "PT"
                    }
                }
            }
        }

        requests = [create_request]

        if text.strip():
            text_requests = self._create_text_requests(element_id, text)
            requests.extend(text_requests)

        self.batch_update(presentation_id, requests)
        return element_id

    def set_text(self, presentation_id: str, element_id: str, text: str):
        """
        Set element text with Markdown support.
        Properly handles existing text replacement.

        Args:
            presentation_id: Presentation ID
            element_id: Element ID
            text: New text (supports Markdown)
        """
        if not text.strip():
            return

        try:
            presentation = self.get_presentation(presentation_id)
            element = None

            # Find the element
            for slide in presentation.get('slides', []):
                for page_element in slide.get('pageElements', []):
                    if page_element.get('objectId') == element_id:
                        element = page_element
                        break
                if element:
                    break

            requests = []

            # Check if element has existing text
            has_existing_text = False
            if element and 'shape' in element and 'text' in element['shape']:
                text_elements = element['shape']['text'].get('textElements', [])
                for te in text_elements:
                    if 'textRun' in te and te['textRun'].get('content', '').strip():
                        has_existing_text = True
                        break

            # Delete existing text only if it exists
            if has_existing_text:
                requests.append({
                    "deleteText": {
                        "objectId": element_id,
                        "textRange": {"type": "ALL"}
                    }
                })

            # Add new text
            text_requests = self._create_text_requests(element_id, text)
            requests.extend(text_requests)

            if requests:
                self.batch_update(presentation_id, requests)

        except Exception as e:
            # Fallback: just try to insert text
            print(f"Fallback text insertion for {element_id}: {e}")
            requests = self._create_text_requests(element_id, text)
            if requests:
                self.batch_update(presentation_id, requests)

    def replace_image(self, presentation_id: str, image_id: str, new_url: str):
        """
        Replace image by URL.

        Args:
            presentation_id: Presentation ID
            image_id: Image ID
            new_url: New image URL
        """
        request = {
            "replaceImage": {
                "imageObjectId": image_id,
                "url": new_url
            }
        }
        self.batch_update(presentation_id, [request])

    def _create_text_requests(self, element_id: str, text: str) -> List[Dict[str, Any]]:
        """
        Create requests for text insertion with Markdown and HTML comments support.

        Args:
            element_id: Element ID
            text: Text to insert

        Returns:
            List of requests for batch update
        """
        if self._has_html_comments(text):
            return self._process_html_comments_text(element_id, text)

        if self.markdown_processor.is_markdown(text):
            return self.markdown_processor.create_slides_requests(element_id, text)

        return [{
            "insertText": {
                "objectId": element_id,
                "insertionIndex": 0,
                "text": text
            }
        }]

    def _has_html_comments(self, text: str) -> bool:
        """Check if text contains HTML formatting comments."""
        return bool(re.search(r'<!-- \w+:[^>]+ -->', text))

    def _process_html_comments_text(self, element_id: str, text: str) -> List[Dict[str, Any]]:
        """
        Process text with HTML comments (compatibility with legacy system).

        Format: <!-- size:24 -->Text<!-- /size -->

        Args:
            element_id: Element ID
            text: Text with HTML comments

        Returns:
            List of requests for batch update
        """
        requests = []
        current_index = 0

        comment_pattern = re.compile(r'<!-- (\w+):([^>]+) -->([^<]*?)<!-- /\1 -->')

        last_end = 0
        for match in comment_pattern.finditer(text):
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                if plain_text:
                    requests.append({
                        "insertText": {
                            "objectId": element_id,
                            "insertionIndex": current_index,
                            "text": plain_text
                        }
                    })
                    current_index += len(plain_text)

            tag_type = match.group(1)
            tag_value = match.group(2)
            content = match.group(3)

            if content:
                requests.append({
                    "insertText": {
                        "objectId": element_id,
                        "insertionIndex": current_index,
                        "text": content
                    }
                })

                style = self._parse_html_comment_style(tag_type, tag_value)
                if style:
                    requests.append({
                        "updateTextStyle": {
                            "objectId": element_id,
                            "style": style,
                            "fields": ",".join(style.keys()),
                            "textRange": {
                                "type": "FIXED_RANGE",
                                "startIndex": current_index,
                                "endIndex": current_index + len(content)
                            }
                        }
                    })

                current_index += len(content)

            last_end = match.end()

        if last_end < len(text):
            remaining_text = text[last_end:]
            if remaining_text:
                requests.append({
                    "insertText": {
                        "objectId": element_id,
                        "insertionIndex": current_index,
                        "text": remaining_text
                    }
                })

        return requests

    def _parse_html_comment_style(self, tag_type: str, tag_value: str) -> Dict[str, Any]:
        """Convert HTML comment to Google Slides style."""
        style = {}

        if tag_type == 'size':
            try:
                size = int(tag_value)
                style['fontSize'] = {
                    'magnitude': size,
                    'unit': 'PT'
                }
                if size >= 16:
                    style['bold'] = True
            except ValueError:
                pass

        elif tag_type == 'font':
            style['fontFamily'] = tag_value

        elif tag_type == 'color':
            if tag_value != 'default':
                style['foregroundColor'] = {
                    'rgbColor': {
                        'red': 0.0,
                        'green': 0.0,
                        'blue': 0.0
                    }
                }

        return style

    def create_template(self, presentation_id: str, template_name: str) -> Dict[str, Any]:
        """
        Create template configuration from presentation with Markdown conversion.

        Args:
            presentation_id: Source presentation ID
            template_name: Template name

        Returns:
            Template configuration with placeholders in Markdown format
        """
        presentation = self.get_presentation(presentation_id)

        template = {
            'name': template_name,
            'source_presentation_id': presentation_id,
            'title': presentation.get('title', 'Untitled'),
            'created_at': self._get_timestamp(),
            'slides': [],
            'placeholders': {}
        }

        placeholder_counter = 1

        for slide_idx, slide in enumerate(presentation.get('slides', [])):
            slide_info = {
                'slide_id': slide['objectId'],
                'slide_index': slide_idx,
                'replaceable_elements': []
            }

            for element in slide.get('pageElements', []):
                if self._is_replaceable_element(element):
                    placeholder_name = self._generate_placeholder_name(
                        element, slide_idx, placeholder_counter
                    )

                    original_content = self._extract_content(element)

                    markdown_content = self._convert_element_to_markdown(element, original_content)

                    element_info = {
                        'element_id': element['objectId'],
                        'placeholder_name': placeholder_name,
                        'element_type': self._get_element_type(element),
                        'original_content': original_content,
                        'markdown_content': markdown_content
                    }

                    slide_info['replaceable_elements'].append(element_info)

                    template['placeholders'][placeholder_name] = {
                        'type': element_info['element_type'],
                        'slide_index': slide_idx,
                        'description': self._get_placeholder_description(element_info['element_type']),
                        'example': markdown_content,
                        'original_example': original_content
                    }

                    placeholder_counter += 1

            if slide_info['replaceable_elements']:
                template['slides'].append(slide_info)

        return template

    def _convert_element_to_markdown(self, element: Dict[str, Any], content: str) -> str:
        """
        Convert Google Slides element to Markdown format.

        Args:
            element: Element from Google Slides API
            content: Extracted content

        Returns:
            Content in Markdown format
        """
        element_type = self._get_element_type(element)

        if element_type == 'text':
            if 'shape' in element and 'text' in element['shape']:
                text_elements = element['shape']['text'].get('textElements', [])
                if text_elements:
                    return self.markdown_processor.slides_elements_to_markdown(text_elements)

        elif element_type == 'image':
            image_data = element.get('image', {})
            url = image_data.get('sourceUrl', 'https://example.com/image.jpg')
            description = image_data.get('title', 'Image')
            return f"![{description}]({url})"

        return content

    def apply_template(self, template: Dict[str, Any], data: Dict[str, Any],
                      title: str = None) -> str:
        """
        Apply template with data substitution.

        Args:
            template: Template configuration
            data: Data for substitution (supports Markdown)
            title: New presentation title

        Returns:
            Created presentation ID
        """
        new_title = title or f"Copy of {template['title']} - {self._get_timestamp()}"
        new_presentation_id = self.copy_presentation(
            template['source_presentation_id'],
            new_title
        )

        for slide_info in template['slides']:
            for element_info in slide_info['replaceable_elements']:
                placeholder_name = element_info['placeholder_name']

                if placeholder_name in data:
                    value = data[placeholder_name]
                    self._apply_element_data(new_presentation_id, element_info, value)

        return new_presentation_id

    def _apply_element_data(self, presentation_id: str, element_info: Dict[str, Any], value: Any):
        """
        Apply data to specific element with Markdown support.

        Args:
            presentation_id: Presentation ID
            element_info: Element information
            value: New value (can be in Markdown format)
        """
        element_type = element_info['element_type']
        element_id = element_info['element_id']

        try:
            if element_type == 'text' and isinstance(value, str):
                self.set_text(presentation_id, element_id, value)

            elif element_type == 'image' and isinstance(value, str):
                if value.startswith(('http://', 'https://')):
                    self.replace_image(presentation_id, element_id, value)

        except Exception as e:
            print(f"Warning: Could not update element {element_id}: {e}")

    def _is_replaceable_element(self, element: Dict[str, Any]) -> bool:
        """Determine if element is replaceable."""
        if 'image' in element:
            return True

        if 'shape' in element:
            shape = element['shape']
            if 'text' in shape:
                text_elements = shape['text'].get('textElements', [])
                for te in text_elements:
                    if 'textRun' in te:
                        content = te['textRun'].get('content', '').strip()
                        if content and len(content) > 1:
                            return True

        if 'table' in element:
            return True

        return False

    def _get_element_type(self, element: Dict[str, Any]) -> str:
        """Determine element type."""
        if 'image' in element:
            return 'image'
        elif 'shape' in element:
            return 'text'
        elif 'table' in element:
            return 'table'
        elif 'video' in element:
            return 'video'
        else:
            return 'unknown'

    def _extract_content(self, element: Dict[str, Any]) -> str:
        """Extract content from element."""
        element_type = self._get_element_type(element)

        if element_type == 'text':
            return self._extract_text_with_formatting(element)
        elif element_type == 'image':
            image_data = element.get('image', {})
            return image_data.get('sourceUrl', 'https://example.com/image.jpg')
        else:
            return f"Sample {element_type} content"

    def _extract_text_with_formatting(self, element: Dict[str, Any]) -> str:
        """Extract text preserving formatting as HTML comments."""
        if 'shape' not in element:
            return ""

        shape = element['shape']
        if 'text' not in shape:
            return ""

        text_data = shape['text']
        text_elements = text_data.get('textElements', [])

        result = ""
        for te in text_elements:
            if 'textRun' in te:
                content = te['textRun'].get('content', '')
                style = te['textRun'].get('style', {})

                formatted_content = self._recreate_html_comments(content, style)
                result += formatted_content

        return result.strip()

    def _recreate_html_comments(self, content: str, style: Dict[str, Any]) -> str:
        """Recreate HTML comments from Google Slides style."""
        if not content:
            return content

        text = content.rstrip('\n')
        trailing_newlines = content[len(text):]

        result = text

        if 'fontSize' in style:
            size = style['fontSize'].get('magnitude', 12)
            result = f"<!-- size:{int(size)} -->{result}<!-- /size -->"

        if 'fontFamily' in style:
            font = style['fontFamily'].lower()
            result = f"<!-- font:{font} -->{result}<!-- /font -->"

        if 'foregroundColor' in style:
            result = f"<!-- color:default -->{result}<!-- /color -->"

        return result + trailing_newlines

    def _generate_placeholder_name(self, element: Dict[str, Any],
                                  slide_idx: int, counter: int) -> str:
        """
        Generate meaningful placeholder name.

        Args:
            element: Presentation element
            slide_idx: Slide index
            counter: Element counter

        Returns:
            Placeholder name
        """
        element_type = self._get_element_type(element)

        if element_type == 'text':
            text_content = self._extract_text_with_formatting(element)
            if text_content:
                clean_text = re.sub(r'[#*`~\[\]()]+', '', text_content)
                clean_text = re.sub(r'<[^>]+>', '', clean_text)
                words = re.findall(r'\w+', clean_text.lower())[:2]
                if words and len(words[0]) > 2:
                    return '_'.join(words)

        return f"slide_{slide_idx + 1}_{element_type}_{counter}"

    def _get_placeholder_description(self, element_type: str) -> str:
        """Get placeholder description by element type."""
        descriptions = {
            'text': 'Text content (supports Markdown and HTML comments)',
            'image': 'Image URL (must be publicly accessible)',
            'table': 'Table data (list of rows or dictionary)',
            'video': 'Video URL'
        }
        return descriptions.get(element_type, f'{element_type.title()} type content')

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        return time.strftime('%Y-%m-%d %H:%M:%S')

    def save_template(self, template: Dict[str, Any], filename: str):
        """
        Save template to JSON file.

        Args:
            template: Template configuration
            filename: File name to save
        """
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

    def load_template(self, filename: str) -> Dict[str, Any]:
        """
        Load template from JSON file.

        Args:
            filename: Template file name

        Returns:
            Template configuration
        """
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_template_info(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed template information.

        Args:
            template: Template configuration

        Returns:
            Template information
        """
        placeholders = template.get('placeholders', {})
        slides = template.get('slides', [])

        element_types = {}
        for placeholder_info in placeholders.values():
            elem_type = placeholder_info['type']
            element_types[elem_type] = element_types.get(elem_type, 0) + 1

        return {
            'name': template.get('name', 'Unnamed'),
            'title': template.get('title', 'Untitled'),
            'created_at': template.get('created_at', 'Unknown'),
            'source_presentation_id': template.get('source_presentation_id'),
            'total_slides': len(slides),
            'total_placeholders': len(placeholders),
            'element_types': element_types,
            'placeholder_names': list(placeholders.keys())
        }

    def validate_template_data(self, template: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data for template application.

        Args:
            template: Template configuration
            data: Data to check

        Returns:
            Validation result
        """
        placeholders = template.get('placeholders', {})

        validation_result = {
            'valid': True,
            'missing_placeholders': [],
            'extra_data': [],
            'invalid_types': [],
            'warnings': []
        }

        for placeholder_name, placeholder_info in placeholders.items():
            if placeholder_name not in data:
                validation_result['missing_placeholders'].append(placeholder_name)
                validation_result['valid'] = False

        for data_key in data.keys():
            if data_key not in placeholders:
                validation_result['extra_data'].append(data_key)
                validation_result['warnings'].append(f"Data '{data_key}' does not match any placeholder")

        for placeholder_name, value in data.items():
            if placeholder_name in placeholders:
                expected_type = placeholders[placeholder_name]['type']

                if expected_type == 'text' and not isinstance(value, str):
                    validation_result['invalid_types'].append(
                        f"{placeholder_name}: expected text, got {type(value).__name__}")
                elif expected_type == 'image' and not isinstance(value, str):
                    validation_result['invalid_types'].append(
                        f"{placeholder_name}: expected image URL, got {type(value).__name__}")
                elif expected_type == 'image' and isinstance(value, str) and not value.startswith(
                        ('http://', 'https://')):
                    validation_result['warnings'].append(
                        f"{placeholder_name}: image URL should start with http:// or https://")

        if validation_result['invalid_types']:
            validation_result['valid'] = False

        return validation_result

    def preview_template_application(self, template: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview template application.

        Args:
            template: Template configuration
            data: Data to apply

        Returns:
            Preview of changes
        """
        placeholders = template.get('placeholders', {})
        preview = {
            'changes': [],
            'unchanged_placeholders': []
        }

        for placeholder_name, placeholder_info in placeholders.items():
            slide_index = placeholder_info.get('slide_index', 0) + 1
            element_type = placeholder_info.get('type', 'unknown')

            if placeholder_name in data:
                old_value = placeholder_info.get('example', '')
                new_value = data[placeholder_name]

                preview['changes'].append({
                    'placeholder': placeholder_name,
                    'slide': slide_index,
                    'type': element_type,
                    'old_value': old_value[:100] + '...' if len(str(old_value)) > 100 else str(old_value),
                    'new_value': new_value[:100] + '...' if len(str(new_value)) > 100 else str(new_value)
                })
            else:
                preview['unchanged_placeholders'].append({
                    'placeholder': placeholder_name,
                    'slide': slide_index,
                    'type': element_type,
                    'current_value': placeholder_info.get('example', '')
                })

        return preview

    def clone_presentation(self, presentation_id: str, title: str = None) -> str:
        """
        Clone presentation (alias for copy_presentation).

        Args:
            presentation_id: Source presentation ID
            title: New presentation title

        Returns:
            Cloned presentation ID
        """
        if title is None:
            original = self.get_presentation(presentation_id)
            title = f"Copy of {original.get('title', 'Untitled')}"

        return self.copy_presentation(presentation_id, title)

    def get_presentation_info(self, presentation_id: str) -> Dict[str, Any]:
        """
        Get brief presentation information.

        Args:
            presentation_id: Presentation ID

        Returns:
            Presentation information
        """
        presentation = self.get_presentation(presentation_id)
        slides = presentation.get('slides', [])

        total_elements = 0
        element_types = {}

        for slide in slides:
            for element in slide.get('pageElements', []):
                total_elements += 1
                elem_type = self._get_element_type(element)
                element_types[elem_type] = element_types.get(elem_type, 0) + 1

        return {
            'id': presentation_id,
            'title': presentation.get('title', 'Untitled'),
            'total_slides': len(slides),
            'total_elements': total_elements,
            'element_types': element_types,
            'url': self.get_presentation_url(presentation_id)
        }

    def create_sample_data(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create sample data for template.

        Args:
            template: Template configuration

        Returns:
            Dictionary with sample data
        """
        placeholders = template.get('placeholders', {})
        sample_data = {}

        for placeholder_name, placeholder_info in placeholders.items():
            element_type = placeholder_info['type']

            if element_type == 'text':
                sample_data[placeholder_name] = f"""# New header for {placeholder_name}

## Subheader

This is **updated content** with various formatting:

- List with *italic*
- Item with `code`
- ~~Strikethrough~~ corrected text

### Additional information

***Bold italic*** and regular text.

> Quote with important information"""

            elif element_type == 'image':
                sample_data[placeholder_name] = "https://via.placeholder.com/600x400/4285f4/ffffff?text=Sample+Image"

            else:
                sample_data[placeholder_name] = f"Sample data for {element_type}"

        return sample_data


def create_templater(service_account_path: str = None,
                    oauth_credentials_path: str = None,
                    token_path: str = None) -> SlidesTemplater:
    """
    Create SlidesTemplater instance.

    Args:
        service_account_path: Path to service account JSON
        oauth_credentials_path: Path to OAuth credentials JSON
        token_path: Path to saved token

    Returns:
        Configured SlidesTemplater
    """
    return SlidesTemplater.from_credentials(
        service_account_path=service_account_path,
        oauth_credentials_path=oauth_credentials_path,
        token_path=token_path
    )
