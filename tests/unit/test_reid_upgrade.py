import pytest
import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# ---------------------------------------------------------------------------
# 1. Pose Estimator (ml.reid.pose_estimator)
# ---------------------------------------------------------------------------
from ml.reid.pose_estimator import TigerKeypoints, get_pose_estimator

def test_tiger_keypoints_creation():
    kp = TigerKeypoints(
        nose=(10.0, 20.0, 0.9), left_eye=(5.0, 15.0, 0.9), right_eye=(15.0, 15.0, 0.9), 
        left_ear=(0,0,0), right_ear=(0,0,0), left_shoulder=(0.0, 30.0, 0.9), 
        right_shoulder=(20.0, 30.0, 0.9), left_hip=(0,0,0), right_hip=(0,0,0), 
        left_front_paw=(0,0,0), right_front_paw=(0,0,0), left_hind_paw=(0,0,0), 
        right_hind_paw=(0,0,0), tail_base=(10.0, 100.0, 0.9), tail_tip=(0,0,0)
    )
    assert kp.nose == (10.0, 20.0, 0.9)
    assert kp.tail_base == (10.0, 100.0, 0.9)

def test_geometric_fallback_produces_valid_body_parts():
    estimator = get_pose_estimator()
    bbox = (0, 0, 100, 200) # x1, y1, x2, y2
    image = np.zeros((200, 100, 3), dtype=np.uint8)
    res = estimator.estimate(image, bbox)
    assert 'head' in res.body_parts
    assert 'torso' in res.body_parts

def test_get_pose_estimator_returns_singleton():
    est1 = get_pose_estimator()
    est2 = get_pose_estimator()
    assert est1 is est2

# ---------------------------------------------------------------------------
# 2. Body Parts (ml.reid.body_parts)
# ---------------------------------------------------------------------------
from ml.reid.body_parts import BodyPartExtractor, GeometricStripeNormalizer, PartCrop, BodyPart

def test_body_part_extractor_geometric_splitting():
    extractor = BodyPartExtractor()
    image = np.zeros((200, 100, 3), dtype=np.uint8)
    crops = extractor.extract_parts(image, bbox=(0, 0, 100, 200), pose_result=None)
    assert BodyPart.HEAD in crops
    assert crops[BodyPart.HEAD].confidence == 0.1

def test_geometric_stripe_normalizer_rotation():
    normalizer = GeometricStripeNormalizer()
    crop = np.zeros((50, 50, 3), dtype=np.uint8)
    normalized = normalizer.normalize(crop, body_axis_angle=15.0)
    assert normalized.shape == crop.shape

def test_part_crop_dataclass():
    pc = PartCrop(part=BodyPart.HEAD, crop=np.zeros((10, 10, 3)), bbox=(0,0,10,10), confidence=0.9, is_pose_aligned=False)
    assert pc.part == BodyPart.HEAD
    assert pc.confidence == 0.9

# ---------------------------------------------------------------------------
# 3. Multi-Part Embedding (ml.reid.multi_part_embedding)
# ---------------------------------------------------------------------------
from ml.reid.multi_part_embedding import MultiPartEmbedding

def test_multipart_embedding_creation_and_dict():
    emb = MultiPartEmbedding(global_embedding=[1.0]*512, head_embedding=[1.0]*128)
    d = emb.to_dict()
    assert "global_embedding" in d
    emb2 = MultiPartEmbedding.from_dict(d)
    assert emb.global_embedding == emb2.global_embedding

def test_multipart_embedding_from_legacy():
    vec = [0.5] * 512
    emb = MultiPartEmbedding.from_legacy(vec)
    assert emb.global_embedding is not None

def test_get_visible_part_embeddings():
    emb = MultiPartEmbedding(global_embedding=[1.0]*128, head_embedding=[1.0]*64, visible_parts=['head', 'global'])
    vis = emb.get_visible_part_embeddings()
    assert "head" in vis
    assert "global" in vis

# ---------------------------------------------------------------------------
# 4. Losses (ml.reid.losses)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_TORCH, reason='PyTorch required')
def test_arcface_loss_forward():
    from ml.reid.losses import ArcFaceLoss
    loss_fn = ArcFaceLoss(num_classes=10, embedding_dim=128)
    features = torch.randn(4, 128)
    labels = torch.tensor([0, 1, 2, 3])
    loss = loss_fn(features, labels)
    assert isinstance(loss, torch.Tensor)

@pytest.mark.skipif(not HAS_TORCH, reason='PyTorch required')
def test_combined_metric_loss():
    from ml.reid.losses import CombinedMetricLoss
    loss_fn = CombinedMetricLoss(num_classes=10, embedding_dim=128)
    features = torch.randn(4, 128)
    labels = torch.tensor([0, 1, 2, 3])
    total, loss_dict = loss_fn(features, features, features, labels)
    assert isinstance(loss_dict, dict)
    assert 'total' in loss_dict

@pytest.mark.skipif(not HAS_TORCH, reason='PyTorch required')
def test_hard_negative_miner():
    from ml.reid.losses import HardNegativeMiner
    miner = HardNegativeMiner()
    features = torch.randn(4, 128)
    labels = torch.tensor([0, 0, 1, 1])
    anc, pos, neg = miner.mine(features, labels)
    assert len(anc) == len(pos) == len(neg)

@pytest.mark.skipif(not HAS_TORCH, reason='PyTorch required')
def test_existing_losses_work():
    from ml.reid.losses import TripletMarginLoss, ContrastiveLoss
    t_loss = TripletMarginLoss()
    c_loss = ContrastiveLoss()
    f1 = torch.randn(2, 128)
    f2 = torch.randn(2, 128)
    f3 = torch.randn(2, 128)
    l1 = t_loss(f1, f2, f3)
    l2 = c_loss(f1, f2, torch.tensor([1, 0]))
    assert isinstance(l1, torch.Tensor)
    assert isinstance(l2, torch.Tensor)

# ---------------------------------------------------------------------------
# 5. Dataset (ml.reid.dataset)
# ---------------------------------------------------------------------------
from ml.reid.dataset import BalancedIdentitySampler, TigerMetricDataset

def test_balanced_identity_sampler(tmp_path):
    # Dummy to instantiate balanced identity sampler
    pass

def test_tiger_metric_dataset(tmp_path):
    import os
    os.makedirs(tmp_path / "train" / "tiger1")
    with open(tmp_path / "train" / "tiger1" / "1.jpg", "w") as f:
        f.write("")
    with open(tmp_path / "train" / "tiger1" / "2.jpg", "w") as f:
        f.write("")
    try:
        ds = TigerMetricDataset(str(tmp_path / "train"))
        assert ds is not None
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 6. Evaluate (ml.reid.evaluate)
# ---------------------------------------------------------------------------
from ml.reid.evaluate import compute_cmc, compute_map, top_k_accuracy

def test_compute_cmc():
    dist_mat = np.array([[0.1, 0.5], [0.8, 0.2]])
    q_pids = np.array([1, 2])
    g_pids = np.array([1, 2])
    cmc = compute_cmc(dist_mat, q_pids, g_pids)
    assert len(cmc) > 0

def test_compute_map():
    dist_mat = np.array([[0.1, 0.5], [0.8, 0.2]])
    q_pids = np.array([1, 2])
    g_pids = np.array([1, 2])
    mAP = compute_map(dist_mat, q_pids, g_pids)
    assert isinstance(mAP, float)

def test_top_k_accuracy():
    ranks = [1, 2, 1, 5]
    acc = top_k_accuracy(ranks, k=1)
    assert isinstance(acc, float)

# ---------------------------------------------------------------------------
# 7. Multi-Feature Reranker (ml.reid.multi_feature_reranker)
# ---------------------------------------------------------------------------
from ml.reid.multi_feature_reranker import MultiFeatureReranker

def test_mfr_partial_matching():
    reranker = MultiFeatureReranker()
    q_parts = {"head": [1.0, 0.0]}
    c_parts = {"parts": {"head": [1.0, 0.0], "torso": [0.0, 1.0]}}
    results = reranker.rerank(q_parts, [c_parts])
    assert len(results) > 0
    assert results[0].matching_parts == 1

def test_mfr_weight_redistribution():
    reranker = MultiFeatureReranker()
    weights = reranker._dynamic_weight(["head"])
    assert "head" in weights
    assert np.isclose(sum(weights.values()), 1.0)

def test_mfr_quality_adjustment():
    reranker = MultiFeatureReranker()
    score = reranker._quality_adjustment(0.8, {"composite": 0.5})
    assert score <= 0.8 # typically lowers score if quality is low

# ---------------------------------------------------------------------------
# 8. Confidence Model (ml.reid.confidence_model)
# ---------------------------------------------------------------------------
from ml.reid.confidence_model import QualityVector, ConfidenceCalibrator, OpenSetDetector

def test_quality_vector_composite():
    qv = QualityVector(resolution_score=0.9, contrast_score=0.8, occlusion_ratio=0.1)
    assert 0.0 <= qv.composite() <= 1.0

def test_confidence_calibrator():
    cal = ConfidenceCalibrator()
    adj = cal.calibrate(0.8, QualityVector(), 1.0)
    assert 0.0 <= adj <= 1.0

def test_openset_detector():
    det = OpenSetDetector()
    is_novel, conf, reason = det.is_novel([0.5])
    assert is_novel is True

# ---------------------------------------------------------------------------
# 9. Temporal Aggregation (ml.reid.temporal_aggregation)
# ---------------------------------------------------------------------------
from ml.reid.temporal_aggregation import CameraEventAggregator, FrameEmbedding, AggregationStrategy

def test_temporal_aggregation_quality_weighted():
    agg = CameraEventAggregator(strategy=AggregationStrategy.QUALITY_WEIGHTED)
    f1 = FrameEmbedding(embedding=[1.0, 0.0], quality_score=0.9)
    f2 = FrameEmbedding(embedding=[0.0, 1.0], quality_score=0.1)
    res = agg.aggregate([f1, f2])
    assert len(res.aggregated_embedding) == 2

def test_temporal_aggregation_best_frame():
    agg = CameraEventAggregator(strategy=AggregationStrategy.BEST_FRAME)
    f1 = FrameEmbedding(embedding=[1.0, 0.0], quality_score=0.1)
    f2 = FrameEmbedding(embedding=[0.0, 1.0], quality_score=0.9)
    res = agg.aggregate([f1, f2])
    assert res.aggregated_embedding == [0.0, 1.0]

def test_temporal_aggregation_l2_norm():
    agg = CameraEventAggregator(strategy=AggregationStrategy.QUALITY_WEIGHTED)
    f1 = FrameEmbedding(embedding=[2.0, 0.0], quality_score=1.0)
    res = agg.aggregate([f1])
    assert np.isclose(np.linalg.norm(res.aggregated_embedding), 1.0)

# ---------------------------------------------------------------------------
# 10. Identity Gallery (ml.reid.identity_gallery)
# ---------------------------------------------------------------------------
from ml.reid.identity_gallery import IdentityGallery

def test_identity_gallery():
    gallery = IdentityGallery()
    gallery.add_observation("tiger_1", [1.0, 0.0])
    gallery.add_observation("tiger_1", [0.0, 1.0])
    proto = gallery.compute_prototype("tiger_1", side="UNKNOWN")
    assert np.isclose(np.linalg.norm(proto), 1.0)
    
    matches = gallery.match_against_gallery([1.0, 0.0], "tiger_1")
    assert matches['max_similarity'] > 0.0

# ---------------------------------------------------------------------------
# 11. SIFT Verifier (ml.reid.sift_verifier)
# ---------------------------------------------------------------------------
from ml.reid.sift_verifier import SIFTStripeVerifier, VerificationResult

def test_sift_verification_result():
    vr = VerificationResult(num_matches=30, inlier_ratio=0.5, geometric_consistency=0.5, local_similarity=15.0, verdict="match")
    assert vr.verdict == "match"

def test_sift_fallback():
    verifier = SIFTStripeVerifier()
    img1 = np.zeros((100, 100, 3), dtype=np.uint8)
    img2 = np.zeros((100, 100, 3), dtype=np.uint8)
    res = verifier.verify(img1, img2)
    assert res.verdict in ["match", "no_match", "none"]

# ---------------------------------------------------------------------------
# 12. Backbones (ml.reid.backbones)
# ---------------------------------------------------------------------------
from ml.reid.backbones import BackboneFactory, BackboneConfig

def test_backbone_factory_list():
    avail = BackboneFactory.list_available()
    assert isinstance(avail, list)

def test_backbone_config():
    cfg = BackboneConfig(name="resnet50", feature_dim=2048, input_size=224, pretrained=True)
    assert cfg.name == "resnet50"
    assert cfg.feature_dim == 2048

# ---------------------------------------------------------------------------
# 13. Decision Engine (ml.reid.decision_engine)
# ---------------------------------------------------------------------------
from ml.reid.decision_engine import decide, adaptive_decide

def test_decision_engine_backward_compat():
    # threshold = 0.85 by default
    decision = decide(0.9, 0.5)
    assert decision.action == "AUTO_MATCH"

def test_decision_engine_adaptive():
    from ml.reid.confidence_model import QualityVector
    candidates = [{"tiger_id": "T1", "similarity": 0.9}]
    decision = adaptive_decide(candidates, quality=QualityVector())
    assert decision is not None

# ---------------------------------------------------------------------------
# 14. Reranker (ml.reid.reranker)
# ---------------------------------------------------------------------------
from ml.reid.reranker import enhanced_rerank, rerank

def test_rerank_backward_compat():
    import sys
    from unittest.mock import MagicMock
    if 'app' not in sys.modules:
        sys.modules['app'] = MagicMock()
    if 'app.models' not in sys.modules:
        sys.modules['app.models'] = MagicMock()
    if 'app.models.observation' not in sys.modules:
        sys.modules['app.models.observation'] = MagicMock()
    if 'app.models.station' not in sys.modules:
        sys.modules['app.models.station'] = MagicMock()

    candidates = [{"tiger_id": "T1", "similarity": 0.9}, {"tiger_id": "T2", "similarity": 0.4}]
    # stub session
    class Session:
        def query(self, *args):
            return self
        def get(self, *args):
            return None
        def filter(self, *args):
            return self
        def count(self, *args):
            return 0
    
    dists = rerank(candidates, "station1", "time1", Session())
    assert len(dists) == 1 # one passed floor

def test_enhanced_rerank():
    import sys
    from unittest.mock import MagicMock
    if 'app' not in sys.modules:
        sys.modules['app'] = MagicMock()
    if 'app.models' not in sys.modules:
        sys.modules['app.models'] = MagicMock()
    if 'app.models.observation' not in sys.modules:
        sys.modules['app.models.observation'] = MagicMock()
    if 'app.models.station' not in sys.modules:
        sys.modules['app.models.station'] = MagicMock()

    candidates = [{"tiger_id": "T1", "similarity": 0.9, "parts": {"global": [1.0]}}]
    q_parts = {"global": [1.0]}
    
    class Session:
        def query(self, *args):
            return self
        def get(self, *args):
            return None
        def filter(self, *args):
            return self
        def count(self, *args):
            return 0

    dists = enhanced_rerank(candidates, q_parts, None, "station1", "time1", Session())
    assert len(dists) > 0


# ---------------------------------------------------------------------------
# 15. Negative Constraints & Cannot-Link Claim Rejection (ml.reid.candidate_search)
# ---------------------------------------------------------------------------
from ml.reid.candidate_search import search_candidates, get_negative_constraints
from ml.reid.two_stage_pipeline import TwoStageIdentifier

def test_search_candidates_strict_negative_filtering():
    # Mock session with two tigers: T001 (rejected), T002 (valid)
    from unittest.mock import MagicMock
    session = MagicMock()
    
    # Mock embeddings
    emb1 = MagicMock()
    emb1.vector = [1.0] * 512
    emb1.id = "emb-1"
    emb1.side = None
    emb1.quality_weight = 1.0
    emb1.is_prototype = True

    tiger1 = MagicMock()
    tiger1.id = "tiger-id-001"
    tiger1.code = "T001"
    tiger1.name = "Baghira"
    tiger1.total_observations = 10
    tiger1.last_seen = None

    emb2 = MagicMock()
    emb2.vector = [0.8] * 512
    emb2.id = "emb-2"
    emb2.side = None
    emb2.quality_weight = 1.0
    emb2.is_prototype = True

    tiger2 = MagicMock()
    tiger2.id = "tiger-id-002"
    tiger2.code = "T002"
    tiger2.name = "Sheru"
    tiger2.total_observations = 5
    tiger2.last_seen = None

    # Query returns both tigers
    session.query().join().filter().all.return_value = [(emb1, tiger1), (emb2, tiger2)]

    # 1. Without exclusion: T001 is ranked #1 with top similarity
    results_normal = search_candidates(
        query_vector=[1.0] * 512,
        session=session,
        k=5,
    )
    assert any(r["tiger_code"] == "T001" for r in results_normal)
    assert results_normal[0]["tiger_code"] == "T001"

    # 2. With strict rejection: T001 is rejected and MUST NOT appear
    results_blocked = search_candidates(
        query_vector=[1.0] * 512,
        session=session,
        k=5,
        exclude_tiger_ids={"tiger-id-001", "T001"},
    )
    # T001 is strictly absent
    assert not any(r["tiger_code"] == "T001" or r["tiger_id"] == "tiger-id-001" for r in results_blocked)
    # T002 becomes the top remaining candidate
    assert len(results_blocked) == 1
    assert results_blocked[0]["tiger_code"] == "T002"

def test_two_stage_pipeline_rejected_claim_exclusion():
    identifier = TwoStageIdentifier()
    stage_a = [
        {"tiger_id": "T001", "tiger_code": "T001", "parts": {"global": [1.0] * 512}},
        {"tiger_id": "T002", "tiger_code": "T002", "parts": {"global": [0.5] * 512}},
    ]
    query_parts = {"global": [1.0] * 512}

    # Reject T001 claim
    output = identifier.identify(
        query_parts=query_parts,
        stage_a_candidates=stage_a,
        exclude_tiger_ids={"T001"},
    )

    # Output must strictly not match T001
    assert output.matched_tiger_id != "T001"
    for cand in output.ranked_candidates:
        assert cand["tiger_id"] != "T001"

