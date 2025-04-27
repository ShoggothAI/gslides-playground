from typing import Dict, Any, List, Optional

from gslides_api.domain import ShapeType
from gslides_api.element import PageElement


def element_to_create_request(e: PageElement, parent_id: str) -> List[Dict[str, Any]]:
    """Convert a PageElement to a create request for the Google Slides API."""

    if e.shape is not None:
        return [
            {
                "createShape": {
                    "elementProperties": {
                        "pageObjectId": parent_id,
                        "size": e.size.to_api_format(),
                        "transform": e.transform.to_api_format(),
                    },
                    "shapeType": e.shape.shapeType.value,
                }
            }
        ]
    elif e.image is not None:
        return [
            {
                "createImage": {
                    "elementProperties": {
                        "pageObjectId": parent_id,
                        "size": e.size.to_api_format(),
                        "transform": e.transform.to_api_format(),
                    },
                    "url": e.image.sourceUrl,
                }
            }
        ]
    elif e.table is not None:
        return [
            {
                "createTable": {
                    "elementProperties": {
                        "pageObjectId": parent_id,
                        "size": e.size.to_api_format(),
                        "transform": e.transform.to_api_format(),
                    },
                    "rows": e.table.rows,
                    "columns": e.table.columns,
                }
            }
        ]
    elif e.video is not None:
        return [
            {
                "createVideo": {
                    "elementProperties": {
                        "pageObjectId": parent_id,
                        "size": e.size.to_api_format(),
                        "transform": e.transform.to_api_format(),
                    },
                    "source": e.video.source.type,
                    "columns": e.video.source.id,
                }
            }
        ]
    else:
        raise ValueError(f"Unsupported element type {e}")


def element_to_update_request(
    e: PageElement, element_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Convert a PageElement to an update request for the Google Slides API.

    :param e: The PageElement to convert
    :type e: :class:`PageElement`
    :param element_id: The id of the element to update, if not the same as e objectId
    :type element_id: str, optional
    :return: The update request
    :rtype: list

    """

    if element_id is None:
        element_id = e.objectId

    if e.shape is not None:
        shape_properties = e.shape.shapeProperties.to_api_format()
        out = []
        # out = [
        #     {
        #         "updateShapeProperties": {
        #             "objectId": element_id,
        #             "shapeProperties": shape_properties,
        #             "fields": ",".join(get_dot_separated_fields(shape_properties)),
        #         }
        #     }
        # ]
        if e.shape.text is None:
            return out
        for te in e.shape.text.textElements:
            if te.textRun is None:
                # TODO: What is the role of empty ParagraphMarkers?
                continue

            style = te.textRun.style.to_api_format()
            out.append(
                [
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
                                "startIndex": te.startIndex,
                                "endIndex": te.endIndex,
                                "type": "FIXED_RANGE",
                            },
                            "style": style,
                            "fields": "*",
                        }
                    },
                ]
            )
        return out
    else:
        raise NotImplementedError


def get_dot_separated_fields(x: dict) -> List[str]:
    keys = x.keys()
    out = []
    for k in keys:
        if isinstance(x[k], dict):
            out += [f"{k}.{subkey}" for subkey in get_dot_separated_fields(x[k])]

        else:
            out.append(k)
    return out
