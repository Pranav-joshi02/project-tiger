import sys
from pathlib import Path

# Add project root and apps/api to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api"))

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta


# ============================================================================
# 1. Multi-Biometric Fusion & Signatures
# ============================================================================
def test_multi_biometric_extractor_and_fusion():
    from ml.reid.multi_biometric import (
        BiometricRegion,
        BiometricSignature,
        MultiBiometricExtractor,
        MultiBiometricFusion,
    )

    extractor = MultiBiometricExtractor()
    dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
    signatures = extractor.extract(dummy_img, None)

    assert BiometricRegion.FACE in signatures
    assert BiometricRegion.LEFT_FLANK in signatures
    assert len(signatures[BiometricRegion.FACE].vector) == 128
    assert len(signatures[BiometricRegion.LEFT_FLANK].vector) == 256

    fusion = MultiBiometricFusion()
    sims = {
        BiometricRegion.FACE: 0.94,
        BiometricRegion.LEFT_FLANK: 0.98,
        BiometricRegion.RIGHT_FLANK: 0.95,
        BiometricRegion.HIND_LEG: 0.91,
    }
    quals = {r: 1.0 for r in sims}
    result = fusion.fuse(sims, quals)
    assert "final_score" in result
    assert result["final_score"] > 0.90


# ============================================================================
# 2. Tiger Identity Fingerprint & Evidence Breakdown
# ============================================================================
def test_tiger_fingerprint_and_matcher():
    from ml.reid.fingerprint import TigerFingerprint, FingerprintMatcher

    fp1 = TigerFingerprint(
        tiger_id="T023",
        biometric_signatures={
            "face": [1.0, 0.0, 0.0] * 42 + [1.0, 0.0],
            "left_flank": [0.5, 0.5] * 128,
            "right_flank": [0.5, 0.5] * 128,
            "hind_leg": [0.3] * 128,
        },
        stripe_topology={"branch_points": 14, "curvature_avg": 0.32},
        morphological_traits={"aspect_ratio": 2.1},
        quality_metrics={"blur": 0.95, "exposure": 0.92},
        created_at=datetime.now(timezone.utc).isoformat(),
        model_version="v2.0-multi",
    )

    d = fp1.to_dict()
    fp_restored = TigerFingerprint.from_dict(d)
    assert fp_restored.tiger_id == "T023"

    breakdown = fp1.get_evidence_breakdown(fp1)
    assert "Left Flank" in breakdown or "Final" in breakdown

    matcher = FingerprintMatcher([fp1])
    matches = matcher.match(fp1)
    assert len(matches) > 0
    assert matches[0]["tiger_id"] == "T023"


# ============================================================================
# 3. Explainable AI & Stripe Correspondence
# ============================================================================
def test_explainable_ai():
    from ml.reid.xai import ExplainableReID

    xai = ExplainableReID()
    dummy_img = np.zeros((200, 300, 3), dtype=np.uint8)
    heatmap = xai.generate_attention_map(dummy_img, (10, 10, 100, 100))
    assert heatmap.shape[:2] == (200, 300)

    corr = xai.compute_stripe_correspondence(dummy_img, dummy_img)
    assert "correspondence_score" in corr

    report = xai.generate_evidence_report(
        {"id": "query_1"},
        {"id": "T023"},
        {"final_score": 0.95, "breakdown": {"FACE": 0.94, "LEFT_FLANK": 0.98}},
    )
    assert "recommendation" in report
    assert report["match_probability"] == 0.95


# ============================================================================
# 4. Topological Stripe Geometry
# ============================================================================
def test_stripe_geometry():
    from ml.reid.stripe_geometry import StripeGeometryDescriptor

    geo = StripeGeometryDescriptor()
    crop = np.zeros((128, 256, 3), dtype=np.uint8)
    res = geo.extract_geometry(crop)

    assert "S_stripe" in res
    score = geo.compare_geometry(res, res)
    assert 0.0 <= score <= 1.0


# ============================================================================
# 5. Calibrated Confidence Scaling
# ============================================================================
def test_calibrated_confidence():
    from ml.reid.calibration import CalibratedConfidence

    calibrator = CalibratedConfidence()
    p_high = calibrator.calibrate(0.95, quality_vector={"blur": 0.9, "exposure": 0.9}, method="platt")
    assert 0.0 <= p_high <= 1.0


# ============================================================================
# 6. 360° Synthetic Augmentation
# ============================================================================
def test_synthetic_view_augmenter():
    from ml.reid.synthetic_aug import SyntheticViewAugmenter

    aug = SyntheticViewAugmenter()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    views = aug.generate_transformations(img)
    assert len(views) >= 1
    assert "type" in views[0]


# ============================================================================
# 7. Multi-Object Tracking (MOT)
# ============================================================================
def test_mot_tracker():
    from ml.tracking.tracker import TigerMultiObjectTracker

    tracker = TigerMultiObjectTracker()
    detections = [{"bbox": (50, 50, 150, 150), "confidence": 0.95, "feature": [0.1] * 512}]
    tracks = tracker.update(detections, timestamp="2026-08-17T12:00:00Z")
    assert len(tracks) >= 1
    assert tracks[0].track_id == 1


# ============================================================================
# 8. Tracklet Re-ID
# ============================================================================
def test_tracklet_reid():
    from ml.tracking.tracker import Tracklet
    from ml.tracking.tracklet_reid import TrackletReID

    t = Tracklet(
        track_id=1,
        bboxes=[(0.0, 0.0, 100.0, 100.0), (5.0, 5.0, 105.0, 105.0)],
        timestamps=["2026-08-17T12:00:00Z", "2026-08-17T12:00:01Z"],
        confidences=[0.9, 0.95],
        features=[[1.0] * 512, [1.0] * 512],
        state="active",
    )

    reid = TrackletReID()
    fused_emb = reid.aggregate_tracklet_features(t)
    assert len(fused_emb) == 512


# ============================================================================
# 9. Wildlife Behavioral Recognition
# ============================================================================
def test_behavior_classifier():
    from ml.tracking.tracker import Tracklet
    from ml.behavior.classifier import TigerBehaviorClassifier, BehaviorClass

    clf = TigerBehaviorClassifier()
    t = Tracklet(
        track_id=1,
        bboxes=[(0.0, 0.0, 100.0, 100.0), (10.0, 0.0, 110.0, 100.0), (20.0, 0.0, 120.0, 100.0)],
        timestamps=["2026-08-17T12:00:00Z", "2026-08-17T12:00:01Z", "2026-08-17T12:00:02Z"],
        confidences=[0.9, 0.9, 0.9],
        features=[],
        state="active",
    )

    pred = clf.classify_sequence(t, fps=10.0)
    assert pred.behavior in BehaviorClass
    assert 0.0 <= pred.confidence <= 1.0


# ============================================================================
# 10. Self-Supervised Contrastive Learning (SSL)
# ============================================================================
def test_ssl_temporal_contrastive():
    from ml.reid.self_supervised import TemporalContrastiveSSL

    ssl = TemporalContrastiveSSL()
    assert ssl is not None


# ============================================================================
# 11. Continual Learning & Exemplar Replay
# ============================================================================
def test_continual_reid():
    from ml.reid.continual import ContinualReID

    cl = ContinualReID(memory_size_per_class=10, feature_dim=512)
    cl.add_exemplar("T023", [0.5] * 512)
    cl.add_exemplar("T023", [0.6] * 512)

    gallery = cl.get_gallery()
    assert "T023" in gallery
    assert len(gallery["T023"]) == 512


# ============================================================================
# 12. Active Learning Query Engine
# ============================================================================
def test_active_learning_engine():
    from ml.reid.active_learning import ActiveLearningEngine

    al = ActiveLearningEngine(strategy="margin")
    candidates = [
        {"id": "img1", "probabilities": [0.88, 0.86, 0.02]},
        {"id": "img2", "probabilities": [0.99, 0.01, 0.00]},
    ]
    sampled = al.select_samples(candidates, num_select=1)
    assert len(sampled) == 1
    assert sampled[0]["id"] == "img1"


# ============================================================================
# 13. Longitudinal Identity & Aging
# ============================================================================
def test_longitudinal_identity():
    from ml.reid.longitudinal import LongitudinalIdentityTracker, LongitudinalRecord

    tracker = LongitudinalIdentityTracker()
    rec1 = LongitudinalRecord(
        year=2024,
        observation_id="obs_001",
        biometric_fingerprint={"flank": 0.5},
        morphological_condition={"body_condition_index": "0.85"},
    )
    rec2 = LongitudinalRecord(
        year=2026,
        observation_id="obs_002",
        biometric_fingerprint={"flank": 0.52},
        morphological_condition={"body_condition_index": "0.82"},
    )
    tracker.add_record("T023", rec1)
    tracker.add_record("T023", rec2)

    stability = tracker.analyze_stability("T023")
    assert "pattern_stability" in stability
    assert stability["years_tracked"] == 2.0


# ============================================================================
# 14. Physical Injury & Scar Detector
# ============================================================================
def test_injury_detector():
    from ml.reid.injury_detector import InjuryAndScarDetector

    detector = InjuryAndScarDetector(sensitivity=0.5)
    current_features = {"gait_irregularity": 0.85, "left_ear_profile": 0.5}
    reference_features = {"left_ear_profile": 1.0}

    res = detector.detect_anomalies(current_features, reference_features)
    assert res.injury_detected is True
    assert len(res.injuries) >= 1


# ============================================================================
# 15. Tiger Identity Graph
# ============================================================================
def test_tiger_identity_graph():
    from spatial.identity_graph import TigerIdentityGraph

    graph = TigerIdentityGraph()
    graph.add_sighting("T023", "ST_01", datetime(2026, 8, 1, 10, 0), (21.65, 79.25))
    graph.add_sighting("T023", "ST_02", datetime(2026, 8, 2, 11, 0), (21.68, 79.28))
    graph.add_sighting("T017", "ST_02", datetime(2026, 8, 3, 14, 0), (21.68, 79.28))

    traj = graph.get_trajectory("T023", datetime(2026, 8, 1), datetime(2026, 8, 5))
    assert len(traj) == 2

    overlap = graph.compute_territory_overlap("T023", "T017")
    assert 0.0 <= overlap <= 1.0


# ============================================================================
# 16. Bayesian Spatio-Temporal Feasibility
# ============================================================================
def test_bayesian_spatiotemporal_feasibility():
    from spatial.spatiotemporal_bayesian import BayesianSpatioTemporalFeasibility

    checker = BayesianSpatioTemporalFeasibility(max_speed_kmh=15.0)

    # 5 km in 2 hours -> feasible
    p_ok = checker.compute_feasibility(
        last_coord=(21.65, 79.25),
        last_time=datetime(2026, 8, 1, 10, 0),
        new_coord=(21.69, 79.27),
        new_time=datetime(2026, 8, 1, 12, 0),
    )
    assert p_ok > 0.5

    # 50 km in 5 minutes -> impossible teleport
    p_teleport = checker.compute_feasibility(
        last_coord=(21.65, 79.25),
        last_time=datetime(2026, 8, 1, 10, 0),
        new_coord=(22.10, 79.90),
        new_time=datetime(2026, 8, 1, 10, 5),
    )
    assert p_teleport < 0.1


# ============================================================================
# 17. Environmental Covariates
# ============================================================================
def test_environmental_enricher():
    from spatial.environmental import EnvironmentalContextEnricher

    enricher = EnvironmentalContextEnricher()
    covs = enricher.fetch_covariates((21.65, 79.25), datetime.now())
    assert covs is not None
    assert hasattr(covs, "ndvi")
    suitability = enricher.calculate_habitat_suitability(covs)
    assert 0.0 <= suitability <= 1.0


# ============================================================================
# 18. Movement Anomaly Detection
# ============================================================================
def test_movement_anomaly_detector():
    from analytics.movement_anomaly import MovementAnomalyDetector

    detector = MovementAnomalyDetector()
    detector.add_buffer_zone(22.10, 79.90, radius_km=5.0)

    history = [
        ((21.65, 79.25), datetime(2026, 8, 1)),
        ((21.66, 79.26), datetime(2026, 8, 2)),
    ]
    alerts = detector.evaluate_sighting("T023", (22.10, 79.90), datetime(2026, 8, 4), history)
    assert isinstance(alerts, list)


# ============================================================================
# 19. Human-Wildlife Conflict Prediction
# ============================================================================
def test_conflict_prediction():
    from analytics.conflict_prediction import ConflictRiskPredictor, ConflictRiskLevel

    predictor = ConflictRiskPredictor()
    predictor.add_village("Awarghani", (21.66, 79.26))

    trajectory = [(21.65, 79.25), (21.658, 79.258)]
    assessment = predictor.assess_risk(trajectory, datetime.now())
    assert assessment.risk_level in ConflictRiskLevel
    assert assessment.risk_score >= 0.0


# ============================================================================
# 20. SECR Population Density Estimation
# ============================================================================
def test_secr_population_density():
    from analytics.secr import SpatiallyExplicitCaptureRecapture

    traps = {f"T{i}": (21.60 + i * 0.01, 79.20 + i * 0.01) for i in range(5)}
    secr = SpatiallyExplicitCaptureRecapture(trap_locations=traps)

    captures = [
        {"tiger_id": "T001", "trap_id": "T0", "timestamp": datetime.now()},
        {"tiger_id": "T002", "trap_id": "T1", "timestamp": datetime.now()},
    ]

    res = secr.estimate_population(captures, study_area_km2=500.0)
    assert res.estimated_density >= 0.0
    assert res.ci_upper >= res.ci_lower


# ============================================================================
# 21. Camera Placement Optimizer
# ============================================================================
def test_camera_placement_optimizer():
    from analytics.camera_optimizer import CameraPlacementOptimizer

    stations = [{"id": "C1", "coords": (21.65, 79.25), "type": "dual"}]
    optimizer = CameraPlacementOptimizer(current_stations=stations)

    opt_res = optimizer.optimize_grid(target_grid_size_km=2.0, budget_new_cameras=3)
    assert opt_res.expected_capture_boost_pct > 0
    assert len(opt_res.recommended_new_stations) == 3


# ============================================================================
# 22. Role-Based Spatial Privacy Obfuscation
# ============================================================================
def test_rbac_spatial_privacy():
    from apps.api.app.core.rbac_spatial import SpatialPrivacyFilter, UserSpatialRole

    f = SpatialPrivacyFilter()
    obs = {"tiger_id": "T023", "latitude": 21.654321, "longitude": 79.256789, "reserve": "Pench MP"}

    # Public: no precise coords
    public_view = f.filter_observation(obs, UserSpatialRole.PUBLIC)
    assert "latitude" not in public_view or public_view["latitude"] is None

    # Researcher: grid obfuscated
    res_view = f.filter_observation(obs, UserSpatialRole.RESEARCHER)
    assert res_view["latitude"] != obs["latitude"]

    # Forest Officer: exact coords
    officer_view = f.filter_observation(obs, UserSpatialRole.FOREST_OFFICER)
    assert officer_view["latitude"] == obs["latitude"]


# ============================================================================
# 23. Cryptographic Merkle Audit Trail
# ============================================================================
def test_merkle_audit_trail():
    from apps.api.app.core.merkle_audit import MerkleAuditTrail

    audit = MerkleAuditTrail()
    r1 = audit.add_record("IDENTIFY", {"tiger_id": "T023", "confidence": 0.98})
    r2 = audit.add_record("HUMAN_CONFIRM", {"tiger_id": "T023", "reviewer": "officer_01"})

    block = audit.commit_block()
    assert block.merkle_root is not None
    assert block.index >= 0

    valid, reason = audit.verify_integrity([block])
    assert valid is True


# ============================================================================
# 24. Model-Version Provenance Tracking
# ============================================================================
def test_model_provenance():
    from apps.api.app.core.provenance import ModelProvenanceTracker, ModelProvenance

    active_prov = ModelProvenance(
        model_version="v2.0-convnext",
        model_hash="sha256:abc12345",
        backbone="convnext_small",
        feature_dim=512,
        weights_checksum="sha256:def67890",
        threshold=0.85,
        preprocessing_version="1.0",
        inference_timestamp=str(datetime.now().timestamp()),
    )
    tracker = ModelProvenanceTracker(active_model_provenance=active_prov)

    rec = {"tiger_id": "T023", "score": 0.95}
    token = tracker.generate_provenance_token(rec, image_hash="sha256:img001")
    assert token is not None

    record_with_prov = tracker.attach_provenance(rec, image_hash="sha256:img001")
    assert "provenance_token" in record_with_prov
    assert record_with_prov["provenance"]["model_version"] == "v2.0-convnext"


# ============================================================================
# 25. Multi-Scale Feature Pyramid (Inverted FPN)
# ============================================================================
def test_multi_scale_fpn():
    from ml.reid.multi_scale_fpn import MultiScaleFeaturePyramid

    fpn = MultiScaleFeaturePyramid(out_dim=512)
    dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
    pyramid = fpn.extract_pyramid_features(dummy_img)

    assert "low_level_texture" in pyramid
    assert "mid_level_parts" in pyramid
    assert "high_level_global" in pyramid

    fused_512 = fpn.fuse_pyramid(pyramid)
    assert len(fused_512) == 512
    assert abs(np.linalg.norm(fused_512) - 1.0) < 1e-4


# ============================================================================
# 26. Similarity Gap Evaluator (G = S1 - S2)
# ============================================================================
def test_similarity_gap_evaluator():
    from ml.reid.similarity_gap import SimilarityGapEvaluator

    gap_eval = SimilarityGapEvaluator(auto_threshold=0.85, margin_threshold=0.08)

    # Case A: Clear match (High similarity + Large gap) -> AUTO_MATCH
    candidates_a = [
        {"tiger_id": "T023", "similarity": 0.96},
        {"tiger_id": "T017", "similarity": 0.71},
    ]
    res_a = gap_eval.evaluate(candidates_a)
    assert res_a.decision_action == "AUTO_MATCH"
    assert res_a.gap == pytest.approx(0.25, 0.01)

    # Case B: Ambiguous twin match (High similarity + Small gap) -> REVIEW_REQUIRED
    candidates_b = [
        {"tiger_id": "T023", "similarity": 0.91},
        {"tiger_id": "T017", "similarity": 0.90},
    ]
    res_b = gap_eval.evaluate(candidates_b)
    assert res_b.decision_action == "REVIEW_REQUIRED"
    assert res_b.gap < 0.08


# ============================================================================
# 27. Two-Stage Identification Pipeline
# ============================================================================
def test_two_stage_identifier():
    from ml.reid.two_stage_pipeline import TwoStageIdentifier

    identifier = TwoStageIdentifier(top_k_stage_a=20, final_k_stage_b=3)

    query_parts = {
        "global": [0.5] * 512,
        "flank": [0.4] * 256,
        "head": [0.3] * 128,
    }
    stage_a_cands = [
        {"tiger_id": "T023", "similarity": 0.95, "flank": [0.4] * 256, "head": [0.3] * 128, "global": [0.5] * 512},
        {"tiger_id": "T017", "similarity": 0.75, "flank": [0.1] * 256, "head": [0.1] * 128, "global": [0.2] * 512},
    ]

    out = identifier.identify(query_parts, stage_a_cands, query_id="query_test_01")
    assert out.decision in ("AUTO_MATCH", "REVIEW_REQUIRED")
    assert out.matched_tiger_id == "T023"
    assert len(out.ranked_candidates) <= 3
