"""
Element models for Google Slides Templater.
"""
import uuid
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING, ForwardRef
from pydantic import Field, model_validator

from gslides_templater.models.base import APIObject
from gslides_templater.models.enums import ElementType, ShapeType

# Используем ForwardRef для циклических зависимостей
Slide = ForwardRef('Slide')
Presentation = ForwardRef('Presentation')

if TYPE_CHECKING:
    from gslides_templater.client import SlidesClient
    from gslides_templater.models.slide import Slide
    from gslides_templater.models.presentation import Presentation


class Transform(APIObject):
    """Transformation applied to an element."""

    scale_x: float = Field(1.0, alias="scaleX")
    scale_y: float = Field(1.0, alias="scaleY")
    translate_x: float = Field(0.0, alias="translateX")
    translate_y: float = Field(0.0, alias="translateY")
    shear_x: Optional[float] = Field(None, alias="shearX")
    shear_y: Optional[float] = Field(None, alias="shearY")
    unit: Optional[str] = None


class TextStyle(APIObject):
    """Style for text."""

    font_family: Optional[str] = Field(None, alias="fontFamily")
    font_size: Optional[Dict[str, Any]] = Field(None, alias="fontSize")
    text_color: Optional[Dict[str, Any]] = Field(None, alias="foregroundColor")
    background_color: Optional[Dict[str, Any]] = Field(None, alias="backgroundColor")
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    strikethrough: Optional[bool] = None
    link: Optional[Dict[str, str]] = None


class ParagraphStyle(APIObject):
    """Style for paragraphs."""

    alignment: Optional[str] = None
    line_spacing: Optional[float] = Field(None, alias="lineSpacing")
    space_above: Optional[Dict[str, Any]] = Field(None, alias="spaceAbove")
    space_below: Optional[Dict[str, Any]] = Field(None, alias="spaceBelow")
    indent_start: Optional[Dict[str, Any]] = Field(None, alias="indentStart")
    indent_end: Optional[Dict[str, Any]] = Field(None, alias="indentEnd")
    indent_first_line: Optional[Dict[str, Any]] = Field(None, alias="indentFirstLine")
    direction: Optional[str] = None  # e.g., "LEFT_TO_RIGHT"


class TextElement(APIObject):
    """Element within text content."""

    start_index: Optional[int] = Field(None, alias="startIndex")
    end_index: int = Field(..., alias="endIndex")
    text_run: Optional[Dict[str, Any]] = Field(None, alias="textRun")
    paragraph_marker: Optional[Dict[str, Any]] = Field(None, alias="paragraphMarker")
    auto_text: Optional[Dict[str, Any]] = Field(None, alias="autoText")

    @property
    def content(self) -> Optional[str]:
        """Get the text content of this element."""
        if self.text_run:
            return self.text_run.get("content")
        return None

    @property
    def style(self) -> Optional[TextStyle]:
        """Get the text style of this element."""
        if self.text_run and "style" in self.text_run:
            return TextStyle.from_api_format(self.text_run["style"])
        return None


class TextContent(APIObject):
    """Text content with its elements."""

    text_elements: List[TextElement] = Field(default_factory=list, alias="textElements")
    lists: Optional[Dict[str, Any]] = None

    @property
    def plain_text(self) -> str:
        """Get the plain text content."""
        text = ""
        for element in self.text_elements:
            if element.content:
                text += element.content
        return text


class Element(APIObject):
    """
    Base class for elements in a slide.

    Elements can be shapes, images, videos, tables, etc.
    """

    size: Dict[str, Any] = Field(default_factory=dict)
    transform: Optional[Transform] = None
    title: Optional[str] = None
    description: Optional[str] = None

    # Element type-specific fields
    shape: Optional[Dict[str, Any]] = None
    image: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None
    table: Optional[Dict[str, Any]] = None
    line: Optional[Dict[str, Any]] = None
    word_art: Optional[Dict[str, Any]] = Field(None, alias="wordArt")
    sheets_chart: Optional[Dict[str, Any]] = Field(None, alias="sheetsChart")
    element_group: Optional[Dict[str, Any]] = Field(None, alias="elementGroup")

    # References for operations - not part of the API model
    _client: Optional['SlidesClient'] = None
    _presentation_id: Optional[str] = None
    _slide: Optional['Slide'] = None

    @property
    def element_type(self) -> Optional[str]:
        """Determine the type of this element."""
        for element_type in ElementType:
            if getattr(self, element_type.value, None) is not None:
                return element_type.value
        return None

    @property
    def text_content(self) -> Optional[TextContent]:
        """Get the text content of a shape element."""
        if self.shape and "text" in self.shape:
            return TextContent.from_api_format(self.shape["text"])
        return None

    @property
    def text(self) -> Optional[str]:
        """Get the plain text content of a shape element."""
        if self.text_content:
            return self.text_content.plain_text
        return None

    def delete(self) -> Dict[str, Any]:
        """
        Delete this element from the slide.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the delete request
        batch.add_request({
            "deleteObject": {
                "objectId": self.object_id
            }
        })

        # Execute the batch request
        return batch.execute()

    def replace_text(self, text: str, replacement: str, match_case: bool = True) -> Dict[str, Any]:
        """
        Replace text in this element.

        Args:
            text: The text to find.
            replacement: The text to replace it with.
            match_case: Whether to match case.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
            ValueError: If this element does not support text.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        if self.element_type != ElementType.SHAPE.value:
            raise ValueError(f"Element of type {self.element_type} does not support text.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the replace text request
        batch.add_request({
            "replaceAllText": {
                "replaceText": replacement,
                "objectIds": [self.object_id],
                "containsText": {
                    "text": text,
                    "matchCase": match_case
                }
            }
        })

        # Execute the batch request
        return batch.execute()

    def set_text(self, text: str) -> Dict[str, Any]:
        """
        Set the text of this element.

        Args:
            text: The text to set.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
            ValueError: If this element does not support text.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        if self.element_type != ElementType.SHAPE.value:
            raise ValueError(f"Element of type {self.element_type} does not support text.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # First delete any existing text
        batch.add_request({
            "deleteText": {
                "objectId": self.object_id,
                "textRange": {
                    "type": "ALL"
                }
            }
        })

        # Then insert the new text
        batch.add_request({
            "insertText": {
                "objectId": self.object_id,
                "insertionIndex": 0,
                "text": text
            }
        })

        # Execute the batch request
        return batch.execute()

    def duplicate(self) -> Optional['Element']:
        """
        Duplicate this element.

        Returns:
            The duplicated element, or None if duplication fails.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the duplicate request
        batch.add_request({
            "duplicateObject": {
                "objectId": self.object_id
            }
        })

        # Execute the batch request
        response = batch.execute()

        # Extract the duplicated element ID
        if "replies" in response and len(response["replies"]) > 0:
            new_id = response["replies"][0].get("duplicateObject", {}).get("objectId")

            # Refresh the slide to get the duplicated element
            if self._slide:
                self._slide.refresh()
                return self._slide.get_element(new_id)

        return None


class Shape(Element):
    """Shape element in a slide."""

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Ensure shape field exists
        if not self.shape:
            self.shape = {}

    @property
    def shape_type(self) -> Optional[ShapeType]:
        """Get the type of this shape."""
        if self.shape and "shapeType" in self.shape:
            return ShapeType(self.shape["shapeType"])
        return None

    @property
    def is_placeholder(self) -> bool:
        """Check if this shape is a placeholder."""
        return self.shape and "placeholder" in self.shape

    @property
    def placeholder_type(self) -> Optional[str]:
        """Get the type of this placeholder."""
        if self.is_placeholder:
            return self.shape["placeholder"].get("type")
        return None

    @property
    def placeholder_index(self) -> Optional[int]:
        """Get the index of this placeholder."""
        if self.is_placeholder:
            return self.shape["placeholder"].get("index")
        return None


class TextBox(Shape):
    """Text box element in a slide."""

    @classmethod
    def create(cls, client: 'SlidesClient', presentation_id: str, slide_id: str,
               text: str = "", position: Dict[str, Any] = None,
               size: Dict[str, Any] = None) -> Optional['TextBox']:
        """
        Create a text box element.

        Args:
            client: The SlidesClient to use.
            presentation_id: The ID of the presentation.
            slide_id: The ID of the slide.
            text: The text to add.
            position: The position of the text box.
            size: The size of the text box.

        Returns:
            The created text box element, or None if creation fails.
        """
        if not position:
            # Исправленный формат transform - добавляем scaleX и scaleY
            position = {
                "translateX": 100,
                "translateY": 100,
                "scaleX": 1.0,  # Важно: добавляем scaleX со значением 1.0
                "scaleY": 1.0,  # Важно: добавляем scaleY со значением 1.0
                "unit": "PT"
            }

        if not size:
            size = {
                "width": {"magnitude": 300, "unit": "PT"},
                "height": {"magnitude": 100, "unit": "PT"}
            }

        # Create a batch request
        batch = client.create_batch_request(presentation_id)

        # Add the create text box request
        batch.add_request({
            "createShape": {
                "objectId": f"textbox_{uuid.uuid4().hex[:8]}",
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": size,
                    "transform": position
                }
            }
        })

        # Execute the batch request
        response = batch.execute()

        # Extract the text box ID
        if "replies" in response and len(response["replies"]) > 0:
            textbox_id = response["replies"][0].get("createShape", {}).get("objectId")

            # If text is provided, add it to the text box
            if text:
                batch = client.create_batch_request(presentation_id)

                batch.add_request({
                    "insertText": {
                        "objectId": textbox_id,
                        "insertionIndex": 0,
                        "text": text
                    }
                })

                batch.execute()

            # Get the slide to retrieve the created text box
            slide = client.get_slide(presentation_id, slide_id)

            # Find the text box element
            for element in slide.page_elements:
                if element.object_id == textbox_id:
                    return cls(**element.to_api_format())

        return None


class Image(Element):
    """Image element in a slide."""

    @property
    def source_url(self) -> Optional[str]:
        """Get the source URL of this image."""
        return self.image.get("sourceUrl") if self.image else None

    @property
    def content_url(self) -> Optional[str]:
        """Get the content URL of this image."""
        return self.image.get("contentUrl") if self.image else None

    @classmethod
    def create(cls, client: 'SlidesClient', presentation_id: str, slide_id: str,
               url: str, position: Dict[str, Any] = None,
               size: Dict[str, Any] = None) -> Optional['Image']:
        """
        Create an image element.

        Args:
            client: The SlidesClient to use.
            presentation_id: The ID of the presentation.
            slide_id: The ID of the slide.
            url: The URL of the image.
            position: The position of the image.
            size: The size of the image.

        Returns:
            The created image element, or None if creation fails.
        """
        if not position:
            position = {
                "translateX": 100,
                "translateY": 100,
                "scaleX": 1.0,  # Добавляем scaleX
                "scaleY": 1.0,  # Добавляем scaleY
                "unit": "PT"
            }

        if not size:
            size = {"width": {"magnitude": 300, "unit": "PT"},
                    "height": {"magnitude": 200, "unit": "PT"}}

        # Create a batch request
        batch = client.create_batch_request(presentation_id)

        # Add the create image request
        batch.add_request({
            "createImage": {
                "url": url,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": size,
                    "transform": position
                }
            }
        })

        # Execute the batch request
        response = batch.execute()

        # Extract the image ID
        if "replies" in response and len(response["replies"]) > 0:
            image_id = response["replies"][0].get("createImage", {}).get("objectId")

            # Get the slide to retrieve the created image
            slide = client.get_slide(presentation_id, slide_id)

            # Find the image element
            for element in slide.page_elements:
                if element.object_id == image_id:
                    return cls(**element.to_api_format())

        return None

    def replace_with_image(self, url: str) -> Dict[str, Any]:
        """
        Replace this image with another image.

        Args:
            url: The URL of the new image.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
            ValueError: If this element is not an image.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        if self.element_type != ElementType.IMAGE.value:
            raise ValueError(f"Element of type {self.element_type} is not an image.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the replace image request
        batch.add_request({
            "replaceImage": {
                "imageObjectId": self.object_id,
                "url": url
            }
        })

        # Execute the batch request
        return batch.execute()


class Table(Element):
    """Table element in a slide."""

    @property
    def rows(self) -> int:
        """Get the number of rows in this table."""
        return self.table.get("rows", 0) if self.table else 0

    @property
    def columns(self) -> int:
        """Get the number of columns in this table."""
        return self.table.get("columns", 0) if self.table else 0

    @property
    def table_rows(self) -> List[Dict[str, Any]]:
        """Get the rows of this table."""
        return self.table.get("tableRows", []) if self.table else []

    @classmethod
    def create(cls, client: 'SlidesClient', presentation_id: str, slide_id: str,
               rows: int, columns: int, position: Dict[str, Any] = None,
               size: Dict[str, Any] = None) -> Optional['Table']:
        """
        Create a table element.

        Args:
            client: The SlidesClient to use.
            presentation_id: The ID of the presentation.
            slide_id: The ID of the slide.
            rows: The number of rows.
            columns: The number of columns.
            position: The position of the table.
            size: The size of the table.

        Returns:
            The created table element, or None if creation fails.
        """
        if not position:
            position = {"translateX": 100, "translateY": 100, "unit": "PT"}

        if not size:
            size = {"width": {"magnitude": 400, "unit": "PT"},
                    "height": {"magnitude": 200, "unit": "PT"}}

        # Create a batch request
        batch = client.create_batch_request(presentation_id)

        # Add the create table request
        batch.add_request({
            "createTable": {
                "rows": rows,
                "columns": columns,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": size,
                    "transform": position
                }
            }
        })

        # Execute the batch request
        response = batch.execute()

        # Extract the table ID
        if "replies" in response and len(response["replies"]) > 0:
            table_id = response["replies"][0].get("createTable", {}).get("objectId")

            # Get the slide to retrieve the created table
            slide = client.get_slide(presentation_id, slide_id)

            # Find the table element
            for element in slide.page_elements:
                if element.object_id == table_id:
                    return cls(**element.to_api_format())

        return None

    def get_cell_text(self, row: int, column: int) -> Optional[str]:
        """
        Get the text in a table cell.

        Args:
            row: The row index (0-based).
            column: The column index (0-based).

        Returns:
            The text in the cell, or None if the cell does not exist.

        Raises:
            ValueError: If the row or column index is out of bounds.
        """
        if row < 0 or row >= self.rows:
            raise ValueError(f"Row index {row} out of bounds (0-{self.rows - 1}).")

        if column < 0 or column >= self.columns:
            raise ValueError(f"Column index {column} out of bounds (0-{self.columns - 1}).")

        # Get the cell
        table_rows = self.table_rows
        if row < len(table_rows):
            table_row = table_rows[row]
            table_cells = table_row.get("tableCells", [])

            if column < len(table_cells):
                table_cell = table_cells[column]
                text = table_cell.get("text", {})
                text_elements = text.get("textElements", [])

                # Combine text from all text elements
                result = ""
                for element in text_elements:
                    if "textRun" in element:
                        result += element["textRun"].get("content", "")

                return result

        return None

    def set_cell_text(self, row: int, column: int, text: str) -> Dict[str, Any]:
        """
        Set the text in a table cell.

        Args:
            row: The row index (0-based).
            column: The column index (0-based).
            text: The text to set.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
            ValueError: If the row or column index is out of bounds.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        if row < 0 or row >= self.rows:
            raise ValueError(f"Row index {row} out of bounds (0-{self.rows - 1}).")

        if column < 0 or column >= self.columns:
            raise ValueError(f"Column index {column} out of bounds (0-{self.columns - 1}).")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # First, delete any existing text in the cell
        batch.add_request({
            "deleteText": {
                "objectId": self.object_id,
                "cellLocation": {
                    "rowIndex": row,
                    "columnIndex": column
                },
                "textRange": {
                    "type": "ALL"
                }
            }
        })

        # Then, insert the new text
        batch.add_request({
            "insertText": {
                "objectId": self.object_id,
                "cellLocation": {
                    "rowIndex": row,
                    "columnIndex": column
                },
                "text": text,
                "insertionIndex": 0
            }
        })

        # Execute the batch request
        return batch.execute()


class Line(Element):
    """Line element in a slide."""

    @property
    def line_type(self) -> Optional[str]:
        """Get the type of this line."""
        return self.line.get("lineType") if self.line else None

    @classmethod
    def create(cls, client: 'SlidesClient', presentation_id: str, slide_id: str,
               start_position: Dict[str, Any], end_position: Dict[str, Any],
               line_type: str = "STRAIGHT") -> Optional['Line']:
        """
        Create a line element.

        Args:
            client: The SlidesClient to use.
            presentation_id: The ID of the presentation.
            slide_id: The ID of the slide.
            start_position: The start position of the line.
            end_position: The end position of the line.
            line_type: The type of line to create.

        Returns:
            The created line element, or None if creation fails.
        """
        # Calculate size and position
        width = abs(end_position["translateX"] - start_position["translateX"])
        height = abs(end_position["translateY"] - start_position["translateY"])

        # Position is at the top-left corner
        position = {
            "translateX": min(start_position["translateX"], end_position["translateX"]),
            "translateY": min(start_position["translateY"], end_position["translateY"]),
            "unit": start_position.get("unit", "PT")
        }

        size = {
            "width": {"magnitude": width, "unit": position["unit"]},
            "height": {"magnitude": height, "unit": position["unit"]}
        }

        # Create a batch request
        batch = client.create_batch_request(presentation_id)

        # Add the create line request
        batch.add_request({
            "createLine": {
                "lineCategory": line_type,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": size,
                    "transform": position
                }
            }
        })

        # Execute the batch request
        response = batch.execute()

        # Extract the line ID
        if "replies" in response and len(response["replies"]) > 0:
            line_id = response["replies"][0].get("createLine", {}).get("objectId")

            # Get the slide to retrieve the created line
            slide = client.get_slide(presentation_id, slide_id)

            # Find the line element
            for element in slide.page_elements:
                if element.object_id == line_id:
                    return cls(**element.to_api_format())

        return None


class Group(Element):
    """Group element in a slide."""

    @property
    def children(self) -> List[Dict[str, Any]]:
        """Get the children of this group."""
        return self.element_group.get("children", []) if self.element_group else []

    def ungroup(self) -> Dict[str, Any]:
        """
        Ungroup this group.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
            ValueError: If this element is not a group.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        if self.element_type != ElementType.GROUP.value:
            raise ValueError(f"Element of type {self.element_type} is not a group.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the ungroup request
        batch.add_request({
            "ungroup": {
                "objectId": self.object_id
            }
        })

        # Execute the batch request
        return batch.execute()


class Video(Element):
    """Video element in a slide."""

    @property
    def source_url(self) -> Optional[str]:
        """Get the source URL of this video."""
        return self.video.get("url") if self.video else None

    @property
    def source_type(self) -> Optional[str]:
        """Get the source type of this video."""
        return self.video.get("source") if self.video else None

    @property
    def id(self) -> Optional[str]:
        """Get the video ID."""
        return self.video.get("id") if self.video else None

    @classmethod
    def create(cls, client: 'SlidesClient', presentation_id: str, slide_id: str,
               source_type: str, video_id: str, position: Dict[str, Any] = None,
               size: Dict[str, Any] = None) -> Optional['Video']:
        """
        Create a video element.

        Args:
            client: The SlidesClient to use.
            presentation_id: The ID of the presentation.
            slide_id: The ID of the slide.
            source_type: The source type of the video ('YOUTUBE' or 'DRIVE').
            video_id: The ID of the video.
            position: The position of the video.
            size: The size of the video.

        Returns:
            The created video element, or None if creation fails.
        """
        if not position:
            position = {"translateX": 100, "translateY": 100, "unit": "PT"}

        if not size:
            size = {"width": {"magnitude": 320, "unit": "PT"},
                    "height": {"magnitude": 180, "unit": "PT"}}

        # Create a batch request
        batch = client.create_batch_request(presentation_id)

        # Add the create video request
        batch.add_request({
            "createVideo": {
                "source": source_type,
                "id": video_id,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": size,
                    "transform": position
                }
            }
        })

        # Execute the batch request
        response = batch.execute()

        # Extract the video ID
        if "replies" in response and len(response["replies"]) > 0:
            element_id = response["replies"][0].get("createVideo", {}).get("objectId")

            # Get the slide to retrieve the created video
            slide = client.get_slide(presentation_id, slide_id)

            # Find the video element
            for element in slide.page_elements:
                if element.object_id == element_id:
                    return cls(**element.to_api_format())

        return None

    def set_autoplay(self, autoplay: bool) -> Dict[str, Any]:
        """
        Set the autoplay property of this video.

        Args:
            autoplay: Whether the video should autoplay.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
            ValueError: If this element is not a video.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        if self.element_type != ElementType.VIDEO.value:
            raise ValueError(f"Element of type {self.element_type} is not a video.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the update video properties request
        batch.add_request({
            "updateVideoProperties": {
                "objectId": self.object_id,
                "videoProperties": {
                    "autoPlay": autoplay
                },
                "fields": "autoPlay"
            }
        })

        # Execute the batch request
        return batch.execute()

    def set_start_and_end_time(self, start_time: Optional[int] = None,
                               end_time: Optional[int] = None) -> Dict[str, Any]:
        """
        Set the start and end time of this video.

        Args:
            start_time: The start time in milliseconds.
            end_time: The end time in milliseconds.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
            ValueError: If this element is not a video.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        if self.element_type != ElementType.VIDEO.value:
            raise ValueError(f"Element of type {self.element_type} is not a video.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Prepare video properties
        video_properties = {}
        fields = []

        if start_time is not None:
            video_properties["start"] = start_time
            fields.append("start")

        if end_time is not None:
            video_properties["end"] = end_time
            fields.append("end")

        if not fields:
            return {}  # Nothing to update

        # Add the update video properties request
        batch.add_request({
            "updateVideoProperties": {
                "objectId": self.object_id,
                "videoProperties": video_properties,
                "fields": ",".join(fields)
            }
        })

        # Execute the batch request
        return batch.execute()

    def set_mute(self, mute: bool) -> Dict[str, Any]:
        """
        Set the mute property of this video.

        Args:
            mute: Whether the video should be muted.

        Returns:
            The response from the API.

        Raises:
            ValueError: If the client is not set.
            ValueError: If the presentation ID or element ID is not set.
            ValueError: If this element is not a video.
        """
        if not self._client:
            raise ValueError("Client not set.")

        if not self._presentation_id:
            raise ValueError("Presentation ID not set.")

        if not self.object_id:
            raise ValueError("Element ID not set.")

        if self.element_type != ElementType.VIDEO.value:
            raise ValueError(f"Element of type {self.element_type} is not a video.")

        # Create a batch request
        batch = self._client.create_batch_request(self._presentation_id)

        # Add the update video properties request
        batch.add_request({
            "updateVideoProperties": {
                "objectId": self.object_id,
                "videoProperties": {
                    "mute": mute
                },
                "fields": "mute"
            }
        })

        # Execute the batch request
        return batch.execute()
