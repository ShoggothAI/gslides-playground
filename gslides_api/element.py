from typing import Optional, Dict, Any, List

from gslides_api.domain import GSlidesBaseModel, Transform, Shape, Table, Image, Size, Video
from gslides_api.execute import slides_batch_update


class PageElement(GSlidesBaseModel):
    """Represents an element on a slide."""

    objectId: str
    size: Size
    transform: Transform
    shape: Optional[Shape] = None
    table: Optional[Table] = None
    image: Optional[Image] = None
    video: Optional[Video] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to the format expected by the Google Slides API."""
        # Start with a copy of any extra fields
        result = {
            k: v
            for k, v in self.__dict__.items()
            if k not in ["objectId", "size", "transform", "shape", "table", "image", "video"]
        }

        # Add the standard fields
        result["objectId"] = self.objectId
        result["size"] = self.size.to_api_format()
        result["transform"] = self.transform.to_api_format()

        if self.shape is not None:
            result["shape"] = self.shape.to_api_format()

        if self.table is not None:
            result["table"] = self.table.to_api_format()

        if self.image is not None:
            result["image"] = self.image.to_api_format()

        if self.video is not None:
            result["video"] = self.video.to_api_format()

        return result

    def create(self, parent_id: str, presentation_id: str):
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

        if self.shape is not None:
            return [
                {
                    "createShape": {
                        "elementProperties": {
                            "pageObjectId": parent_id,
                            "size": self.size.to_api_format(),
                            "transform": self.transform.to_api_format(),
                        },
                        "shapeType": self.shape.shapeType.value,
                    }
                }
            ]
        elif self.image is not None:
            return [
                {
                    "createImage": {
                        "elementProperties": {
                            "pageObjectId": parent_id,
                            "size": self.size.to_api_format(),
                            "transform": self.transform.to_api_format(),
                        },
                        "url": self.image.sourceUrl,
                    }
                }
            ]
        elif self.table is not None:
            return [
                {
                    "createTable": {
                        "elementProperties": {
                            "pageObjectId": parent_id,
                            "size": self.size.to_api_format(),
                            "transform": self.transform.to_api_format(),
                        },
                        "rows": self.table.rows,
                        "columns": self.table.columns,
                    }
                }
            ]
        elif self.video is not None:
            return [
                {
                    "createVideo": {
                        "elementProperties": {
                            "pageObjectId": parent_id,
                            "size": self.size.to_api_format(),
                            "transform": self.transform.to_api_format(),
                        },
                        "source": self.video.source.type,
                        "columns": self.video.source.id,
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
            out = []
            if self.shape.text is None:
                return out
            for te in self.shape.text.textElements:
                if te.textRun is None:
                    # TODO: What is the role of empty ParagraphMarkers?
                    continue

                style = te.textRun.style.to_api_format()
                out += [
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

            return out
        elif self.image is not None:
            image_properties = self.image.imageProperties.to_api_format()
            # propertyState is a readonly property, API will barf if we try to set it
            image_properties["outline"].pop("propertyState")
            image_properties["shadow"].pop("propertyState")
            requests = [
                {
                    "updateImageProperties": {
                        "objectId": element_id,
                        "imageProperties": image_properties,
                        "fields": ",".join(dict_to_dot_separated_field_list(image_properties)),
                    }
                }
            ]
            return requests
        else:
            return []
            # raise NotImplementedError


def dict_to_dot_separated_field_list(x: Dict[str, Any]) -> List[str]:
    """Convert a dictionary to a list of dot-separated fields."""
    out = []
    for k, v in x.items():
        if isinstance(v, dict):
            out += [f"{k}.{i}" for i in dict_to_dot_separated_field_list(v)]
        else:
            out.append(k)
    return out
