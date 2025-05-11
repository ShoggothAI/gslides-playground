"""
Template creator for Google Slides Templater.
"""

import json
from typing import Dict, List, Optional, Tuple

from gslides_templater.client import SlidesClient
from gslides_templater.models.element import TextBox
from gslides_templater.models.presentation import Presentation
from gslides_templater.models.slide import Slide
from gslides_templater.utils.helpers import extract_placeholders


class TemplateCreator:
    """
    Template creator for Google Slides.

    This class helps create templates from existing presentations or from scratch.
    Templates can have placeholders that can be filled later using TemplateFiller.
    """

    def __init__(self, client: SlidesClient):
        """
        Initialize the template creator.

        Args:
            client: The Google Slides client to use.
        """
        self.client = client

    def create_from_presentation(self,
                                 presentation_id: str,
                                 title: Optional[str] = None,
                                 include_slides: Optional[List[int]] = None,
                                 include_slide_ids: Optional[List[str]] = None) -> Presentation:
        """
        Create a template from an existing presentation.

        Args:
            presentation_id: The ID of the presentation to use as a template.
            title: The title for the template presentation.
            include_slides: List of slide indices to include (0-based).
            include_slide_ids: List of slide IDs to include.

        Returns:
            The newly created template presentation.

        Raises:
            ValueError: If both include_slides and include_slide_ids are provided.
        """
        if include_slides and include_slide_ids:
            raise ValueError("Only one of include_slides and include_slide_ids should be provided.")

        # Get the original presentation
        original = self.client.get_presentation(presentation_id)

        # Create a copy with the specified title
        if not title:
            title = f"Template of {original.title}"

        template = self.client.copy_presentation(presentation_id, title=title)
        template = template.with_client(self.client)

        # If specific slides should be included, remove the others
        if include_slides or include_slide_ids:
            # Create a set of slide IDs to keep
            slides_to_keep = set()

            if include_slides:
                for index in include_slides:
                    if 0 <= index < len(template.slides):
                        slides_to_keep.add(template.slides[index].object_id)

            if include_slide_ids:
                slides_to_keep.update(include_slide_ids)

            # Remove slides that should not be kept
            slide_ids_to_remove = []
            for slide in template.slides:
                if slide.object_id not in slides_to_keep:
                    slide_ids_to_remove.append(slide.object_id)

            # Remove slides in reverse order to avoid index shifting
            for slide_id in slide_ids_to_remove:
                template.delete_slide(slide_id)

        # Refresh the template to get the updated slides list
        template.refresh()

        return template

    def create_blank_template(self, title: str = "Blank Template") -> Presentation:
        """
        Create a blank template presentation.

        Args:
            title: The title for the template presentation.

        Returns:
            The newly created blank template presentation.
        """
        # Create a new blank presentation
        template = self.client.create_presentation(title)
        template = template.with_client(self.client)

        return template

    def add_placeholder_slide(self,
                              template: Presentation,
                              title: str = "Title {{title}}",
                              content: str = "Content {{content}}") -> Slide:
        """
        Add a new slide with placeholders to the template.

        Args:
            template: The template presentation.
            title: The title text with placeholders.
            content: The content text with placeholders.

        Returns:
            The newly created slide.
        """
        # Create a new slide
        slide = template.create_slide()

        title_transform = {
            "translateX": 100,
            "translateY": 50,
            "scaleX": 1.0,
            "scaleY": 1.0,
            "unit": "PT"
        }

        content_transform = {
            "translateX": 100,
            "translateY": 120,
            "scaleX": 1.0,
            "scaleY": 1.0,
            "unit": "PT"
        }

        # Create title text box
        title_box = TextBox.create(
            self.client,
            template.presentation_id,
            slide.object_id,
            text=title,
            position=title_transform,
            size={"width": {"magnitude": 400, "unit": "PT"},
                  "height": {"magnitude": 50, "unit": "PT"}}
        )

        # Create content text box
        content_box = TextBox.create(
            self.client,
            template.presentation_id,
            slide.object_id,
            text=content,
            position=content_transform,
            size={"width": {"magnitude": 400, "unit": "PT"},
                  "height": {"magnitude": 200, "unit": "PT"}}
        )

        # Refresh the slide to include the new elements
        slide.refresh()

        return slide

    def find_placeholders(self, template: Presentation) -> Dict[str, List[Tuple[str, str, str]]]:
        """
        Find all placeholders in the template.

        Args:
            template: The template presentation.

        Returns:
            A dictionary mapping placeholder names to lists of tuples containing
            (slide_id, element_id, placeholder_context) for each occurrence.
        """
        placeholders = {}

        for slide in template.slides:
            for element in slide.page_elements:
                # Check if this element has text content
                text_content = element.text_content
                if text_content:
                    text = text_content.plain_text
                    found_placeholders = extract_placeholders(text)

                    for placeholder in found_placeholders:
                        if placeholder not in placeholders:
                            placeholders[placeholder] = []

                        # Add this occurrence with some context
                        context = text[:100] + "..." if len(text) > 100 else text
                        placeholders[placeholder].append((
                            slide.object_id,
                            element.object_id,
                            context
                        ))

        return placeholders

    def export_template_config(self, template: Presentation, output_path: str) -> None:
        """
        Export template configuration to a JSON file.

        This exports information about the template, including placeholders,
        slides, and other metadata that can be used by TemplateFiller.

        Args:
            template: The template presentation.
            output_path: The path to save the configuration file.
        """
        # Get information about the template
        placeholders = self.find_placeholders(template)

        # Prepare configuration dictionary
        config = {
            "template_id": template.presentation_id,
            "title": template.title,
            "slides": [{
                "slide_id": slide.object_id,
                "index": i
            } for i, slide in enumerate(template.slides)],
            "placeholders": {
                placeholder: [{
                    "slide_id": slide_id,
                    "element_id": element_id,
                    "context": context
                } for slide_id, element_id, context in occurrences]
                for placeholder, occurrences in placeholders.items()
            }
        }

        # Save to file
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)

    def mark_template_elements(self, template: Presentation,
                               template_elements: Dict[str, List[str]]) -> None:
        """
        Mark elements in the template with special tags.

        This adds special descriptive tags to elements to indicate their purpose
        in the template. These tags are used by TemplateFiller to identify elements.

        Args:
            template: The template presentation.
            template_elements: A dictionary mapping element types to lists of element IDs.
                Example: {"title": ["elementId1"], "content": ["elementId2"]}
        """
        batch = template.create_batch_request()

        for element_type, element_ids in template_elements.items():
            for element_id in element_ids:
                # Check if the element exists
                element_found = False
                for slide in template.slides:
                    element = slide.get_element(element_id)
                    if element:
                        element_found = True
                        # Add a description tag to the element
                        batch.add_request({
                            "updatePageElementProperties": {
                                "objectId": element_id,
                                "pageElementProperties": {
                                    "description": f"template:{element_type}"
                                },
                                "fields": "description"
                            }
                        })
                        break

                if not element_found:
                    print(f"Warning: Element {element_id} not found in template.")

        # Execute the batch request
        batch.execute()
