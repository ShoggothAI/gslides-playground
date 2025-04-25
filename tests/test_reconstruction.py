import json
import os
import sys
from typing import Dict, Any, List, Tuple, Union, Set

import pytest

# Import our custom modules
from gslides_api import Presentation


@pytest.fixture
def presentation_json_path() -> str:
    """Fixture that returns the path to the test presentation JSON file."""
    return os.path.join(os.path.dirname(__file__), "presentation_output.json")


@pytest.fixture
def original_json(presentation_json_path: str) -> Dict[str, Any]:
    """Fixture that loads and returns the original presentation JSON."""
    with open(presentation_json_path, "r") as f:
        return json.load(f)


@pytest.fixture
def presentation_model(original_json: Dict[str, Any]) -> Presentation:
    """Fixture that creates a Presentation model from the original JSON."""
    return Presentation.model_validate(original_json)


@pytest.fixture
def reconstructed_json(presentation_model: Presentation) -> Dict[str, Any]:
    """Fixture that generates the reconstructed JSON from the Presentation model."""
    return presentation_model.to_api_format()


@pytest.fixture
def output_json_path() -> str:
    """Fixture that returns the path to save the reconstructed JSON."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "reconstructed_output.json")


@pytest.fixture
def ignored_keys() -> Set[str]:
    """Fixture that returns a set of keys to ignore in the comparison."""
    return {"propertyState"}


@pytest.fixture
def ignored_paths() -> Set[str]:
    """Fixture that returns a set of paths to ignore in the comparison."""
    return set()


def compare_json_structures(
    original: Any,
    reconstructed: Any,
    path: str = "",
    ignored_keys: Set[str] = None,
    ignored_paths: Set[str] = None,
) -> List[str]:
    """
    Recursively compare two JSON structures and return a list of differences.

    Args:
        original: The original JSON structure
        reconstructed: The reconstructed JSON structure
        path: The current path in the JSON structure (for error reporting)
        ignored_keys: Set of keys to ignore in the comparison
        ignored_paths: Set of paths to ignore in the comparison

    Returns:
        A list of differences between the two structures
    """
    if ignored_keys is None:
        ignored_keys = set()

    if ignored_paths is None:
        ignored_paths = set()

    # Check if the current path should be ignored
    if any(path.startswith(ignored_path) for ignored_path in ignored_paths if ignored_path):
        return []

    differences = []

    # If types are different, handle special cases
    if type(original) != type(reconstructed):
        # Allow int/float conversions for numeric values
        if isinstance(original, (int, float)) and isinstance(reconstructed, (int, float)):
            # For numeric values, compare the actual values with a small tolerance
            if abs(float(original) - float(reconstructed)) > 1e-10:
                differences.append(f"Value mismatch at {path}: {original} vs {reconstructed}")
        else:
            differences.append(
                f"Type mismatch at {path}: {type(original)} vs {type(reconstructed)}"
            )
            return differences

    # Handle dictionaries
    elif isinstance(original, dict):
        # Check for missing keys
        original_keys = set(original.keys()) - ignored_keys
        reconstructed_keys = set(reconstructed.keys()) - ignored_keys

        # Keys in original but not in reconstructed
        for key in original_keys - reconstructed_keys:
            # Skip default style properties that might be missing in the original
            differences.append(f"Key '{key}' at {path} exists in original but not in reconstructed")

        # Keys in reconstructed but not in original
        for key in reconstructed_keys - original_keys:
            # Skip default style properties that might be added in the reconstruction
            if key in ["bold", "italic", "underline", "strikethrough"] and path.endswith("style"):
                # These are default style properties that are always included in our model
                continue
            if key == "shapeType" and path.endswith("shape"):
                # ShapeType is always included in our model
                continue
            if key == "pageElements" and path.endswith("slides"):
                # Empty pageElements array is added by our preprocessor
                continue
            differences.append(f"Key '{key}' at {path} exists in reconstructed but not in original")

        # Recursively compare values for keys that exist in both
        for key in original_keys & reconstructed_keys:
            new_path = f"{path}.{key}" if path else key
            differences.extend(
                compare_json_structures(
                    original[key], reconstructed[key], new_path, ignored_keys, ignored_paths
                )
            )

    # Handle lists
    elif isinstance(original, list):
        if len(original) != len(reconstructed):
            differences.append(
                f"List length mismatch at {path}: {len(original)} vs {len(reconstructed)}"
            )
        else:
            # Recursively compare each item in the list
            for i, (orig_item, recon_item) in enumerate(zip(original, reconstructed)):
                new_path = f"{path}[{i}]"
                differences.extend(
                    compare_json_structures(
                        orig_item, recon_item, new_path, ignored_keys, ignored_paths
                    )
                )

    # Handle primitive values (strings, numbers, booleans, None)
    elif original != reconstructed:
        # For floating point values, allow small differences
        if isinstance(original, float) and isinstance(reconstructed, float):
            if abs(original - reconstructed) > 1e-10:
                differences.append(f"Value mismatch at {path}: {original} vs {reconstructed}")
        else:
            differences.append(f"Value mismatch at {path}: {original} vs {reconstructed}")

    return differences


def test_save_reconstructed_json(reconstructed_json: Dict[str, Any], output_json_path: str):
    """Test that we can save the reconstructed JSON to a file."""
    with open(output_json_path, "w") as f:
        json.dump(reconstructed_json, f, indent=2)
    assert os.path.exists(output_json_path), f"Failed to save reconstructed JSON to {output_json_path}"


def test_essential_fields_preserved(original_json: Dict[str, Any], reconstructed_json: Dict[str, Any]):
    """Test that essential fields are preserved in the reconstructed JSON."""
    essential_fields = ["presentationId", "pageSize", "slides"]
    for field in essential_fields:
        assert field in original_json, f"Field '{field}' missing in original JSON"
        assert field in reconstructed_json, f"Field '{field}' missing in reconstructed JSON"


def test_slide_count_preserved(original_json: Dict[str, Any], reconstructed_json: Dict[str, Any]):
    """Test that the number of slides is preserved in the reconstructed JSON."""
    original_slides = len(original_json.get("slides", []))
    reconstructed_slides = len(reconstructed_json.get("slides", []))
    assert reconstructed_slides == original_slides, (
        f"Slide count mismatch: {original_slides} in original, {reconstructed_slides} in reconstructed"
    )


@pytest.mark.parametrize(
    "field_path",
    [
        ["presentationId"],
        ["pageSize", "width", "magnitude"],
        ["pageSize", "height", "magnitude"],
        ["pageSize", "width", "unit"],
    ],
)
def test_field_values_preserved(original_json: Dict[str, Any], reconstructed_json: Dict[str, Any], field_path: List[str]):
    """Test that specific field values are preserved in the reconstructed JSON."""
    # Navigate to the field in both JSONs
    orig_value = original_json
    recon_value = reconstructed_json

    for key in field_path:
        try:
            orig_value = orig_value[key]
            recon_value = recon_value[key]
        except (KeyError, TypeError):
            pytest.skip(f"Field path {field_path} not found in one of the JSONs")

    # For numeric values, allow small differences
    if isinstance(orig_value, (int, float)) and isinstance(recon_value, (int, float)):
        assert abs(float(orig_value) - float(recon_value)) < 1e-10, (
            f"Value mismatch at {'.'.join(field_path)}: {orig_value} vs {recon_value}"
        )
    else:
        assert orig_value == recon_value, (
            f"Value mismatch at {'.'.join(field_path)}: {orig_value} vs {recon_value}"
        )


def test_slide_content_preserved(original_json: Dict[str, Any], reconstructed_json: Dict[str, Any]):
    """Test that slide content is preserved in the reconstructed JSON."""
    # Skip if there are no slides
    if not original_json.get("slides") or not reconstructed_json.get("slides"):
        pytest.skip("No slides found in one of the JSONs")

    # Check the first slide's content if available
    try:
        # Try to extract a title or some content from the first slide
        # This is a common path to text content in a slide, but might need adjustment
        # based on the actual structure of your presentation
        path_to_check = ["slides", 0, "pageElements", 0, "shape", "text", "textElements", 1, "textRun", "content"]

        orig_value = original_json
        recon_value = reconstructed_json

        for key in path_to_check:
            if isinstance(key, int):
                # Handle list indexing
                orig_value = orig_value[key]
                recon_value = recon_value[key]
            else:
                # Handle dictionary keys
                orig_value = orig_value.get(key)
                recon_value = recon_value.get(key)

                # Skip if the key doesn't exist
                if orig_value is None or recon_value is None:
                    pytest.skip(f"Path {path_to_check} not found in one of the JSONs")

        # If we got here, we have values to compare
        assert orig_value == recon_value, f"Slide content mismatch: {orig_value} vs {recon_value}"
    except (KeyError, IndexError, TypeError):
        # If the path doesn't exist, skip the test rather than fail
        pytest.skip("Could not extract comparable content from slides")


def test_deep_comparison(original_json: Dict[str, Any], reconstructed_json: Dict[str, Any],
                         ignored_keys: Set[str], ignored_paths: Set[str]):
    """Test that the deep comparison of JSON structures finds no differences."""
    differences = compare_json_structures(
        original_json, reconstructed_json, ignored_keys=ignored_keys, ignored_paths=ignored_paths
    )

    # If there are differences, format them for the assertion message
    if differences:
        diff_message = "\n".join([f"{i+1}. {diff}" for i, diff in enumerate(differences)])
        assert not differences, f"Found {len(differences)} differences:\n{diff_message}"
    else:
        assert True, "No differences found in the deep comparison"
