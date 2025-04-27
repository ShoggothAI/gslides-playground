import pytest
from gslides_api.slide import Slide, SlideProperties
from gslides_api.domain import PageProperties

def test_presentation_id_not_in_api_format():
    """Test that presentation_id is not included in the API format."""
    # Create a minimal slide
    slide = Slide(
        objectId="test-slide-id",
        slideProperties=SlideProperties(
            layoutObjectId="test-layout-id",
            masterObjectId="test-master-id"
        ),
        pageProperties=PageProperties(
            pageBackgroundFill={}
        ),
        presentation_id="test-presentation-id"
    )

    # Convert to API format
    api_format = slide.to_api_format()

    # Check that presentation_id is not in the API format
    assert "presentation_id" not in api_format

    # Check that other fields are in the API format
    assert api_format["objectId"] == "test-slide-id"
    assert "slideProperties" in api_format
    assert "pageProperties" in api_format

def test_write_sets_presentation_id(monkeypatch):
    """Test that the write method sets the presentation_id."""
    # Create a minimal slide
    slide = Slide(
        objectId="test-slide-id",
        slideProperties=SlideProperties(
            layoutObjectId="test-layout-id",
            masterObjectId="test-master-id"
        ),
        pageProperties=PageProperties(
            pageBackgroundFill={}
        )
    )

    # Mock the create_blank method to avoid API calls
    def mock_create_blank(self, presentation_id, insertion_index=None):
        return "new-slide-id"

    # Mock the slides_batch_update function
    def mock_slides_batch_update(requests, presentation_id):
        return {"replies": [{"createSlide": {"objectId": "new-slide-id"}}]}

    # Apply the monkeypatches
    import gslides_api.slide
    monkeypatch.setattr(Slide, "create_blank", mock_create_blank)
    monkeypatch.setattr(gslides_api.slide, "slides_batch_update", mock_slides_batch_update)

    # Call write with a presentation_id
    result = slide.write(presentation_id="test-presentation-id")

    # Check that presentation_id is set on the original slide
    assert slide.presentation_id == "test-presentation-id"

    # Check that presentation_id is set on the returned slide
    assert result.presentation_id == "test-presentation-id"

def test_duplicate_preserves_presentation_id(monkeypatch):
    """Test that the duplicate method preserves the presentation_id."""
    # Create a minimal slide
    slide = Slide(
        objectId="test-slide-id",
        slideProperties=SlideProperties(
            layoutObjectId="test-layout-id",
            masterObjectId="test-master-id"
        ),
        pageProperties=PageProperties(
            pageBackgroundFill={}
        ),
        presentation_id="test-presentation-id"
    )

    # Mock the duplicate function to avoid API calls
    def mock_duplicate(objectId, presentation_id):
        return "new-slide-id"

    # Apply the monkeypatch
    import gslides_api.slide
    monkeypatch.setattr(gslides_api.slide, "duplicate", mock_duplicate)

    # Call duplicate with a different presentation_id
    result = slide.duplicate(presentation_id="new-presentation-id")

    # Check that presentation_id is updated on the returned slide
    assert result.presentation_id == "new-presentation-id"
