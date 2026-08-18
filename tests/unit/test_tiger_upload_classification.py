"""Comprehensive unit tests for tiger photo upload triage and classification.

Verifies that uploaded tiger photos (regardless of filename) are accurately
recognized as Bengal Tigers and NEVER falsely quarantined as Sloth Bears.
"""
import io
import shutil
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from PIL import Image as PILImage, ImageDraw
from app.services.species_classifier import SpeciesClassifier, species_classifier
from ml.triage.sloth_bear_analyzer import SlothBearAnalyzer
from ml.triage.spotted_deer_analyzer import SpottedDeerAnalyzer


def _create_synthetic_tiger(width=600, height=400):
    img = PILImage.new("RGB", (width, height), color=(217, 119, 6))
    draw = ImageDraw.Draw(img)
    for x in range(80, width - 60, 60):
        draw.polygon(
            [(x, 40), (x + 20, 200), (x - 10, 360), (x + 10, 360), (x + 35, 200), (x + 15, 40)],
            fill=(24, 24, 27)
        )
    return img


def _create_synthetic_sloth_bear(width=600, height=400):
    bg_color = (60, 75, 45)
    img = PILImage.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    body_color = (35, 30, 28)
    draw.ellipse([(100, 80), (500, 360)], fill=body_color)
    draw.ellipse([(60, 50), (180, 170)], fill=(40, 35, 32))
    draw.ellipse([(50, 110), (120, 155)], fill=(140, 130, 115))
    draw.polygon([(280, 120), (320, 120), (330, 220), (300, 260), (270, 220)], fill=(230, 225, 210))
    return img


class TestTigerUploadClassification:
    """Test suite ensuring tiger photo uploads are correctly classified as Tigers."""

    def test_tiger_with_generic_camera_filenames(self, tmp_path):
        """Tiger photos with standard camera filenames (DSC_*, IMG_*, etc.) must be TIGER."""
        clf = SpeciesClassifier()
        img = _create_synthetic_tiger()
        generic_names = [
            "DSC_0042.jpg",
            "IMG_9821.jpg",
            "live_capture.jpg",
            "photo.jpg",
            "upload_1234.png",
            "capture_frame.jpg",
            "webcam_snapshot.jpg",
        ]
        for name in generic_names:
            p = tmp_path / name
            img.save(p)
            res = clf.classify(p)
            assert res.is_tiger is True, f"Failed for {name}: is_tiger={res.is_tiger}, category={res.category}"
            assert res.category == "TIGER", f"Failed for {name}: category={res.category}"
            assert "Tiger" in res.species_name, f"Failed for {name}: species_name={res.species_name}"

    def test_real_sample_tiger_not_sloth_bear(self, tmp_path):
        """Real tiger sample image from storage must be classified as TIGER with neutral filename."""
        src = Path("storage/test_samples/tiger_baghira_sample.jpg")
        if not src.exists():
            pytest.skip("Test sample storage/test_samples/tiger_baghira_sample.jpg not found")

        clf = SpeciesClassifier()
        dst = tmp_path / "camera_trap_0049.jpg"
        shutil.copy(src, dst)

        res = clf.classify(dst)
        assert res.is_tiger is True, f"Real tiger misclassified! is_tiger={res.is_tiger}, category={res.category}"
        assert res.category == "TIGER", f"Real tiger categorized as {res.category}"
        assert res.confidence >= 0.85

    def test_sloth_bear_analyzer_rejects_tiger(self):
        """SlothBearAnalyzer must return is_likely_bear=False on tiger images."""
        analyzer = SlothBearAnalyzer()
        src = Path("storage/test_samples/tiger_baghira_sample.jpg")
        if src.exists():
            res = analyzer.analyze(src)
            assert res.is_likely_bear is False, f"Bear analyzer falsely flagged real tiger: {res}"
            assert res.confidence == 0.0, f"Bear analyzer confidence should be 0 for tiger: {res.confidence}"

    def test_sloth_bear_analyzer_accepts_sloth_bear(self, tmp_path):
        """SlothBearAnalyzer must recognize genuine sloth bear images."""
        analyzer = SlothBearAnalyzer()
        img = _create_synthetic_sloth_bear()
        p = tmp_path / "bear_test.jpg"
        img.save(p)

        res = analyzer.analyze(p)
        assert res.is_likely_bear is True, f"Bear analyzer failed on sloth bear image: {res}"
        assert res.confidence > 0.50, f"Bear analyzer confidence too low: {res.confidence}"

    def test_forest_blank_not_sloth_bear(self):
        """Forest foliage blank image must not be classified as sloth bear."""
        src = Path("storage/test_samples/forest_blank.jpg")
        if not src.exists():
            pytest.skip("forest_blank.jpg not found")

        clf = SpeciesClassifier()
        res = clf.classify(src)
        assert res.is_tiger is False
        assert res.category == "BLANK", f"Forest blank categorized as {res.category}"
