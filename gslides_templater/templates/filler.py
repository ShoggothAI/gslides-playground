"""
Template filler for Google Slides Templater.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Union, Set, Tuple, Callable

from gslides_templater.client import SlidesClient
from gslides_templater.models.presentation import Presentation
from gslides_templater.models.slide import Slide
from gslides_templater.models.element import Element, TextBox, Image, Table
from gslides_templater.utils.helpers import extract_placeholders, is_image_url

logger = logging.getLogger(__name__)


class TemplateFiller:
    """
    Template filler for Google Slides.

    This class helps fill templates created by TemplateCreator with data.
    """

    def __init__(self, client: SlidesClient):
        """
        Initialize the template filler.

        Args:
            client: The Google Slides client to use.
        """
        self.client = client

    def create_from_template(self,
                             template_id: str,
                             title: Optional[str] = None) -> Presentation:
        """
        Create a new presentation from a template.

        Args:
            template_id: The ID of the template presentation.
            title: The title for the new presentation.

        Returns:
            The newly created presentation.
        """
        # Get the template presentation
        template = self.client.get_presentation(template_id)

        # Create a copy with the specified title
        if not title:
            title = f"From template: {template.title}"

        presentation = self.client.copy_presentation(template_id, title=title)
        presentation = presentation.with_client(self.client)

        return presentation

    def fill_from_template_config(self,
                                  presentation: Presentation,
                                  config_path: str,
                                  data: Dict[str, Any]) -> None:
        """
        Fill a presentation using a template configuration file.

        Args:
            presentation: The presentation to fill.
            config_path: The path to the template configuration file.
            data: The data to fill the template with.
        """
        # Load the template configuration
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Fill the placeholders
        self.fill_placeholders(presentation, config["placeholders"], data)

    def fill_placeholders(self,
                          presentation: Presentation,
                          placeholders_config: Dict[str, List[Dict[str, str]]],
                          data: Dict[str, Any]) -> None:
        """
        Fill placeholders in a presentation with data.

        Args:
            presentation: The presentation to fill.
            placeholders_config: The placeholders configuration from the template config file.
            data: The data to fill the placeholders with.
        """
        # Create a batch request for efficiency
        batch = presentation.create_batch_request()
        image_operations = []  # Store image operations separately as they need special handling

        # Track placeholders that have been filled
        filled_placeholders = set()

        # Process all placeholders
        for placeholder, occurrences in placeholders_config.items():
            # Check if the placeholder exists in the data
            if placeholder in data:
                filled_placeholders.add(placeholder)
                value = data[placeholder]

                for occurrence in occurrences:
                    slide_id = occurrence["slide_id"]
                    element_id = occurrence["element_id"]

                    slide = presentation.get_slide(slide_id)
                    if not slide:
                        logger.warning(f"Slide {slide_id} not found in presentation.")
                        continue

                    element = slide.get_element(element_id)
                    if not element:
                        logger.warning(f"Element {element_id} not found in slide {slide_id}.")
                        continue

                    # Handle different types of data
                    if isinstance(value, str):
                        if is_image_url(value):
                            # Handle image URLs
                            if element.element_type == "image":
                                # For image elements, replace the image
                                image_operations.append((element, value))
                            else:
                                # For other elements, replace with placeholder text
                                batch.replace_all_text(
                                    f"{{{{{placeholder}}}}}",
                                    f"[Image: {placeholder}]",
                                    match_case=True
                                )
                        else:
                            # Handle text replacements
                            batch.replace_all_text(
                                f"{{{{{placeholder}}}}}",
                                value,
                                match_case=True
                            )
                    elif isinstance(value, (int, float, bool)):
                        # Handle numeric and boolean values
                        batch.replace_all_text(
                            f"{{{{{placeholder}}}}}",
                            str(value),
                            match_case=True
                        )
                    elif isinstance(value, dict) and element.element_type == "table":
                        # Handle table data
                        # This will be processed separately after the batch request
                        logger.info(f"Table data for {placeholder} will be processed separately.")
                    elif isinstance(value, list) and element.element_type == "table":
                        # Handle table data as list
                        # This will be processed separately after the batch request
                        logger.info(f"Table data (list) for {placeholder} will be processed separately.")
                    else:
                        # For other types, convert to string
                        batch.replace_all_text(
                            f"{{{{{placeholder}}}}}",
                            str(value),
                            match_case=True
                        )

        # Execute the batch request for text replacements
        if batch.requests:
            batch.execute()

        # Process image operations separately
        for element, url in image_operations:
            if isinstance(element, Image):
                element.replace_with_image(url)

        # Process table data separately
        for placeholder, occurrences in placeholders_config.items():
            if placeholder in data and placeholder in filled_placeholders:
                value = data[placeholder]

                if isinstance(value, (dict, list)):
                    for occurrence in occurrences:
                        slide_id = occurrence["slide_id"]
                        element_id = occurrence["element_id"]

                        slide = presentation.get_slide(slide_id)
                        if not slide:
                            continue

                        element = slide.get_element(element_id)
                        if not element or element.element_type != "table":
                            continue

                        # Fill the table with data
                        self._fill_table(element, value)

        # Warn about any placeholders that were not filled
        missing_placeholders = set(placeholders_config.keys()) - filled_placeholders
        if missing_placeholders:
            logger.warning(f"The following placeholders were not filled: {missing_placeholders}")

    def _fill_table(self, table_element: Element, data: Union[Dict[str, Any], List[Any]]) -> None:
        """
        Fill a table element with data.

        Args:
            table_element: The table element to fill.
            data: The data to fill the table with. Can be a dictionary or a list.
        """
        if not isinstance(table_element, Table):
            # Convert to Table type if necessary
            table_element.__class__ = Table

        # Get table dimensions
        rows = table_element.rows
        columns = table_element.columns

        if rows == 0 or columns == 0:
            logger.warning("Table has no rows or columns.")
            return

        if isinstance(data, dict):
            # Fill from dictionary
            # Using the keys as headers in the first row and values in the second row
            keys = list(data.keys())
            for col, key in enumerate(keys[:columns]):
                # Set header
                table_element.set_cell_text(0, col, key)

                # Set value
                value = data[key]
                if col < columns:
                    table_element.set_cell_text(1, col, str(value))

        elif isinstance(data, list):
            # Fill from list
            if all(isinstance(item, dict) for item in data):
                # List of dictionaries (typical data table)
                if not data:
                    return  # Empty list

                # Use the keys of the first dictionary as headers
                headers = list(data[0].keys())

                # Set headers
                for col, header in enumerate(headers[:columns]):
                    table_element.set_cell_text(0, col, header)

                # Set values
                for row, item in enumerate(data[:rows - 1]):
                    for col, header in enumerate(headers[:columns]):
                        if header in item:
                            table_element.set_cell_text(row + 1, col, str(item.get(header, "")))
            else:
                # Simple list
                # Determine how to lay out the data based on list length and table dimensions
                if len(data) <= rows:
                    # Fit vertically
                    for row, item in enumerate(data[:rows]):
                        table_element.set_cell_text(row, 0, str(item))
                else:
                    # Fit horizontally and vertically
                    item_index = 0
                    for row in range(rows):
                        for col in range(columns):
                            if item_index < len(data):
                                table_element.set_cell_text(row, col, str(data[item_index]))
                                item_index += 1

    def fill_template(self,
                      presentation: Presentation,
                      data: Dict[str, Any]) -> None:
        """
        Fill a presentation with data by replacing all placeholders.

        This method searches for all placeholders in the presentation and replaces
        them with the corresponding values from the data dictionary.

        Args:
            presentation: The presentation to fill.
            data: The data to fill the template with.
        """
        # Create a batch request for efficiency
        batch = presentation.create_batch_request()

        # Replace all placeholders in the presentation
        for key, value in data.items():
            if isinstance(value, str):
                if is_image_url(value):
                    # For images, we need special handling
                    # We'll do this in a separate pass
                    continue

                batch.replace_all_text(
                    f"{{{{{key}}}}}",
                    value,
                    match_case=True
                )
            elif isinstance(value, (int, float, bool)):
                batch.replace_all_text(
                    f"{{{{{key}}}}}",
                    str(value),
                    match_case=True
                )
            else:
                # For complex types, convert to string representation
                batch.replace_all_text(
                    f"{{{{{key}}}}}",
                    str(value),
                    match_case=True
                )

        # Execute the batch request
        if batch.requests:
            batch.execute()

        # Handle image URLs
        for key, value in data.items():
            if isinstance(value, str) and is_image_url(value):
                # Find image placeholders first
                self._replace_image_placeholders(presentation, key, value)

        # Handle special tables
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                # Find table placeholders
                self._replace_table_placeholders(presentation, key, value)

    def _replace_image_placeholders(self,
                                    presentation: Presentation,
                                    key: str,
                                    image_url: str) -> None:
        """
        Replace image placeholders with actual images.

        Args:
            presentation: The presentation to process.
            key: The placeholder key.
            image_url: The URL of the image to use.
        """
        for slide in presentation.slides:
            # Look for shape elements with the placeholder
            for element in slide.page_elements:
                if element.element_type == "shape" and element.text:
                    if f"{{{{{key}}}}}" in element.text:
                        # This shape contains the image placeholder
                        # Create a new image at the same position and delete the shape
                        if element.size and element.transform:
                            try:
                                # Create the image
                                Image.create(
                                    self.client,
                                    presentation.presentation_id,
                                    slide.object_id,
                                    url=image_url,
                                    position=element.transform.to_api_format(),
                                    size=element.size
                                )

                                # Delete the placeholder shape
                                element.delete()
                            except Exception as e:
                                logger.error(f"Error replacing image placeholder: {e}")

                elif element.element_type == "image":
                    # For existing images, check if they're marked as the placeholder
                    description = element.description or ""
                    if description == f"image:{key}" or description == f"template:image:{key}":
                        try:
                            # Replace the image
                            element.replace_with_image(image_url)
                        except Exception as e:
                            logger.error(f"Error replacing image: {e}")

    def _replace_table_placeholders(self,
                                    presentation: Presentation,
                                    key: str,
                                    data: Union[Dict[str, Any], List[Any]]) -> None:
        """
        Replace table placeholders with actual data.

        Args:
            presentation: The presentation to process.
            key: The placeholder key.
            data: The table data to use.
        """
        for slide in presentation.slides:
            # Look for table elements
            for element in slide.page_elements:
                if element.element_type == "table":
                    # Check if this table is marked for this data
                    description = element.description or ""
                    if description == f"table:{key}" or description == f"template:table:{key}":
                        # This table should be filled with the data
                        self._fill_table(element, data)
                        continue

                # Also check text elements that might contain the table placeholder
                if element.element_type == "shape" and element.text:
                    if f"{{{{{key}}}}}" in element.text:
                        # This shape contains a table placeholder
                        # Find other table elements that might be intended for this data
                        nearby_tables = []

                        for table_element in slide.page_elements:
                            if table_element.element_type == "table":
                                if not table_element.description:
                                    # This table has no specific assignment, so it might be for this data
                                    nearby_tables.append(table_element)

                        if nearby_tables:
                            # Use the first available table
                            self._fill_table(nearby_tables[0], data)

                            # Replace the placeholder with empty text
                            element.replace_text(f"{{{{{key}}}}}", "", match_case=True)
