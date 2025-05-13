"""
Batch request handling for Google Slides API.
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gslides_templater.client import SlidesClient


class BatchRequest:
    """
    Manages a batch of requests to the Google Slides API.

    This class allows collecting multiple operations and executing them in a single
    batch request, which is more efficient than making individual requests.
    """

    def __init__(self, client: 'SlidesClient', presentation_id: str):
        """
        Initialize a batch request.

        Args:
            client: The SlidesClient to use for executing the batch.
            presentation_id: The ID of the presentation to operate on.
        """
        self.client = client
        self.presentation_id = presentation_id
        self.requests: List[Dict[str, Any]] = []

    def add_request(self, request: Dict[str, Any]) -> 'BatchRequest':
        """
        Add a request to the batch.

        Args:
            request: The request to add to the batch.

        Returns:
            self for method chaining.
        """
        self.requests.append(request)
        return self

    def create_slide(self,
                     slide_layout_id: Optional[str] = None,
                     insertion_index: Optional[int] = None) -> 'BatchRequest':
        """
        Add a request to create a slide.

        Args:
            slide_layout_id: The ID of the slide layout to use. If None, uses default layout.
            insertion_index: The index to insert the slide at. If None, appends to the end.

        Returns:
            self for method chaining.
        """
        request = {"createSlide": {}}

        if insertion_index is not None:
            request["createSlide"]["insertionIndex"] = insertion_index

        if slide_layout_id is not None:
            request["createSlide"]["slideLayoutReference"] = {"layoutId": slide_layout_id}

        return self.add_request(request)

    def duplicate_object(self, object_id: str) -> 'BatchRequest':
        """
        Add a request to duplicate an object.

        Args:
            object_id: The ID of the object to duplicate.

        Returns:
            self for method chaining.
        """
        request = {"duplicateObject": {"objectId": object_id}}
        return self.add_request(request)

    def delete_object(self, object_id: str) -> 'BatchRequest':
        """
        Add a request to delete an object.

        Args:
            object_id: The ID of the object to delete.

        Returns:
            self for method chaining.
        """
        request = {"deleteObject": {"objectId": object_id}}
        return self.add_request(request)

    def move_slide(self, slide_id: str, insertion_index: int) -> 'BatchRequest':
        """
        Add a request to move a slide to a new position.

        Args:
            slide_id: The ID of the slide to move.
            insertion_index: The index to move the slide to.

        Returns:
            self for method chaining.
        """
        request = {
            "updateSlidesPosition": {
                "slideObjectIds": [slide_id],
                "insertionIndex": insertion_index
            }
        }
        return self.add_request(request)

    def replace_all_text(self, text: str, replacement: str,
                         match_case: bool = True) -> 'BatchRequest':
        """
        Add a request to replace all occurrences of a text string.

        Args:
            text: The text to find.
            replacement: The text to replace it with.
            match_case: Whether to match case.

        Returns:
            self for method chaining.
        """
        request = {
            "replaceAllText": {
                "replaceText": replacement,
                "containsText": {
                    "text": text,
                    "matchCase": match_case
                }
            }
        }
        return self.add_request(request)

    def replace_placeholder_text(self, placeholder_id: str,
                                 replacement: str) -> 'BatchRequest':
        """
        Add a request to replace text in a placeholder shape.

        Args:
            placeholder_id: The ID of the placeholder shape.
            replacement: The text to replace the placeholder with.

        Returns:
            self for method chaining.
        """
        # First, insert the text at the beginning
        self.add_request({
            "insertText": {
                "objectId": placeholder_id,
                "insertionIndex": 0,
                "text": replacement
            }
        })

        # Then, delete any existing text
        request = {
            "deleteText": {
                "objectId": placeholder_id,
                "textRange": {
                    "startIndex": len(replacement),
                    "type": "FROM_START_INDEX"
                }
            }
        }
        return self.add_request(request)

    def replace_image(self, image_id: str, url: str) -> 'BatchRequest':
        """
        Add a request to replace an image.

        Args:
            image_id: The ID of the image to replace.
            url: The URL of the new image.

        Returns:
            self for method chaining.
        """
        request = {
            "replaceImage": {
                "imageObjectId": image_id,
                "url": url
            }
        }
        return self.add_request(request)

    def execute(self) -> Dict[str, Any]:
        """
        Execute the batch request.

        Returns:
            The response from the API.

        Raises:
            APIError: If the batch request could not be executed.
        """
        if not self.requests:
            return {"replies": []}

        response = self.client.batch_update(self.presentation_id, self.requests)

        # Clear the requests after execution
        self.requests = []

        return response

    def create_video(self, slide_id: str, source_type: str, video_id: str,
                     position: Dict[str, Any], size: Dict[str, Any]) -> 'BatchRequest':
        """
        Add a request to create a video.

        Args:
            slide_id: The ID of the slide.
            source_type: The source type of the video ('YOUTUBE' or 'DRIVE').
            video_id: The ID of the video.
            position: The position of the video.
            size: The size of the video.

        Returns:
            self for method chaining.
        """
        request = {
            "createVideo": {
                "source": source_type,
                "id": video_id,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": size,
                    "transform": position
                }
            }
        }
        return self.add_request(request)

    def update_video_properties(self, video_id: str,
                                properties: Dict[str, Any],
                                fields: str) -> 'BatchRequest':
        """
        Add a request to update video properties.

        Args:
            video_id: The ID of the video element.
            properties: The properties to update.
            fields: Comma-separated list of fields to update.

        Returns:
            self for method chaining.
        """
        request = {
            "updateVideoProperties": {
                "objectId": video_id,
                "videoProperties": properties,
                "fields": fields
            }
        }
        return self.add_request(request)
