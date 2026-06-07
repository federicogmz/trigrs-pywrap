"""Basic smoke tests for trigrs-pywrap package."""
import pytest


def test_geohazards_imports():
    """Test that geohazards module can be imported."""
    from geohazards import geohazards
    assert callable(geohazards)


def test_trigrs_class_exists():
    """Test that TRIGRS class is accessible."""
    from geohazards import TRIGRS
    assert callable(TRIGRS)


def test_trigrs_inherits_geohazards():
    """Test that TRIGRS inherits from geohazards."""
    from geohazards import TRIGRS, geohazards
    assert issubclass(TRIGRS, geohazards)


def test_geohazards_has_expected_methods():
    """Test that geohazards base class has expected methods."""
    from geohazards import geohazards
    expected_methods = ["Slope", "flowdir", "Catani", "exportASCII", "preprocess_dem"]
    for method in expected_methods:
        assert hasattr(geohazards, method), f"Missing method: {method}"
