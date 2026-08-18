"""Embedding generation task with multi-part body feature extraction.

Upgraded pipeline:
1. Extract multi-part embeddings (global + head + flank + hind)
2. Extract stripe features from aligned flank crop
3. Fuse into 512-D vector for pgvector search
4. Store all part embeddings for re-ranking stage

Falls back to dual-branch (ConvNeXt + Gabor) if multi-part extraction fails.
"""
import logging
import uuid
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.embedding.generate_embeddings", queue="reid")
def generate_embeddings(run_id: str) -> dict:
    """Generate multi-part visual embeddings for tiger flanks."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.flank import Flank
    from app.models.detection import Detection
    from app.models.image import Image
    from app.models.embedding import Embedding

    db = get_worker_db()
    try:
        flanks = (
            db.query(Flank)
            .join(Detection)
            .join(Image)
            .filter(Image.run_id == uuid.UUID(run_id))
            .all()
        )

        embeddings_created = 0
        multipart_count = 0

        # Try to load the multi-part extractor first
        use_multipart = False
        try:
            from ml.reid.embedding import extract_multipart_embedding
            use_multipart = True
        except ImportError:
            logger.info("Multi-part extractor unavailable, using dual-branch fallback")

        # Fallback to standard dual-branch
        try:
            from ml.reid.embedding import extract_embedding
        except ImportError:
            logger.warning("Re-ID encoder not available")
            return {"run_id": run_id, "embeddings_created": 0, "message": "Encoder unavailable"}

        for flank in flanks:
            detection = flank.detection
            image = detection.image if detection else None
            if not image or not image.storage_uri:
                continue

            try:
                # Get quality scores from Flank model
                qs = {
                    "blur": flank.blur_score if flank.blur_score is not None else 1.0,
                    "exposure": flank.exposure_score if flank.exposure_score is not None else 1.0,
                    "occlusion": flank.occlusion_score if flank.occlusion_score is not None else 0.0,
                }

                quality_weight = qs["blur"] * qs["exposure"] * (1.0 - qs["occlusion"])

                # --- Multi-part extraction (Items #2, #3, #4, #17) ---
                head_emb = None
                flank_emb = None
                hind_emb = None
                visible_parts = None
                pose_confidence = None
                stripe_quality = None

                if use_multipart:
                    try:
                        bbox = tuple(int(v) for v in detection.bbox[:4]) if detection.bbox else None
                        mp_result = extract_multipart_embedding(
                            image.storage_uri,
                            bbox=bbox,
                            quality_scores=qs,
                        )
                        fused_embedding = mp_result.fused_embedding
                        head_emb = mp_result.head_embedding
                        flank_emb = mp_result.flank_embedding
                        hind_emb = mp_result.hind_embedding
                        visible_parts = mp_result.visible_parts
                        pose_confidence = mp_result.pose_confidence
                        stripe_quality = (
                            mp_result.quality_scores.get("stripe_quality")
                            if mp_result.quality_scores else None
                        )
                        model_version = mp_result.model_version
                        multipart_count += 1
                    except Exception as e:
                        logger.debug(f"Multi-part extraction failed for flank {flank.id}: {e}. Using dual-branch.")
                        result = extract_embedding(image.storage_uri, quality_scores=qs)
                        fused_embedding = result["embedding"]
                        model_version = result["model_version"]
                        stripe_quality = result.get("stripe_quality")
                else:
                    # Standard dual-branch extraction
                    result = extract_embedding(image.storage_uri, quality_scores=qs)
                    fused_embedding = result["embedding"]
                    model_version = result["model_version"]
                    stripe_quality = result.get("stripe_quality")

                # Create embedding record with multi-part data
                embedding = Embedding(
                    flank_id=flank.id,
                    vector=fused_embedding,
                    model_version=model_version,
                    side=flank.side,
                    quality_weight=quality_weight,
                    head_embedding=head_emb,
                    flank_embedding=flank_emb,
                    hind_embedding=hind_emb,
                    visible_parts=visible_parts,
                    pose_confidence=pose_confidence,
                    stripe_quality=stripe_quality,
                )
                db.add(embedding)
                embeddings_created += 1
            except Exception as e:
                logger.warning(f"Embedding failed for flank {flank.id}: {e}")

        db.commit()
        logger.info(
            f"Generated {embeddings_created} embeddings for run {run_id} "
            f"(multi-part: {multipart_count})"
        )

        # Chain to next step
        if embeddings_created > 0:
            from workers.tasks.reid import identify_tigers
            identify_tigers.delay(run_id)
        else:
            from app.models.run import Run, RunStatus
            from datetime import datetime, timezone
            run = db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
            if run:
                run.status = RunStatus.COMPLETE
                run.completed_at = datetime.now(timezone.utc)
                db.commit()

        return {
            "run_id": run_id,
            "embeddings_created": embeddings_created,
            "multipart_count": multipart_count,
        }
    finally:
        db.close()

