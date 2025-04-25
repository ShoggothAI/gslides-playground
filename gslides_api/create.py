from typing import Dict, Any, List

from gslides_api.domain import PageElement, ShapeType


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
