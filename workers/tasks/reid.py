"""Tiger Re-ID task with multi-feature re-ranking and adaptive confidence.

Upgraded pipeline (Items #5, #9, #10, #11, #12, #13, #18):
1. Top-20 pgvector candidate retrieval (was Top-5)
2. Multi-feature re-ranking (global + flank + head + hind similarities)
3. Spatio-temporal context re-ranking
4. SIFT/ORB stripe verification (secondary signal)
5. Adaptive confidence calibration (quality-aware)
6. Open-set recognition for novel individual detection
"""
import logging
import uuid
import os
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.reid.identify_tigers", queue="reid")
def identify_tigers(run_id: str) -> dict:
    """Match embeddings against known tiger catalogue with multi-factor scoring."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.embedding import Embedding
    from app.models.flank import Flank
    from app.models.detection import Detection
    from app.models.image import Image
    from app.models.run import Run
    from app.models.observation import Observation
    from app.models.review import Review

    from ml.reid.candidate_search import search_candidates
    from ml.reid.decision_engine import decide
    from ml.reid.enrollment import enroll
    from ml.reid.reranker import rerank

    # Try to load enhanced modules (graceful fallback)
    try:
        from ml.reid.reranker import enhanced_rerank
        has_enhanced_rerank = True
    except ImportError:
        has_enhanced_rerank = False

    try:
        from ml.reid.decision_engine import adaptive_decide
        has_adaptive_decide = True
    except ImportError:
        has_adaptive_decide = False

    try:
        from ml.reid.sift_verifier import SIFTStripeVerifier
        sift_verifier = SIFTStripeVerifier()
        has_sift = True
    except ImportError:
        has_sift = False

    try:
        from ml.reid.confidence_model import QualityVector
        has_quality_model = True
    except ImportError:
        has_quality_model = False

    db = get_worker_db()
    try:
        embeddings = (
            db.query(Embedding, Image)
            .join(Flank)
            .join(Detection)
            .join(Image)
            .filter(Image.run_id == uuid.UUID(run_id), Embedding.tiger_id.is_(None))
            .all()
        )

        auto_matched = 0
        new_tigers = 0
        for_review = 0
        sift_verified = 0

        for emb, image in embeddings:
            # 1. Search — Top-20 retrieval (Item #9)
            candidates = search_candidates(
                emb.vector, session=db, side_filter=emb.side, k=20
            )

            # 2. Multi-feature re-ranking (Items #5, #10, #18)
            query_parts = {}
            if emb.head_embedding is not None:
                query_parts["head"] = (
                    list(emb.head_embedding) if not isinstance(emb.head_embedding, list)
                    else emb.head_embedding
                )
            if emb.flank_embedding is not None:
                query_parts["flank"] = (
                    list(emb.flank_embedding) if not isinstance(emb.flank_embedding, list)
                    else emb.flank_embedding
                )
            if emb.hind_embedding is not None:
                query_parts["hind"] = (
                    list(emb.hind_embedding) if not isinstance(emb.hind_embedding, list)
                    else emb.hind_embedding
                )
            query_parts["global"] = (
                list(emb.vector) if not isinstance(emb.vector, list) else emb.vector
            )

            # Build quality vector (Item #13)
            quality = None
            if has_quality_model:
                try:
                    flank_obj = emb.flank
                    quality = QualityVector.from_flank_scores(
                        blur=flank_obj.blur_score if flank_obj and flank_obj.blur_score else 1.0,
                        exposure=flank_obj.exposure_score if flank_obj and flank_obj.exposure_score else 1.0,
                        occlusion=flank_obj.occlusion_score if flank_obj and flank_obj.occlusion_score else 0.0,
                    )
                except Exception:
                    quality = None

            # Apply enhanced reranking if available
            station_id = image.station_id if hasattr(image, "station_id") else None
            if has_enhanced_rerank and query_parts:
                try:
                    reranked = enhanced_rerank(
                        candidates=candidates,
                        query_parts=query_parts,
                        query_quality=quality.to_dict() if quality else None,
                        query_station_id=station_id,
                        query_timestamp=image.captured_at,
                        session=db,
                    )
                except Exception as e:
                    logger.debug(f"Enhanced reranking failed: {e}. Using standard reranking.")
                    reranked = rerank(candidates, station_id, image.captured_at, db)
            else:
                # Fallback to standard spatio-temporal reranking
                reranked = rerank(candidates, station_id, image.captured_at, db)

            # 3. Decide — adaptive confidence (Items #11, #12)
            if has_adaptive_decide and quality:
                try:
                    pose_compat = emb.pose_confidence if emb.pose_confidence else 1.0
                    decision = adaptive_decide(
                        reranked,
                        quality=quality,
                        pose_compatibility=pose_compat,
                    )
                except Exception as e:
                    logger.debug(f"Adaptive decide failed: {e}. Using standard decide.")
                    decision = decide(reranked)
            else:
                decision = decide(reranked)

            # 4. Optional SIFT verification (Item #6) for borderline cases
            if has_sift and decision.action in ("AUTO_MATCH", "REVIEW_REQUIRED"):
                if decision.metadata and decision.metadata.get("top_sim", 0) < 0.92:
                    try:
                        import cv2
                        query_img = cv2.imread(str(image.storage_uri))
                        if query_img is not None and decision.tiger_id:
                            # Find candidate's best observation image
                            candidate_emb = db.query(Embedding).filter(
                                Embedding.tiger_id == uuid.UUID(decision.tiger_id),
                                Embedding.is_prototype == True,
                            ).first()
                            if candidate_emb and candidate_emb.flank:
                                candidate_det = candidate_emb.flank.detection
                                if candidate_det and candidate_det.image:
                                    candidate_img = cv2.imread(str(candidate_det.image.storage_uri))
                                    if candidate_img is not None:
                                        sift_result = sift_verifier.verify(query_img, candidate_img)
                                        sift_verified += 1
                                        # Downgrade auto-match if SIFT is weak
                                        if (
                                            decision.action == "AUTO_MATCH"
                                            and sift_result.verdict == "weak"
                                        ):
                                            decision = decide.__class__(
                                                action="REVIEW_REQUIRED",
                                                tiger_id=decision.tiger_id,
                                                reason=f"SIFT verification weak ({sift_result.inlier_ratio:.2f})",
                                                metadata={
                                                    **(decision.metadata or {}),
                                                    "sift_verdict": sift_result.verdict,
                                                    "sift_inlier_ratio": sift_result.inlier_ratio,
                                                },
                                            )
                    except Exception as e:
                        logger.debug(f"SIFT verification skipped: {e}")

            # 5. Act on decision
            if decision.action == "AUTO_MATCH" and decision.tiger_id:
                # Enroll existing tiger with high confidence
                enroll(decision.tiger_id, str(emb.id), db, is_confirmed=True)

                # Create Observation record with enriched metadata
                if hasattr(image, "station_id") and image.station_id:
                    obs = Observation(
                        tiger_id=uuid.UUID(decision.tiger_id),
                        station_id=image.station_id,
                        image_id=image.id,
                        identity_confidence=decision.metadata.get("top_sim", 0.99) if decision.metadata else 0.99,
                        identity_method="AUTO",
                        captured_at=image.captured_at,
                    )
                    # Store multi-factor scores in observation (Item #18)
                    if decision.metadata:
                        if hasattr(obs, "global_similarity"):
                            obs.global_similarity = decision.metadata.get("top_sim")
                        if hasattr(obs, "calibrated_confidence"):
                            obs.calibrated_confidence = decision.metadata.get("calibrated_confidence")
                        if hasattr(obs, "matching_parts"):
                            obs.matching_parts = decision.metadata.get("matching_parts")
                    db.add(obs)
                auto_matched += 1

            elif decision.action == "NEW_TIGER":
                # Create provisional new identity (Item #12 — open-set)
                new_tid = enroll(None, str(emb.id), db, is_confirmed=False)
                # Mark as novel detection
                if hasattr(image, "station_id") and image.station_id:
                    obs = Observation(
                        tiger_id=uuid.UUID(new_tid),
                        station_id=image.station_id,
                        image_id=image.id,
                        identity_confidence=decision.metadata.get("top_sim", 0.0) if decision.metadata else 0.0,
                        identity_method="AUTO",
                        captured_at=image.captured_at,
                    )
                    if hasattr(obs, "is_novel_detection"):
                        obs.is_novel_detection = True
                    db.add(obs)
                new_tigers += 1
            else:
                for_review += 1
                review = Review(
                    image_id=image.id,
                    detection_id=emb.flank.detection_id if hasattr(emb, "flank") and emb.flank else None,
                    flank_id=emb.flank_id,
                    state="PENDING",
                    similarity_score=decision.metadata.get("top_sim") if decision.metadata else None,
                    candidates=decision.metadata if decision.metadata else [],
                )
                db.add(review)

        # Update run stats
        run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
        if run:
            run.auto_matched = auto_matched
            run.new_tigers = new_tigers
            run.for_review += for_review

            from app.models.run import RunStatus
            from datetime import datetime, timezone
            run.status = RunStatus.COMPLETE
            run.completed_at = datetime.now(timezone.utc)

        db.commit()
        logger.info(
            f"Re-ID for run {run_id}: {auto_matched} auto, {new_tigers} new, "
            f"{for_review} review, {sift_verified} SIFT verified"
        )
        return {
            "run_id": run_id,
            "auto_matched": auto_matched,
            "new_tigers": new_tigers,
            "for_review": for_review,
            "sift_verified": sift_verified,
        }
    finally:
        db.close()

