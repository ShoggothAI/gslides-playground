from typing import Optional, Dict, Any, List
from enum import Enum

from gslides_api.domain import (
    GSlidesBaseModel,
    Transform,
    Shape,
    Table,
    Image,
    Size,
    Video,
    Line,
    WordArt,
    SheetsChart,
    SpeakerSpotlight,
    Group,
)
from gslides_api.execute import slides_batch_update
from gslides_api.utils import dict_to_dot_separated_field_list


class ElementKind(Enum):
    """Enumeration of possible page element kinds based on the Google Slides API.

    Reference: https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations.pages#pageelement
    """

    GROUP = "elementGroup"
    SHAPE = "shape"
    IMAGE = "image"
    VIDEO = "video"
    LINE = "line"
    TABLE = "table"
    WORD_ART = "wordArt"
    SHEETS_CHART = "sheetsChart"
    SPEAKER_SPOTLIGHT = "speakerSpotlight"


class PageElement(GSlidesBaseModel):
    """Represents an element on a slide."""

    objectId: str
    size: Size
    transform: Transform
    title: Optional[str] = None
    description: Optional[str] = None
    shape: Optional[Shape] = None
    table: Optional[Table] = None
    image: Optional[Image] = None
    video: Optional[Video] = None
    line: Optional[Line] = None
    wordArt: Optional[WordArt] = None
    sheetsChart: Optional[SheetsChart] = None
    speakerSpotlight: Optional[SpeakerSpotlight] = None
    elementGroup: Optional[Group] = None

    def create_copy(self, parent_id: str, presentation_id: str):
        request = self.create_request(parent_id)
        out = slides_batch_update(request, presentation_id)
        try:
            request_type = list(out["replies"][0].keys())[0]
            new_element_id = out["replies"][0][request_type]["objectId"]
            return new_element_id
        except:
            return None

    def create_request(self, parent_id: str) -> List[Dict[str, Any]]:
        """Convert a PageElement to a create request for the Google Slides API."""

        # Common element properties
        element_properties = {
            "pageObjectId": parent_id,
            "size": self.size.to_api_format(),
            "transform": self.transform.to_api_format(),
        }

        # Add title and description if provided
        if self.title is not None:
            element_properties["title"] = self.title
        if self.description is not None:
            element_properties["description"] = self.description

        if self.shape is not None:
            return [
                {
                    "createShape": {
                        "elementProperties": element_properties,
                        "shapeType": self.shape.shapeType.value,
                    }
                }
            ]
        elif self.image is not None:
            return [
                {
                    "createImage": {
                        "elementProperties": element_properties,
                        "url": self.image.contentUrl,
                    }
                }
            ]
        elif self.table is not None:
            return [
                {
                    "createTable": {
                        "elementProperties": element_properties,
                        "rows": self.table.rows,
                        "columns": self.table.columns,
                    }
                }
            ]
        elif self.video is not None:
            if self.video.source is None:
                raise ValueError("Video source type is required")

            return [
                {
                    "createVideo": {
                        "elementProperties": element_properties,
                        "source": self.video.source.value,
                        "id": self.video.id,
                    }
                }
            ]
        elif self.line is not None:
            return [
                {
                    "createLine": {
                        "elementProperties": element_properties,
                        "lineCategory": self.line.lineType if self.line.lineType else "STRAIGHT",
                    }
                }
            ]
        elif self.sheetsChart is not None:
            if not self.sheetsChart.spreadsheetId or not self.sheetsChart.chartId:
                raise ValueError("Spreadsheet ID and Chart ID are required for Sheets Chart")

            return [
                {
                    "createSheetsChart": {
                        "elementProperties": element_properties,
                        "spreadsheetId": self.sheetsChart.spreadsheetId,
                        "chartId": self.sheetsChart.chartId,
                    }
                }
            ]
        elif self.wordArt is not None:
            if not self.wordArt.renderedText:
                raise ValueError("Rendered text is required for Word Art")

            return [
                {
                    "createWordArt": {
                        "elementProperties": element_properties,
                        "renderedText": self.wordArt.renderedText,
                    }
                }
            ]
        else:
            raise ValueError(f"Unsupported element type {self}, {self.__dict__}")

    def update(self, presentation_id: str, element_id: Optional[str] = None) -> Dict[str, Any]:
        if element_id is None:
            element_id = self.objectId
        requests = self.element_to_update_request(element_id)
        if len(requests):
            out = slides_batch_update(requests, presentation_id)
            return out
        else:
            return {}

    def element_to_update_request(self, element_id: str) -> List[Dict[str, Any]]:
        """Convert a PageElement to an update request for the Google Slides API.
        :param element_id: The id of the element to update, if not the same as e objectId
        :type element_id: str, optional
        :return: The update request
        :rtype: list

        """

        # Update title and description if provided
        requests = []
        if self.title is not None or self.description is not None:
            update_fields = []
            properties = {}

            if self.title is not None:
                properties["title"] = self.title
                update_fields.append("title")

            if self.description is not None:
                properties["description"] = self.description
                update_fields.append("description")

            if update_fields:
                requests.append(
                    {
                        "updatePageElementProperties": {
                            "objectId": element_id,
                            "pageElementProperties": properties,
                            "fields": ",".join(update_fields),
                        }
                    }
                )

        if self.shape is not None:
            # shape_properties = self.shape.shapeProperties.to_api_format()
            ## TODO: fix the below, now causes error
            # b'{\n  "error": {\n    "code": 400,\n    "message": "Invalid requests[0].updateShapeProperties: Updating shapeBackgroundFill propertyState to INHERIT is not supported for shape with no placeholder parent shape",\n    "status": "INVALID_ARGUMENT"\n  }\n}\n'
            # out = [
            #     {
            #         "updateShapeProperties": {
            #             "objectId": element_id,
            #             "shapeProperties": shape_properties,
            #             "fields": "*",
            #         }
            #     }
            # ]
            shape_requests = []
            if self.shape.text is None:
                return requests
            for te in self.shape.text.textElements:
                if te.textRun is None:
                    # TODO: What is the role of empty ParagraphMarkers?
                    continue

                style = te.textRun.style.to_api_format()
                shape_requests += [
                    {
                        "insertText": {
                            "objectId": element_id,
                            "text": te.textRun.content,
                            "insertionIndex": te.startIndex,
                        }
                    },
                    {
                        "updateTextStyle": {
                            "objectId": element_id,
                            "textRange": {
                                "startIndex": te.startIndex or 0,
                                "endIndex": te.endIndex,
                                "type": "FIXED_RANGE",
                            },
                            "style": style,
                            "fields": "*",
                        }
                    },
                ]

            return requests + shape_requests
        elif self.image is not None:
            if hasattr(self.image, "imageProperties") and self.image.imageProperties is not None:
                image_properties = self.image.imageProperties.to_api_format()
                # "fields": "*" causes an error
                image_requests = [
                    {
                        "updateImageProperties": {
                            "objectId": element_id,
                            "imageProperties": image_properties,
                            "fields": ",".join(dict_to_dot_separated_field_list(image_properties)),
                        }
                    }
                ]
                return requests + image_requests
        elif self.video is not None:
            if hasattr(self.video, "videoProperties") and self.video.videoProperties is not None:
                video_properties = self.video.videoProperties.to_api_format()
                video_requests = [
                    {
                        "updateVideoProperties": {
                            "objectId": element_id,
                            "videoProperties": video_properties,
                            "fields": ",".join(dict_to_dot_separated_field_list(video_properties)),
                        }
                    }
                ]
                return requests + video_requests
        elif self.line is not None:
            if hasattr(self.line, "lineProperties") and self.line.lineProperties is not None:
                line_properties = self.line.lineProperties.to_api_format()
                line_requests = [
                    {
                        "updateLineProperties": {
                            "objectId": element_id,
                            "lineProperties": line_properties,
                            "fields": ",".join(dict_to_dot_separated_field_list(line_properties)),
                        }
                    }
                ]
                return requests + line_requests
        elif self.sheetsChart is not None:
            if (
                hasattr(self.sheetsChart, "sheetsChartProperties")
                and self.sheetsChart.sheetsChartProperties is not None
            ):
                chart_properties = self.sheetsChart.sheetsChartProperties.to_api_format()
                chart_requests = [
                    {
                        "updateSheetsChartProperties": {
                            "objectId": element_id,
                            "sheetsChartProperties": chart_properties,
                            "fields": ",".join(dict_to_dot_separated_field_list(chart_properties)),
                        }
                    }
                ]
                return requests + chart_requests

        return requests
