"""
Template converter for Google Slides Templater.

This module provides tools for converting regular presentations into templates
by identifying and replacing text with placeholders.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Pattern, Union, Set

from gslides_templater.client import SlidesClient
from gslides_templater.models.presentation import Presentation
from gslides_templater.templates.creator import TemplateCreator

logger = logging.getLogger(__name__)


class TemplateConverter:
    """
    Converter for transforming regular presentations into templates.

    This class provides methods for identifying potential placeholders in presentations
    and replacing them with actual placeholders in the format {{placeholder_name}}.
    """

    def __init__(self, client: SlidesClient):
        """
        Initialize the template converter.

        Args:
            client: The Google Slides client to use.
        """
        self.client = client
        self.creator = TemplateCreator(client)

    def convert_presentation(self, presentation_id: str,
                             replacements: Dict[str, str],
                             title: Optional[str] = None,
                             create_copy: bool = True) -> Presentation:
        """
        Convert a presentation into a template by replacing text with placeholders.

        Args:
            presentation_id: The ID of the presentation to convert.
            replacements: Dictionary mapping original text to placeholder names.
                For example: {"Acme Corp": "company_name", "John Doe": "ceo_name"}
            title: The title for the new template presentation (if create_copy is True).
            create_copy: Whether to create a copy of the presentation or modify in place.

        Returns:
            The converted presentation object.

        Example:
            converter = TemplateConverter(client)
            template = converter.convert_presentation(
                "1abc123...",
                {
                    "Acme Corp": "company_name",
                    "John Doe": "ceo_name",
                    "$10M": "revenue",
                    "50 employees": "employee_count"
                }
            )
        """
        # Get the original presentation
        original = self.client.get_presentation(presentation_id)

        # Create a copy if requested
        if create_copy:
            if not title:
                title = f"Template of {original.title}"

            template = self.client.copy_presentation(presentation_id, title=title)
            template = template.with_client(self.client)
        else:
            template = original

        # Replace text with placeholders
        self.replace_text_with_placeholders(template, replacements)

        # Refresh the presentation to get the latest data
        template.refresh()

        return template

    def replace_text_with_placeholders(self, presentation: Presentation,
                                       replacements: Dict[str, str]) -> None:
        """
        Replace text in a presentation with placeholders.

        Args:
            presentation: The presentation to modify.
            replacements: Dictionary mapping original text to placeholder names.
        """
        # Create a batch request for efficiency
        batch = presentation.create_batch_request()

        # Replace each text with its placeholder
        for original_text, placeholder_name in replacements.items():
            placeholder = f"{{{{{placeholder_name}}}}}"

            # Add a replace all text request
            batch.add_request({
                "replaceAllText": {
                    "replaceText": placeholder,
                    "containsText": {
                        "text": original_text,
                        "matchCase": True
                    }
                }
            })

        # Execute the batch request
        if batch.requests:
            batch.execute()

    def identify_potential_placeholders(self, presentation: Presentation) -> Dict[str, List[str]]:
        """
        Identify potential text that could be converted to placeholders.

        This method analyzes the text content of the presentation and suggests
        text that might be suitable for replacement with placeholders.

        Args:
            presentation: The presentation to analyze.

        Returns:
            A dictionary mapping suggested placeholder names to lists of original text.
            For example: {"company_name": ["Acme Corp", "ACME CORPORATION"]}
        """
        import re
        import logging
        from typing import Dict, List, Set, Pattern, Any

        logger = logging.getLogger(__name__)

        # Common patterns for potential placeholders
        patterns = {
            "company_name": [
                r"[A-Z][a-z]+ (Corporation|Corp|Inc|LLC|Ltd)",
                r"[A-Z][A-Z]+ (CORPORATION|CORP|INC|LLC|LTD)"
            ],
            "person_name": [
                r"[A-Z][a-z]+ [A-Z][a-z]+",  # John Doe
                r"[A-Z]\. [A-Z][a-z]+"  # J. Doe
            ],
            "date": [
                r"\d{1,2}/\d{1,2}/\d{2,4}",  # MM/DD/YYYY
                r"\d{1,2}-\d{1,2}-\d{2,4}",  # MM-DD-YYYY
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}"  # Month DD, YYYY
            ],
            "number": [
                r"\$\d+([,\.]\d+)*[KMB]?",  # $1,000 or $1.5M
                r"\d+([,\.]\d+)*[KMB]?"  # 1,000 or 1.5M
            ],
            "email": [
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            ],
            "website": [
                r"(www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(\.[a-zA-Z]{2,})?"
            ],
            "phone": [
                r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}"
            ]
        }

        # Compile the patterns
        compiled_patterns: Dict[str, List[Pattern]] = {}
        for category, pattern_list in patterns.items():
            compiled_patterns[category] = [re.compile(pattern) for pattern in pattern_list]

        # Build a dictionary of matched text
        matches: Dict[str, Set[str]] = {category: set() for category in patterns.keys()}
        other_matches: Set[str] = set()  # Text that doesn't match any pattern

        # Используем логирование для отладки
        logger.info(f"Analyzing presentation: {presentation.presentation_id}")
        logger.info(f"Presentation has {len(presentation.slides)} slides")

        # Step 1: Use direct API access to get all presentation data
        try:
            if not hasattr(self, 'client') or self.client is None:
                logger.error("No client available in TemplateConverter")
                return {}

            api_presentation = self.client._slides_service.presentations().get(
                presentationId=presentation.presentation_id
            ).execute()

            logger.info(f"Retrieved API presentation with {len(api_presentation.get('slides', []))} slides")

            slides = api_presentation.get('slides', [])
            for slide_idx, slide in enumerate(slides):
                slide_id = slide.get('objectId')
                logger.info(f"Processing slide {slide_idx + 1} (ID: {slide_id})")

                for element_idx, element in enumerate(slide.get('pageElements', [])):
                    element_id = element.get('objectId')

                    element_type = 'unknown'
                    for key in ['shape', 'image', 'video', 'table', 'line', 'wordArt', 'sheetsChart']:
                        if key in element:
                            element_type = key
                            break

                    logger.info(f"  Element {element_idx + 1} (ID: {element_id}, Type: {element_type})")

                    if element_type == 'shape' and 'text' in element['shape']:
                        shape_text = ""
                        for text_elem in element['shape']['text'].get('textElements', []):
                            if 'textRun' in text_elem:
                                shape_text += text_elem['textRun'].get('content', '')

                        if shape_text.strip():
                            logger.info(f"    Found text in shape: {shape_text.strip()}")

                            matched_categories = []
                            for category, pattern_list in compiled_patterns.items():
                                for pattern in pattern_list:
                                    for match in pattern.finditer(shape_text):
                                        matched_text = match.group(0)
                                        matches[category].add(matched_text)
                                        matched_categories.append(f"{category}:{matched_text}")

                            if not matched_categories:
                                words = shape_text.strip().split()
                                if len(words) >= 1:
                                    other_matches.add(shape_text.strip())
                                    logger.info(f"    Added to 'other': {shape_text.strip()}")
                            else:
                                logger.info(f"    Matched as: {', '.join(matched_categories)}")

                    if element_type == 'table':
                        for row_idx, row in enumerate(element['table'].get('tableRows', [])):
                            for cell_idx, cell in enumerate(row.get('tableCells', [])):
                                if 'text' in cell:
                                    cell_text = ""
                                    for text_elem in cell['text'].get('textElements', []):
                                        if 'textRun' in text_elem:
                                            cell_text += text_elem['textRun'].get('content', '')

                                    if cell_text.strip():
                                        logger.info(
                                            f"    Found text in table cell [{row_idx},{cell_idx}]: {cell_text.strip()}")

                                        matched_categories = []
                                        for category, pattern_list in compiled_patterns.items():
                                            for pattern in pattern_list:
                                                for match in pattern.finditer(cell_text):
                                                    matched_text = match.group(0)
                                                    matches[category].add(matched_text)
                                                    matched_categories.append(f"{category}:{matched_text}")

                                        if not matched_categories:
                                            words = cell_text.strip().split()
                                            if len(words) >= 1:
                                                other_matches.add(cell_text.strip())
                                                logger.info(f"    Added to 'other': {cell_text.strip()}")
                                        else:
                                            logger.info(f"    Matched as: {', '.join(matched_categories)}")

        except Exception as e:
            logger.error(f"Error accessing presentation through API: {str(e)}")

        # Step 2: Traditional Approach via Library Models (Backup)
        try:
            for slide_idx, slide in enumerate(presentation.slides):
                logger.info(f"Processing slide {slide_idx + 1} using library models")

                for element_idx, element in enumerate(slide.page_elements):
                    # We try to get the text in different ways
                    text = None

                    # Method 1: via text_content
                    if hasattr(element, 'text_content') and element.text_content:
                        text = element.text_content.plain_text

                    # Method 2: via text() method
                    elif hasattr(element, 'text') and callable(getattr(element, 'text')):
                        text = element.text()

                    # Method 3: via text attribute
                    elif hasattr(element, 'text'):
                        text = element.text

                    # Method 4: via shape.text for shape elements
                    elif hasattr(element, 'shape') and element.shape and 'text' in element.shape:
                        shape_text = ""
                        for text_element in element.shape['text'].get('textElements', []):
                            if 'textRun' in text_element:
                                shape_text += text_element['textRun'].get('content', '')
                        text = shape_text

                    if text and text.strip():
                        logger.info(f"  Found text using library models: {text.strip()}")

                        # Checking the text for patterns
                        matched = False
                        for category, pattern_list in compiled_patterns.items():
                            for pattern in pattern_list:
                                for match in pattern.finditer(text):
                                    matched_text = match.group(0)
                                    matches[category].add(matched_text)
                                    matched = True
                                    logger.info(f"  Matched as {category}: {matched_text}")

                        # If it doesn't match any template, add to 'other'
                        if not matched and len(text.strip()) > 0:
                            words = text.strip().split()
                            if len(words) >= 1:  # We accept even one word
                                other_matches.add(text.strip())
                                logger.info(f"  Added to 'other': {text.strip()}")

        except Exception as e:
            logger.error(f"Error processing using library models: {str(e)}")

        # Convert the results to the expected format
        result: Dict[str, List[str]] = {}
        for category, matched_set in matches.items():
            if matched_set:
                result[category] = list(matched_set)

        if other_matches:
            result["other"] = list(other_matches)

        # Final logging of results
        total_matches = sum(len(matches[category]) for category in patterns.keys()) + len(other_matches)
        logger.info(f"Total potential placeholders found: {total_matches}")
        for category, texts in result.items():
            logger.info(f"Category '{category}': {len(texts)} items")

        return result

    def suggest_replacements(self, presentation: Presentation) -> Dict[str, str]:
        """
        Suggest text replacements for converting to placeholders.

        This method analyzes the presentation and suggests specific text
        that could be replaced with placeholders.

        Args:
            presentation: The presentation to analyze.

        Returns:
            A dictionary mapping original text to suggested placeholder names.
            For example: {"Acme Corp": "company_name", "John Doe": "ceo_name"}
        """
        # Get potential placeholders
        potential = self.identify_potential_placeholders(presentation)

        # Добавим вывод для отладки
        print(f"Potential placeholders: {potential}")

        # Build suggestions
        suggestions: Dict[str, str] = {}

        # Process each category
        for category, texts in potential.items():
            if category == "other":
                # For uncategorized text, generate placeholder names from the text
                for text in texts:
                    placeholder = self._text_to_placeholder_name(text)
                    suggestions[text] = placeholder
            else:
                # For categorized text, use the category as the base
                for i, text in enumerate(texts):
                    if len(texts) == 1:
                        # If there's only one match in this category, use the category name
                        suggestions[text] = category
                    else:
                        # Otherwise, append a number
                        suggestions[text] = f"{category}_{i + 1}"

        return suggestions

    def _text_to_placeholder_name(self, text: str) -> str:
        """
        Convert text to a suitable placeholder name.

        Args:
            text: The text to convert.

        Returns:
            A placeholder name derived from the text.
        """
        # Lowercase and replace spaces with underscores
        placeholder = text.lower().replace(' ', '_')

        # Remove any non-alphanumeric characters (except underscores)
        placeholder = re.sub(r'[^a-z0-9_]', '', placeholder)

        # Ensure it doesn't start with a number
        if placeholder and placeholder[0].isdigit():
            placeholder = 'n' + placeholder

        # Truncate if too long
        if len(placeholder) > 30:
            placeholder = placeholder[:30]

        # Ensure we have something valid
        if not placeholder:
            placeholder = 'placeholder'

        return placeholder

    def create_template_from_json(self, json_data: Union[Dict[str, Any], str],
                                  replacements: Dict[str, str],
                                  title: Optional[str] = None) -> Presentation:
        """
        Create a template directly from a JSON representation of a presentation.

        Args:
            json_data: Either a dictionary containing the JSON data, or a string path to a JSON file.
            replacements: Dictionary mapping original text to placeholder names.
            title: The title for the new template presentation.

        Returns:
            The created template presentation.
        """
        # First create a presentation from the JSON
        presentation = self.client.create_presentation_from_json(json_data, title=title)

        # Then convert it to a template
        self.replace_text_with_placeholders(presentation, replacements)

        # Refresh the presentation to get the latest data
        presentation.refresh()

        return presentation

    def analyze_and_convert(self, presentation_id: str, title: Optional[str] = None,
                            suggestion_threshold: float = 0.7) -> Tuple[Presentation, Dict[str, str]]:
        """
        Analyze a presentation and automatically convert it to a template.

        This method analyzes the presentation, identifies potential placeholders,
        and creates a template by replacing the text with the suggested placeholders.

        Args:
            presentation_id: The ID of the presentation to convert.
            title: The title for the new template presentation.
            suggestion_threshold: Confidence threshold for automatic suggestions (0.0-1.0).

        Returns:
            A tuple containing:
            - The converted template presentation
            - The dictionary of replacements that were made
        """
        # Get the original presentation
        original = self.client.get_presentation(presentation_id)

        # Get suggestions
        suggestions = self.suggest_replacements(original)

        # Filter suggestions based on confidence
        # This is a simplified version - in a real implementation,
        # you would need a more sophisticated confidence calculation
        replacements = {}
        for text, placeholder in suggestions.items():
            # Very basic confidence measure based on text length
            # In a real implementation, this would be much more sophisticated
            confidence = min(len(text) / 20, 1.0)
            if confidence >= suggestion_threshold:
                replacements[text] = placeholder

        # Convert the presentation
        template = self.convert_presentation(
            presentation_id,
            replacements,
            title=title,
            create_copy=True
        )

        return template, replacements
