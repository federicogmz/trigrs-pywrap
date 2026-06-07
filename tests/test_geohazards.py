"""Comprehensive tests for the geohazards and TRIGRS classes."""


# ============================================================
# Import and Structure Tests
# ============================================================


class TestImports:
    """Test module import and class accessibility."""

    def test_geohazards_imports(self):
        from geohazards import geohazards

        assert callable(geohazards)

    def test_trigrs_imports(self):
        from geohazards import TRIGRS

        assert callable(TRIGRS)

    def test_trigrs_inherits_geohazards(self):
        from geohazards import TRIGRS, geohazards

        assert issubclass(TRIGRS, geohazards)

    def test_geohazards_has_expected_public_methods(self):
        from geohazards import geohazards

        expected = ["Slope", "flowdir", "Catani", "exportASCII", "preprocess_dem"]
        for method in expected:
            assert hasattr(geohazards, method), f"Missing method: {method}"

    def test_trigrs_has_expected_public_methods(self):
        from geohazards import TRIGRS

        expected = [
            "Insumos",
            "GridMatch",
            "TopoIndex",
            "tr_in_creation",
            "TRIGRS_main",
        ]
        for method in expected:
            assert hasattr(TRIGRS, method), f"Missing method: {method}"


# ============================================================
# Class Hierarchy Tests
# ============================================================


class TestClassHierarchy:
    """Test that class hierarchy is correct."""

    def test_geohazards_is_base_class(self):
        from geohazards import geohazards

        assert geohazards.__bases__ == (object,)

    def test_trigrs_extends_geohazards(self):
        from geohazards import TRIGRS, geohazards

        assert geohazards in TRIGRS.__mro__

    def test_trigrs_has_call_method(self):
        """TRIGRS should be callable (uses __call__)."""
        from geohazards import TRIGRS

        assert callable(getattr(TRIGRS, "__call__", None))


# ============================================================
# Method Signature Tests
# ============================================================


class TestMethodSignatures:
    """Test that methods have expected signatures."""

    def test_geohazards_init_signature(self):
        import inspect

        from geohazards import geohazards

        sig = inspect.signature(geohazards.__init__)
        params = list(sig.parameters.keys())
        assert "dem_path" in params
        assert "geo" in params

    def test_trigrs_init_signature(self):
        import inspect

        from geohazards import TRIGRS

        sig = inspect.signature(TRIGRS.__init__)
        params = list(sig.parameters.keys())
        assert "dem_path" in params
        assert "geo" in params

    def test_slope_method_signature(self):
        import inspect

        from geohazards import geohazards

        sig = inspect.signature(geohazards.Slope)
        params = list(sig.parameters.keys())
        assert "unit" in params

    def test_catani_method_signature(self):
        import inspect

        from geohazards import geohazards

        sig = inspect.signature(geohazards.Catani)
        params = list(sig.parameters.keys())
        assert "hmin" in params
        assert "hmax" in params


# ============================================================
# Module Docstring Tests
# ============================================================


class TestModuleStructure:
    """Test that module structure is correct and discoverable."""

    def test_geohazards_module_has_code(self):
        """geohazards module should contain the geohazards class."""
        from geohazards import geohazards

        # Verify it's a proper class with expected attributes
        assert hasattr(geohazards, "__init__")
        assert hasattr(geohazards, "Slope")
        assert hasattr(geohazards, "flowdir")
