"""Test AI dependencies are properly installed and importable."""
import pytest


def test_google_genai_import():
    """Test that google.genai can be imported successfully."""
    try:
        import google.genai
    except ImportError as e:
        pytest.fail(f"Failed to import google.genai: {e}")
