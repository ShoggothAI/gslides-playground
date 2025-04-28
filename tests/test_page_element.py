import pytest
from gslides_api.element import PageElement
from gslides_api.domain import (
    Size, Transform, Shape, ShapeProperties, ShapeType, 
    Line, LineProperties, WordArt, SheetsChart, SheetsChartProperties,
    SpeakerSpotlight, SpeakerSpotlightProperties, Group, Video, VideoProperties,
    Image, ImageProperties, Table
)

def test_page_element_fields():
    """Test that PageElement has all the required fields."""
    element = PageElement(
        objectId="test_id",
        size=Size(width=100, height=100),
        transform=Transform(translateX=0, translateY=0, scaleX=1, scaleY=1),
        title="Test Title",
        description="Test Description"
    )
    
    assert element.objectId == "test_id"
    assert element.size.width == 100
    assert element.size.height == 100
    assert element.transform.translateX == 0
    assert element.transform.translateY == 0
    assert element.transform.scaleX == 1
    assert element.transform.scaleY == 1
    assert element.title == "Test Title"
    assert element.description == "Test Description"
    
    # Check that all element types are initialized to None
    assert element.shape is None
    assert element.table is None
    assert element.image is None
    assert element.video is None
    assert element.line is None
    assert element.wordArt is None
    assert element.sheetsChart is None
    assert element.speakerSpotlight is None
    assert element.elementGroup is None

def test_page_element_with_shape():
    """Test PageElement with a shape."""
    element = PageElement(
        objectId="shape_id",
        size=Size(width=100, height=100),
        transform=Transform(translateX=0, translateY=0, scaleX=1, scaleY=1),
        shape=Shape(
            shapeType=ShapeType.RECTANGLE,
            shapeProperties=ShapeProperties()
        )
    )
    
    assert element.shape is not None
    assert element.shape.shapeType == ShapeType.RECTANGLE
    
    # Create request should generate a valid request
    request = element.create_request("page_id")
    assert len(request) == 1
    assert "createShape" in request[0]
    assert request[0]["createShape"]["shapeType"] == "RECTANGLE"

def test_page_element_with_line():
    """Test PageElement with a line."""
    element = PageElement(
        objectId="line_id",
        size=Size(width=100, height=100),
        transform=Transform(translateX=0, translateY=0, scaleX=1, scaleY=1),
        line=Line(
            lineType="STRAIGHT",
            lineProperties=LineProperties()
        )
    )
    
    assert element.line is not None
    assert element.line.lineType == "STRAIGHT"
    
    # Create request should generate a valid request
    request = element.create_request("page_id")
    assert len(request) == 1
    assert "createLine" in request[0]
    assert request[0]["createLine"]["lineCategory"] == "STRAIGHT"

def test_page_element_with_word_art():
    """Test PageElement with word art."""
    element = PageElement(
        objectId="wordart_id",
        size=Size(width=100, height=100),
        transform=Transform(translateX=0, translateY=0, scaleX=1, scaleY=1),
        wordArt=WordArt(
            renderedText="Test Word Art"
        )
    )
    
    assert element.wordArt is not None
    assert element.wordArt.renderedText == "Test Word Art"
    
    # Create request should generate a valid request
    request = element.create_request("page_id")
    assert len(request) == 1
    assert "createWordArt" in request[0]
    assert request[0]["createWordArt"]["renderedText"] == "Test Word Art"

def test_page_element_with_sheets_chart():
    """Test PageElement with a sheets chart."""
    element = PageElement(
        objectId="chart_id",
        size=Size(width=100, height=100),
        transform=Transform(translateX=0, translateY=0, scaleX=1, scaleY=1),
        sheetsChart=SheetsChart(
            spreadsheetId="spreadsheet_id",
            chartId=123,
            sheetsChartProperties=SheetsChartProperties()
        )
    )
    
    assert element.sheetsChart is not None
    assert element.sheetsChart.spreadsheetId == "spreadsheet_id"
    assert element.sheetsChart.chartId == 123
    
    # Create request should generate a valid request
    request = element.create_request("page_id")
    assert len(request) == 1
    assert "createSheetsChart" in request[0]
    assert request[0]["createSheetsChart"]["spreadsheetId"] == "spreadsheet_id"
    assert request[0]["createSheetsChart"]["chartId"] == 123

def test_update_request_with_title_description():
    """Test that update request includes title and description."""
    element = PageElement(
        objectId="element_id",
        size=Size(width=100, height=100),
        transform=Transform(translateX=0, translateY=0, scaleX=1, scaleY=1),
        title="Updated Title",
        description="Updated Description"
    )
    
    request = element.element_to_update_request("element_id")
    assert len(request) == 1
    assert "updatePageElementProperties" in request[0]
    assert request[0]["updatePageElementProperties"]["pageElementProperties"]["title"] == "Updated Title"
    assert request[0]["updatePageElementProperties"]["pageElementProperties"]["description"] == "Updated Description"
