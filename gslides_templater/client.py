"""
Main client interface for Google Slides Templater.
"""

import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Union

from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from gslides_templater.auth import Credentials
from gslides_templater.models import TextBox, Table
from gslides_templater.models.presentation import Presentation
from gslides_templater.models.slide import Slide
from gslides_templater.utils.batch import BatchRequest

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Exception raised when an API request fails."""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class SlidesClient:
    """
    Main client interface for interacting with the Google Slides API.

    This class provides methods for creating and manipulating presentations,
    slides, and elements within slides. It handles authentication and
    provides a high-level interface to the Google Slides API.
    """

    def __init__(self, credentials: Credentials):
        """
        Initialize the client with Google API credentials.

        Args:
            credentials: Google API credentials.
        """
        self.credentials = credentials
        self._slides_service = credentials.slides_service
        self._drive_service = credentials.drive_service

    @retry(
        retry=retry_if_exception_type(HttpError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def get_presentation(self, presentation_id: str) -> Presentation:
        """
        Get a presentation by ID.

        Args:
            presentation_id: The ID of the presentation to retrieve.

        Returns:
            A Presentation object representing the retrieved presentation.

        Raises:
            APIError: If the presentation could not be retrieved.
        """
        try:
            response = self._slides_service.presentations().get(
                presentationId=presentation_id).execute()
            return Presentation.from_api_format(response)
        except HttpError as e:
            status_code = e.resp.status
            error_details = json.loads(e.content.decode('utf-8'))

            if status_code == 404:
                raise APIError(f"Presentation not found: {presentation_id}",
                               status_code=status_code, details=error_details)
            else:
                raise APIError(f"Failed to get presentation: {e.reason}",
                               status_code=status_code, details=error_details)

    def create_presentation(self, title: str = "Untitled Presentation") -> Presentation:
        """
        Create a new blank presentation.

        Args:
            title: The title of the new presentation.

        Returns:
            A Presentation object representing the newly created presentation.

        Raises:
            APIError: If the presentation could not be created.
        """
        try:
            response = self._slides_service.presentations().create(
                body={"title": title}).execute()
            return Presentation.from_api_format(response)
        except HttpError as e:
            status_code = e.resp.status
            error_details = json.loads(e.content.decode('utf-8'))
            raise APIError(f"Failed to create presentation: {e.reason}",
                           status_code=status_code, details=error_details)

    def copy_presentation(self, presentation_id: str,
                          title: Optional[str] = None) -> Presentation:
        """
        Create a copy of an existing presentation.

        Args:
            presentation_id: The ID of the presentation to copy.
            title: The title for the new copy. If None, uses "Copy of [original title]".

        Returns:
            A Presentation object representing the copied presentation.

        Raises:
            APIError: If the presentation could not be copied.
        """
        try:
            # First, get the original presentation to get its title
            if title is None:
                original = self.get_presentation(presentation_id)
                title = f"Copy of {original.title}"

            # Copy the file using Drive API
            body = {"name": title}
            drive_response = self._drive_service.files().copy(
                fileId=presentation_id, body=body).execute()

            # Get the new presentation ID and retrieve the full presentation
            new_presentation_id = drive_response.get("id")
            return self.get_presentation(new_presentation_id)

        except HttpError as e:
            status_code = e.resp.status
            error_details = json.loads(e.content.decode('utf-8'))
            raise APIError(f"Failed to copy presentation: {e.reason}",
                           status_code=status_code, details=error_details)

    def batch_update(self, presentation_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a batch update request against the presentation.

        Args:
            presentation_id: The ID of the presentation to update.
            requests: A list of request dictionaries to execute.

        Returns:
            The response from the API.

        Raises:
            APIError: If the batch update failed.
        """
        try:
            response = self._slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests}
            ).execute()
            return response
        except HttpError as e:
            status_code = e.resp.status
            try:
                error_details = json.loads(e.content.decode('utf-8'))
            except json.JSONDecodeError:
                error_details = {"raw_content": e.content.decode('utf-8')}

            raise APIError(f"Batch update failed: {e.reason}",
                           status_code=status_code, details=error_details)

    def create_slide(self, presentation_id: str,
                     slide_layout_id: Optional[str] = None,
                     insertion_index: Optional[int] = None) -> Slide:
        """
        Create a new slide in a presentation.

        Args:
            presentation_id: The ID of the presentation.
            slide_layout_id: The ID of the slide layout to use. If None, uses default layout.
            insertion_index: The index to insert the slide at. If None, appends to the end.

        Returns:
            A Slide object representing the newly created slide.

        Raises:
            APIError: If the slide could not be created.
        """
        create_request = {}

        if insertion_index is not None:
            create_request["insertionIndex"] = insertion_index

        if slide_layout_id is not None:
            create_request["slideLayoutReference"] = {"layoutId": slide_layout_id}

        try:
            response = self.batch_update(
                presentation_id,
                [{"createSlide": create_request}]
            )

            # Extract slide ID from response
            slide_id = response["replies"][0]["createSlide"]["objectId"]

            # Get the slide details
            return self.get_slide(presentation_id, slide_id)

        except APIError as e:
            # Enhance the error message
            raise APIError(f"Failed to create slide: {str(e)}",
                           status_code=e.status_code, details=e.details)

    def get_slide(self, presentation_id: str, slide_id: str) -> Slide:
        """
        Get a slide by ID.

        Args:
            presentation_id: The ID of the presentation.
            slide_id: The ID of the slide to retrieve.

        Returns:
            A Slide object representing the retrieved slide.

        Raises:
            APIError: If the slide could not be retrieved.
        """
        try:
            response = self._slides_service.presentations().pages().get(
                presentationId=presentation_id,
                pageObjectId=slide_id
            ).execute()

            # Create a slide from the response
            slide = Slide.from_api_format(response)

            # Set the presentation ID on the slide
            slide._presentation_id = presentation_id

            return slide

        except HttpError as e:
            status_code = e.resp.status
            error_details = json.loads(e.content.decode('utf-8'))

            if status_code == 404:
                raise APIError(f"Slide not found: {slide_id}",
                               status_code=status_code, details=error_details)
            else:
                raise APIError(f"Failed to get slide: {e.reason}",
                               status_code=status_code, details=error_details)

    def duplicate_slide(self, presentation_id: str, slide_id: str) -> Slide:
        """
        Duplicate a slide in a presentation.

        Args:
            presentation_id: The ID of the presentation.
            slide_id: The ID of the slide to duplicate.

        Returns:
            A Slide object representing the duplicated slide.

        Raises:
            APIError: If the slide could not be duplicated.
        """
        try:
            response = self.batch_update(
                presentation_id,
                [{"duplicateObject": {"objectId": slide_id}}]
            )

            # Extract duplicated slide ID
            duplicated_slide_id = response["replies"][0]["duplicateObject"]["objectId"]

            # Get the duplicated slide
            return self.get_slide(presentation_id, duplicated_slide_id)

        except APIError as e:
            # Enhance the error message
            raise APIError(f"Failed to duplicate slide: {str(e)}",
                           status_code=e.status_code, details=e.details)

    def delete_slide(self, presentation_id: str, slide_id: str) -> None:
        """
        Delete a slide from a presentation.

        Args:
            presentation_id: The ID of the presentation.
            slide_id: The ID of the slide to delete.

        Raises:
            APIError: If the slide could not be deleted.
        """
        try:
            self.batch_update(
                presentation_id,
                [{"deleteObject": {"objectId": slide_id}}]
            )
        except APIError as e:
            # Enhance the error message
            raise APIError(f"Failed to delete slide: {str(e)}",
                           status_code=e.status_code, details=e.details)

    def move_slide(self, presentation_id: str, slide_id: str, insertion_index: int) -> None:
        """
        Move a slide to a new position in the presentation.

        Args:
            presentation_id: The ID of the presentation.
            slide_id: The ID of the slide to move.
            insertion_index: The index to move the slide to.

        Raises:
            APIError: If the slide could not be moved.
        """
        try:
            self.batch_update(
                presentation_id,
                [{
                    "updateSlidesPosition": {
                        "slideObjectIds": [slide_id],
                        "insertionIndex": insertion_index
                    }
                }]
            )
        except APIError as e:
            # Enhance the error message
            raise APIError(f"Failed to move slide: {str(e)}",
                           status_code=e.status_code, details=e.details)

    def create_batch_request(self, presentation_id: str) -> BatchRequest:
        """
        Create a batch request for the specified presentation.

        This allows collecting multiple operations and executing them in a single batch.

        Args:
            presentation_id: The ID of the presentation to create a batch request for.

        Returns:
            A BatchRequest object for the specified presentation.
        """
        return BatchRequest(self, presentation_id)

    def create_presentation_from_json(self, json_data: Union[Dict[str, Any], str],
                                      title: Optional[str] = None) -> Presentation:
        """
        Create a new presentation from JSON data.

        Args:
            json_data: A dictionary with JSON data or a path to a JSON file
            title: The title for the new presentation. If None, uses the title from JSON

        Returns:
            A Presentation object representing the created presentation

        Raises:
            FileNotFoundError: If json_data is a string and the file is not found
            json.JSONDecodeError: If json_data is a string and the file contains invalid JSON
            ValueError: If json_data is neither a dictionary nor a string
            APIError: If an error occurred while creating the presentation
        """
        # Load JSON from file if a path is provided
        if isinstance(json_data, str):
            try:
                with open(json_data, 'r', encoding='utf-8') as f:
                    json_dict = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"JSON file not found: {json_data}")
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"JSON parsing error: {e.msg}", e.doc, e.pos)
        elif isinstance(json_data, dict):
            json_dict = json_data
        else:
            raise ValueError("json_data must be a dictionary or a path to a JSON file")

        # Get the title from JSON if not specified
        if title is None and "title" in json_dict:
            title = json_dict.get("title", "Imported Presentation")
        elif title is None:
            title = "Imported Presentation"

        # Create a new presentation
        presentation = self.create_presentation(title)

        # Set the client for the presentation
        presentation = presentation.with_client(self)

        # Process slides from JSON
        if "slides" in json_dict:
            # Estimate the workload
            total_elements = 0
            for slide_data in json_dict["slides"]:
                if "pageElements" in slide_data:
                    total_elements += len(slide_data["pageElements"])

            print(f"Found {len(json_dict['slides'])} slides and {total_elements} elements")
            print("Creating the presentation may take time due to API limits (60 requests/min)")

            # Process each slide with rate limiting
            for i, slide_data in enumerate(json_dict["slides"]):
                print(f"Processing slide {i + 1} of {len(json_dict['slides'])}...")

                # Add a delay to comply with API quota (60 requests/min)
                # Delay between slides to avoid exceeding the quota
                if i > 0:
                    time.sleep(1)  # 1 second delay between slides

                try:
                    # Create a new slide
                    slide = presentation.create_slide()

                    # Process slide elements
                    if "pageElements" in slide_data:
                        for j, element_data in enumerate(slide_data["pageElements"]):
                            # Add delay between element creations
                            if j > 0 and j % 10 == 0:  # Pause every 10 elements
                                print(f"  Pausing to comply with API limits...")
                                time.sleep(2)  # 2 seconds pause

                            try:
                                self._create_element_with_retry(
                                    presentation.presentation_id,
                                    slide.object_id,
                                    element_data
                                )
                            except Exception as e:
                                print(f"  Error creating element {j + 1}: {str(e)}")
                except Exception as e:
                    print(f"Error creating slide {i + 1}: {str(e)}")
                    # Continue with the next slide

        # Refresh the presentation to get updated data
        presentation.refresh()

        return presentation

    @retry(
        retry=retry_if_exception_type((APIError, HttpError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _create_element_with_retry(self, presentation_id: str, slide_id: str,
                                   element_data: Dict[str, Any]) -> Optional[str]:
        """
        Create an element with automatic retries for quota errors.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide ID
            element_data: The element data from JSON

        Returns:
            The created element ID or None in case of error
        """
        try:
            return self._create_element_from_json(presentation_id, slide_id, element_data)
        except APIError as e:
            # Check if the error is related to quota exceeded
            if "Quota exceeded" in str(e) or "RATE_LIMIT_EXCEEDED" in str(e):
                print(f"  API quota exceeded, waiting before retry...")
                # Wait longer before retrying (tenacity will automatically add delay)
                # Retry will be performed automatically by the retry decorator
            raise

    def _create_element_from_json(self, presentation_id: str, slide_id: str,
                                  element_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a slide element from JSON data.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide ID
            element_data: The element data from JSON

        Returns:
            The created element ID or None in case of error
        """
        try:
            # Get common element properties
            position = element_data.get("transform", {})
            size = element_data.get("size", {})

            # Ensure transform contains all necessary properties
            if "scaleX" not in position:
                position["scaleX"] = 1.0
            if "scaleY" not in position:
                position["scaleY"] = 1.0

            # Determine element type and create it
            if "shape" in element_data:
                return self._create_shape_from_json(
                    presentation_id, slide_id, element_data, position, size
                )
            elif "image" in element_data:
                return self._create_image_from_json(
                    presentation_id, slide_id, element_data, position, size
                )
            elif "table" in element_data:
                return self._create_table_from_json(
                    presentation_id, slide_id, element_data, position, size
                )
            elif "video" in element_data:
                return self._create_video_from_json(
                    presentation_id, slide_id, element_data, position, size
                )
            elif "line" in element_data:
                return self._create_line_from_json(
                    presentation_id, slide_id, element_data, position, size
                )
            elif "elementGroup" in element_data:
                return self._create_group_from_json(
                    presentation_id, slide_id, element_data, position, size
                )
            elif "wordArt" in element_data:
                # WordArt processing is not fully implemented in the API
                logger.warning("WordArt elements are not currently supported")
                return None
            elif "sheetsChart" in element_data:
                # Sheets Chart processing requires additional Google Sheets integration
                logger.warning("Sheets Chart elements are not currently supported")
                return None
            else:
                logger.warning(f"Unknown element type: {element_data.keys()}")
                return None

        except Exception as e:
            logger.error(f"Error creating element: {e}")
            return None

    def _create_video_from_json(self, presentation_id: str, slide_id: str,
                                element_data: Dict[str, Any], position: Dict[str, Any],
                                size: Dict[str, Any]) -> Optional[str]:
        """
        Create a video element from JSON data.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide ID
            element_data: The element data from JSON
            position: The position data of the element
            size: The size data of the element

        Returns:
            The created element ID or None in case of error
        """
        from gslides_templater.models.element import Video

        video_data = element_data["video"]
        video_id = video_data.get("id")
        source_type = video_data.get("source", "YOUTUBE")  # YouTube by default

        if not video_id:
            logger.warning("Video ID not found in JSON")
            return None

        try:
            element = Video.create(
                self,
                presentation_id,
                slide_id,
                source_type=source_type,
                video_id=video_id,
                position=position,
                size=size
            )

            # Set additional properties if they exist
            if element and "autoPlay" in video_data:
                element.set_autoplay(video_data["autoPlay"])

            return element.object_id if element else None
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            return None

    def _create_line_from_json(self, presentation_id: str, slide_id: str,
                               element_data: Dict[str, Any], position: Dict[str, Any],
                               size: Dict[str, Any]) -> Optional[str]:
        """
        Create a line element from JSON data.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide ID
            element_data: The element data from JSON
            position: The position data of the element
            size: The size data of the element

        Returns:
            The created element ID or None in case of error
        """
        from gslides_templater.models.element import Line

        line_data = element_data["line"]
        line_type = line_data.get("lineType", "STRAIGHT")

        # Calculate start and end positions of the line based on transform and size
        start_x = position.get("translateX", 0)
        start_y = position.get("translateY", 0)

        # Assume the line goes from the top-left corner to the bottom-right corner
        end_x = start_x + size.get("width", {}).get("magnitude", 0)
        end_y = start_y + size.get("height", {}).get("magnitude", 0)

        start_position = {
            "translateX": start_x,
            "translateY": start_y,
            "unit": position.get("unit", "PT")
        }

        end_position = {
            "translateX": end_x,
            "translateY": end_y,
            "unit": position.get("unit", "PT")
        }

        try:
            element = Line.create(
                self,
                presentation_id,
                slide_id,
                start_position=start_position,
                end_position=end_position,
                line_type=line_type
            )

            return element.object_id if element else None
        except Exception as e:
            logger.error(f"Error creating line: {e}")
            return None

    def _create_group_from_json(self, presentation_id: str, slide_id: str,
                                element_data: Dict[str, Any], position: Dict[str, Any],
                                size: Dict[str, Any]) -> Optional[str]:
        """
        Create a group element from JSON data.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide ID
            element_data: The element data from JSON
            position: The position data of the element
            size: The size data of the element

        Returns:
            The created element ID or None in case of error
        """
        # Note: Google Slides API doesn't allow direct group creation
        # First create individual elements, then group them

        group_data = element_data["elementGroup"]
        children = group_data.get("children", [])

        if not children:
            logger.warning("Group contains no child elements")
            return None

        # Create child elements
        child_ids = []
        for child_data in children:
            child_id = self._create_element_from_json(
                presentation_id,
                slide_id,
                child_data
            )
            if child_id:
                child_ids.append(child_id)

        if not child_ids:
            logger.warning("Failed to create any child elements in the group")
            return None

        # Group the elements
        batch = self.create_batch_request(presentation_id)

        # Unique ID for the group
        group_id = f"group_{uuid.uuid4().hex[:8]}"

        batch.add_request({
            "groupObjects": {
                "objectIds": child_ids,
                "groupObjectId": group_id
            }
        })

        try:
            batch.execute()
            return group_id
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            return None

    def _create_shape_from_json(self, presentation_id: str, slide_id: str,
                                element_data: Dict[str, Any], position: Dict[str, Any],
                                size: Dict[str, Any]) -> Optional[str]:
        """
        Create a shape element from JSON data.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide ID
            element_data: The element data from JSON
            position: The position data of the element
            size: The size data of the element

        Returns:
            The created element ID or None in case of error
        """

        shape_data = element_data["shape"]
        shape_type = shape_data.get("shapeType")

        # Extract text if it exists
        text = ""
        if "text" in shape_data:
            text_elements = shape_data["text"].get("textElements", [])
            for text_element in text_elements:
                if "textRun" in text_element:
                    text += text_element["textRun"].get("content", "")

        # Create element based on type
        if shape_type == "TEXT_BOX":
            element = TextBox.create(
                self,
                presentation_id,
                slide_id,
                text=text,
                position=position,
                size=size
            )
            return element.object_id if element else None
        else:
            # Other shape types
            # Create a universal Shape element with the specified type
            batch = self.create_batch_request(presentation_id)

            # Generate ID for the new element
            object_id = f"shape_{uuid.uuid4().hex[:8]}"

            # Add request to create shape
            batch.add_request({
                "createShape": {
                    "objectId": object_id,
                    "shapeType": shape_type,
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": size,
                        "transform": position
                    }
                }
            })

            # Add text if it exists
            if text:
                batch.add_request({
                    "insertText": {
                        "objectId": object_id,
                        "insertionIndex": 0,
                        "text": text
                    }
                })

            # Execute requests
            try:
                batch.execute()

                # Get the slide to retrieve the created element
                slide = self.get_slide(presentation_id, slide_id)

                # Find the created element
                for element in slide.page_elements:
                    if element.object_id == object_id:
                        return object_id

            except Exception as e:
                logger.error(f"Error creating shape of type {shape_type}: {e}")

            return None

    def _create_image_from_json(self, presentation_id: str, slide_id: str,
                                element_data: Dict[str, Any], position: Dict[str, Any],
                                size: Dict[str, Any]) -> Optional[str]:
        """
        Create an image element from JSON data.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide ID
            element_data: The element data from JSON
            position: The position data of the element
            size: The size data of the element

        Returns:
            The created element ID or None in case of error
        """
        from gslides_templater.models.element import Image

        image_data = element_data["image"]
        url = image_data.get("contentUrl")

        if not url:
            logger.warning("Image URL not found in JSON")
            return None

        element = Image.create(
            self,
            presentation_id,
            slide_id,
            url=url,
            position=position,
            size=size
        )

        return element.object_id if element else None

    def _create_table_from_json(self, presentation_id: str, slide_id: str,
                                element_data: Dict[str, Any], position: Dict[str, Any],
                                size: Dict[str, Any]) -> Optional[str]:
        """
        Create a table element from JSON data.

        Args:
            presentation_id: The presentation ID
            slide_id: The slide ID
            element_data: The element data from JSON
            position: The position data of the element
            size: The size data of the element

        Returns:
            The created element ID or None in case of error
        """

        table_data = element_data["table"]
        rows = table_data.get("rows", 0)
        columns = table_data.get("columns", 0)

        if rows <= 0 or columns <= 0:
            logger.warning(f"Invalid table dimensions: {rows}x{columns}")
            return None

        element = Table.create(
            self,
            presentation_id,
            slide_id,
            rows=rows,
            columns=columns,
            position=position,
            size=size
        )

        if not element:
            return None

        # Fill table cells if data exists
        if "tableRows" in table_data:
            table_rows = table_data["tableRows"]
            for row_idx, row_data in enumerate(table_rows):
                if row_idx >= rows:
                    break

                if "tableCells" in row_data:
                    table_cells = row_data["tableCells"]
                    for col_idx, cell_data in enumerate(table_cells):
                        if col_idx >= columns:
                            break

                        # Extract text from the cell
                        text = ""
                        if "text" in cell_data:
                            text_elements = cell_data["text"].get("textElements", [])
                            for text_element in text_elements:
                                if "textRun" in text_element:
                                    text += text_element["textRun"].get("content", "")

                        # Set cell text
                        if text:
                            try:
                                element.set_cell_text(row_idx, col_idx, text)
                            except Exception as e:
                                logger.warning(f"Error setting cell text: {e}")

        return element.object_id
