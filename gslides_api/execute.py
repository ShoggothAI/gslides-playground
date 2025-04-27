from typing import Dict, Any

from gslides import creds


def slides_batch_update(requests: list, presentation_id: str) -> Dict[str, Any]:
    return (
        creds.slide_service.presentations()
        .batchUpdate(presentationId=presentation_id, body={"requests": requests})
        .execute()
    )
