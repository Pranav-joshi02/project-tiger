"""Unit tests for Spotted Deer and Sloth Bear detection.

Tests that the enhanced species classifier correctly identifies:
1. Spotted Deer / Chital (Axis axis) — brown body, white spots, no stripes
2. Sloth Bear (Melursus ursinus) — black fur, white V-chest, nocturnal IR images
3. No regression: tigers still correctly identified
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
import numpy as np
from PIL import Image as PILImage, ImageDraw


# ---- Synthetic Image Generators ----

def _create_spotted_deer_image(width=600, height=400):
    """Synthetic spotted deer: fawn/brown body with scattered white spots."""
    bg_color = (80, 130, 60)  # green foliage background
    img = PILImage.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fawn/tawny-brown deer body (center of frame)
    body_color = (185, 145, 90)  # warm brown, NOT tiger orange
    draw.ellipse([(120, 100), (500, 340)], fill=body_color)

    # Legs
    draw.rectangle([(170, 300), (200, 390)], fill=(175, 135, 80))
    draw.rectangle([(250, 310), (275, 390)], fill=(175, 135, 80))
    draw.rectangle([(380, 310), (405, 390)], fill=(175, 135, 80))
    draw.rectangle([(440, 300), (465, 390)], fill=(175, 135, 80))

    # Head and neck
    draw.ellipse([(80, 70), (160, 160)], fill=(180, 140, 85))

    # White spots scattered across the body (THE defining chital feature)
    import random
    random.seed(42)
    for _ in range(55):
        cx = random.randint(140, 480)
        cy = random.randint(120, 310)
        r = random.randint(3, 7)
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(245, 245, 240))

    # Light belly
    draw.ellipse([(180, 240), (450, 330)], fill=(210, 195, 165))

    return img


def _create_sloth_bear_image(width=600, height=400):
    """Synthetic sloth bear: predominantly black with white V-chest marking."""
    bg_color = (60, 75, 45)  # dark forest background
    img = PILImage.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Large dark/black body
    body_color = (35, 30, 28)  # very dark / black fur
    draw.ellipse([(100, 80), (500, 360)], fill=body_color)

    # Head
    draw.ellipse([(60, 50), (180, 170)], fill=(40, 35, 32))

    # Light muzzle
    draw.ellipse([(50, 110), (120, 155)], fill=(140, 130, 115))

    # White V-shaped chest marking (THE defining sloth bear feature)
    draw.polygon(
        [(280, 120), (320, 120), (330, 220), (300, 260), (270, 220)],
        fill=(230, 225, 210)
    )

    # Shaggy fur texture — add noise-like dark variations
    import random
    random.seed(42)
    for _ in range(200):
        x = random.randint(120, 480)
        y = random.randint(100, 340)
        shade = random.randint(20, 55)
        draw.point((x, y), fill=(shade, shade - 5, shade - 8))

    return img


def _create_sloth_bear_ir_image(width=600, height=400):
    """Synthetic night-time IR camera trap image of a sloth bear.
    Grayscale with a dark mass (bear) against lighter background."""
    bg_color = (110, 110, 110)  # IR medium gray background
    img = PILImage.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Dark bear mass
    draw.ellipse([(100, 80), (500, 360)], fill=(40, 40, 40))
    draw.ellipse([(60, 50), (180, 170)], fill=(45, 45, 45))

    # Bright eyes (IR reflection)
    draw.ellipse([(95, 90), (110, 105)], fill=(200, 200, 200))
    draw.ellipse([(135, 90), (150, 105)], fill=(200, 200, 200))

    # Light chest marking (still visible in IR)
    draw.polygon(
        [(280, 120), (320, 120), (325, 200), (300, 230), (275, 200)],
        fill=(130, 130, 130)
    )

    return img


def _create_tiger_image(width=600, height=400):
    """Synthetic tiger: warm orange body with dark vertical stripes."""
    img = PILImage.new("RGB", (width, height), color=(217, 119, 6))
    draw = ImageDraw.Draw(img)
    for x in range(80, width - 60, 60):
        draw.polygon(
            [(x, 40), (x + 20, 200), (x - 10, 360), (x + 10, 360), (x + 35, 200), (x + 15, 40)],
            fill=(24, 24, 27)
        )
    return img


# ---- Fixtures ----

@pytest.fixture
def species_clf():
    """Get a fresh species classifier instance (no YOLO model loaded)."""
    from app.services.species_classifier import SpeciesClassifier
    clf = SpeciesClassifier()
    clf._initialized = True  # Skip YOLO model loading
    clf._yolo_model = None
    clf._pench_model = None
    return clf


# ---- Spotted Deer Tests ----

class TestSpottedDeerDetection:
    """Tests for correct identification of Spotted Deer / Chital."""

    def test_deer_image_classified_as_spotted_deer(self, species_clf, tmp_path):
        """A synthetic spotted deer image should be classified as SPOTTED_DEER."""
        img = _create_spotted_deer_image()
        path = tmp_path / "camera_trap_unknown_001.jpg"
        img.save(path, format="JPEG")

        result = species_clf.classify(path)

        assert result.is_tiger is False, f"Spotted deer falsely classified as tiger! Category={result.category}"
        # The visual analyzer should catch the fawn body + white spots
        # Even without YOLO, the classifier should NOT say TIGER

    def test_deer_by_filename_hint(self, species_clf, tmp_path):
        """A deer image with filename hint should be classified as SPOTTED_DEER."""
        img = _create_spotted_deer_image()
        path = tmp_path / "chital_grazing_zone_b.jpg"
        img.save(path, format="JPEG")

        result = species_clf.classify(path)

        assert result.is_tiger is False
        assert result.category == "SPOTTED_DEER"
        assert "Spotted Deer" in result.species_name or "Chital" in result.species_name
        assert result.confidence >= 0.85

    def test_deer_not_confused_with_tiger(self, species_clf, tmp_path):
        """Spotted deer brown tones should NOT trigger tiger warm-palette detection."""
        img = _create_spotted_deer_image()
        path = tmp_path / "unlabeled_camera_001.jpg"
        img.save(path, format="JPEG")

        result = species_clf.classify(path)
        assert result.category != "TIGER", (
            f"Spotted deer misclassified as TIGER with confidence {result.confidence}!"
        )

    def test_deer_keywords_expanded(self, species_clf, tmp_path):
        """Various deer-related keywords should all trigger deer classification."""
        keywords = ["deer", "chital", "sambar", "hiran", "cheetal", "axis"]
        img = _create_spotted_deer_image()

        for kw in keywords:
            path = tmp_path / f"{kw}_capture.jpg"
            img.save(path, format="JPEG")
            result = species_clf.classify(path)
            assert result.is_tiger is False, f"Keyword '{kw}' failed: classified as tiger"
            assert result.category == "SPOTTED_DEER", f"Keyword '{kw}' failed: got {result.category}"


# ---- Sloth Bear Tests ----

class TestSlothBearDetection:
    """Tests for correct identification of Sloth Bear."""

    def test_bear_image_by_filename(self, species_clf, tmp_path):
        """A sloth bear image with filename hint should be classified as SLOTH_BEAR."""
        img = _create_sloth_bear_image()
        path = tmp_path / "sloth_bear_pench_zone_a.jpg"
        img.save(path, format="JPEG")

        result = species_clf.classify(path)

        assert result.is_tiger is False
        assert result.category == "SLOTH_BEAR"
        assert "Sloth Bear" in result.species_name
        assert result.confidence >= 0.85

    def test_bear_not_classified_as_tiger(self, species_clf, tmp_path):
        """A sloth bear (predominantly dark fur) should NEVER be classified as tiger."""
        img = _create_sloth_bear_image()
        path = tmp_path / "unlabeled_night_capture_005.jpg"
        img.save(path, format="JPEG")

        result = species_clf.classify(path)
        assert result.category != "TIGER", (
            f"Sloth bear misclassified as TIGER with confidence {result.confidence}!"
        )

    def test_ir_nighttime_bear_not_tiger(self, species_clf, tmp_path):
        """A night-time IR camera trap image of a sloth bear should not be classified as tiger."""
        img = _create_sloth_bear_ir_image()
        path = tmp_path / "ir_night_capture_0042.jpg"
        img.save(path, format="JPEG")

        result = species_clf.classify(path)
        assert result.category != "TIGER", (
            f"IR night bear misclassified as TIGER with confidence {result.confidence}!"
        )

    def test_bear_keywords_expanded(self, species_clf, tmp_path):
        """Various bear-related keywords should all trigger bear classification."""
        keywords = ["bear", "sloth", "bhaloo", "bhalu", "melursus", "ursus"]
        img = _create_sloth_bear_image()

        for kw in keywords:
            path = tmp_path / f"{kw}_camera_trap.jpg"
            img.save(path, format="JPEG")
            result = species_clf.classify(path)
            assert result.is_tiger is False, f"Keyword '{kw}' failed: classified as tiger"
            assert result.category == "SLOTH_BEAR", f"Keyword '{kw}' failed: got {result.category}"


# ---- Tiger Regression Tests ----

class TestTigerNoRegression:
    """Ensure tiger detection still works correctly after the deer/bear changes."""

    def test_tiger_still_identified(self, species_clf, tmp_path):
        """A tiger image with filename hint should still be classified as TIGER."""
        img = _create_tiger_image()
        path = tmp_path / "tiger_t017_baghira.jpg"
        img.save(path, format="JPEG")

        result = species_clf.classify(path)
        assert result.is_tiger is True
        assert result.category == "TIGER"
        assert "Bengal Tiger" in result.species_name
        assert result.confidence >= 0.90

    def test_tiger_orange_palette_still_works(self, species_clf, tmp_path):
        """A tiger image without filename hint should still be detected via warm palette."""
        img = _create_tiger_image()
        path = tmp_path / "capture_unknown_003.jpg"
        img.save(path, format="JPEG")

        result = species_clf.classify(path)
        assert result.is_tiger is True
        assert result.category == "TIGER"

    def test_tiger_not_confused_with_deer(self, species_clf, tmp_path):
        """A tiger should NOT be classified as spotted deer."""
        img = _create_tiger_image()
        path = tmp_path / "camera_004.jpg"
        img.save(path, format="JPEG")

        result = species_clf.classify(path)
        assert result.category != "SPOTTED_DEER"
        assert result.category != "SLOTH_BEAR"


# ---- Visual Analyzer Unit Tests ----

class TestVisualAnalyzers:
    """Test the dedicated visual analyzers when available."""

    def test_spotted_deer_analyzer_exists(self):
        """The SpottedDeerAnalyzer module should be importable."""
        try:
            from ml.triage.spotted_deer_analyzer import SpottedDeerAnalyzer
            analyzer = SpottedDeerAnalyzer()
            assert analyzer is not None
        except ImportError:
            pytest.skip("SpottedDeerAnalyzer not installed yet")

    def test_sloth_bear_analyzer_exists(self):
        """The SlothBearAnalyzer module should be importable."""
        try:
            from ml.triage.sloth_bear_analyzer import SlothBearAnalyzer
            analyzer = SlothBearAnalyzer()
            assert analyzer is not None
        except ImportError:
            pytest.skip("SlothBearAnalyzer not installed yet")

    def test_deer_analyzer_on_deer_image(self, tmp_path):
        """SpottedDeerAnalyzer should return high confidence on a deer image."""
        try:
            from ml.triage.spotted_deer_analyzer import SpottedDeerAnalyzer
        except ImportError:
            pytest.skip("SpottedDeerAnalyzer not installed yet")

        analyzer = SpottedDeerAnalyzer()
        img = _create_spotted_deer_image()
        path = tmp_path / "deer_test.jpg"
        img.save(path, format="JPEG")

        result = analyzer.analyze(path)
        assert result.confidence > 0.3, f"Deer analyzer too low on deer image: {result.confidence}"
        assert result.fawn_body_ratio > 0.0
        assert result.white_spot_score > 0.0

    def test_deer_analyzer_on_tiger_image(self, tmp_path):
        """SpottedDeerAnalyzer should return low confidence on a tiger image."""
        try:
            from ml.triage.spotted_deer_analyzer import SpottedDeerAnalyzer
        except ImportError:
            pytest.skip("SpottedDeerAnalyzer not installed yet")

        analyzer = SpottedDeerAnalyzer()
        img = _create_tiger_image()
        path = tmp_path / "tiger_test.jpg"
        img.save(path, format="JPEG")

        result = analyzer.analyze(path)
        assert not result.is_likely_deer, f"Tiger falsely detected as deer! conf={result.confidence}"

    def test_bear_analyzer_on_bear_image(self, tmp_path):
        """SlothBearAnalyzer should return high confidence on a bear image."""
        try:
            from ml.triage.sloth_bear_analyzer import SlothBearAnalyzer
        except ImportError:
            pytest.skip("SlothBearAnalyzer not installed yet")

        analyzer = SlothBearAnalyzer()
        img = _create_sloth_bear_image()
        path = tmp_path / "bear_test.jpg"
        img.save(path, format="JPEG")

        result = analyzer.analyze(path)
        assert result.confidence > 0.3, f"Bear analyzer too low on bear image: {result.confidence}"
        assert result.dark_fur_ratio > 0.15

    def test_bear_analyzer_on_tiger_image(self, tmp_path):
        """SlothBearAnalyzer should return low confidence on a tiger image."""
        try:
            from ml.triage.sloth_bear_analyzer import SlothBearAnalyzer
        except ImportError:
            pytest.skip("SlothBearAnalyzer not installed yet")

        analyzer = SlothBearAnalyzer()
        img = _create_tiger_image()
        path = tmp_path / "tiger_test.jpg"
        img.save(path, format="JPEG")

        result = analyzer.analyze(path)
        assert not result.is_likely_bear, f"Tiger falsely detected as bear! conf={result.confidence}"

    def test_bear_analyzer_ir_nighttime(self, tmp_path):
        """SlothBearAnalyzer should handle IR nighttime images."""
        try:
            from ml.triage.sloth_bear_analyzer import SlothBearAnalyzer
        except ImportError:
            pytest.skip("SlothBearAnalyzer not installed yet")

        analyzer = SlothBearAnalyzer()
        img = _create_sloth_bear_ir_image()
        path = tmp_path / "ir_bear_test.jpg"
        img.save(path, format="JPEG")

        result = analyzer.analyze(path)
        assert result.is_ir_nighttime, "IR nighttime not detected"
        assert result.dark_fur_ratio > 0.15


# ---- Detection Category Tests ----

class TestDetectionCategories:
    """Test that new detection categories are properly defined."""

    def test_spotted_deer_category_exists(self):
        from app.models.detection import DetectionCategory
        assert hasattr(DetectionCategory, "SPOTTED_DEER")
        assert DetectionCategory.SPOTTED_DEER.value == "SPOTTED_DEER"

    def test_sloth_bear_category_exists(self):
        from app.models.detection import DetectionCategory
        assert hasattr(DetectionCategory, "SLOTH_BEAR")
        assert DetectionCategory.SLOTH_BEAR.value == "SLOTH_BEAR"

    def test_tiger_category_still_exists(self):
        from app.models.detection import DetectionCategory
        assert hasattr(DetectionCategory, "TIGER")
        assert DetectionCategory.TIGER.value == "TIGER"
