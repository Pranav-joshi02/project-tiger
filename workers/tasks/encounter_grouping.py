"""Encounter grouping task with temporal embedding aggregation.

Groups camera-trap burst images (same station, within 60 seconds) into
single encounters. After grouping, aggregates frame-level embeddings
into robust track embeddings (Item #14).
"""
import logging
import uuid
from datetime import timedelta
from pathlib import Path

from workers.celery_app import celery_app, get_worker_db

logger = logging.getLogger(__name__)

# Default time delta to group images into the same encounter
ENCOUNTER_DELTA_SECONDS = 60

@celery_app.task(name="workers.tasks.encounter_grouping.group_encounters", queue="detection")
def group_encounters(run_id: str) -> dict:
    """Group images into encounters and aggregate embeddings temporally."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
    from app.models.image import Image, ImageState
    from app.models.encounter import Encounter

    db = get_worker_db()
    try:
        # Get all images for this run, sorted by station and time
        images = (
            db.query(Image)
            .filter(Image.run_id == uuid.UUID(run_id), Image.state == ImageState.ACTIVE)
            .order_by(Image.station_id, Image.captured_at)
            .all()
        )

        if not images:
            return {"run_id": run_id, "encounters_created": 0}

        encounters_created = 0
        current_encounter = None
        encounter_images = []  # Track images in current encounter for aggregation

        for image in images:
            if not current_encounter:
                # Start new encounter
                current_encounter = Encounter(
                    run_id=uuid.UUID(run_id),
                    station_id=image.station_id,
                    started_at=image.captured_at,
                    ended_at=image.captured_at,
                    image_count=1,
                    best_image_id=image.id
                )
                db.add(current_encounter)
                encounters_created += 1
                encounter_images = [image]
            else:
                # Check if image belongs to current encounter
                time_diff = (image.captured_at - current_encounter.ended_at).total_seconds()

                if image.station_id == current_encounter.station_id and time_diff <= ENCOUNTER_DELTA_SECONDS:
                    # Update current encounter
                    current_encounter.ended_at = image.captured_at
                    current_encounter.image_count += 1
                    encounter_images.append(image)

                    # Logic to update best_image_id based on quality could go here.
                    # For now, just keep the first or update randomly.
                else:
                    # Aggregate embeddings for the completed encounter (Item #14)
                    _aggregate_encounter_embeddings(db, current_encounter, encounter_images)

                    # Start new encounter
                    current_encounter = Encounter(
                        run_id=uuid.UUID(run_id),
                        station_id=image.station_id,
                        started_at=image.captured_at,
                        ended_at=image.captured_at,
                        image_count=1,
                        best_image_id=image.id
                    )
                    db.add(current_encounter)
                    encounters_created += 1
                    encounter_images = [image]

        # Aggregate the last encounter
        if current_encounter and encounter_images:
            _aggregate_encounter_embeddings(db, current_encounter, encounter_images)

        db.commit()
        logger.info(f"Grouped {len(images)} images into {encounters_created} encounters for run {run_id}")
        return {"run_id": run_id, "encounters_created": encounters_created}

    finally:
        db.close()


def _aggregate_encounter_embeddings(db, encounter, images):
    """Aggregate frame-level embeddings for an encounter into a track embedding.

    Uses quality-weighted mean aggregation to produce a single robust embedding
    from multiple burst frames, reducing the effect of blurry individual frames.
    """
    if len(images) < 2:
        return  # Single frame — no aggregation needed

    try:
        from app.models.embedding import Embedding
        from app.models.flank import Flank
        from app.models.detection import Detection
        from ml.reid.temporal_aggregation import (
            CameraEventAggregator,
            FrameEmbedding,
            AggregationStrategy,
        )

        # Collect embeddings from all images in this encounter
        frame_embeddings = []
        best_quality = -1.0
        best_image_id = None

        for image in images:
            # Find embeddings associated with this image
            emb_records = (
                db.query(Embedding)
                .join(Flank)
                .join(Detection)
                .filter(Detection.image_id == image.id)
                .all()
            )

            for emb in emb_records:
                quality = emb.quality_weight if emb.quality_weight else 0.5
                vec = emb.vector
                if vec is not None:
                    vec_list = list(vec) if not isinstance(vec, list) else vec
                    frame_embeddings.append(FrameEmbedding(
                        embedding=vec_list,
                        quality_score=quality,
                        timestamp=image.captured_at.isoformat() if image.captured_at else None,
                        frame_index=len(frame_embeddings),
                    ))
                    if quality > best_quality:
                        best_quality = quality
                        best_image_id = image.id

        if len(frame_embeddings) < 2:
            return

        # Aggregate
        aggregator = CameraEventAggregator(strategy=AggregationStrategy.QUALITY_WEIGHTED)
        track = aggregator.aggregate(frame_embeddings)

        # Update encounter with best image and store aggregated embedding
        if best_image_id:
            encounter.best_image_id = best_image_id

        # Create CameraEvent record if the model exists
        try:
            from app.models.camera_event import CameraEvent
            event = CameraEvent(
                station_id=encounter.station_id,
                run_id=encounter.run_id,
                encounter_id=encounter.id,
                start_time=encounter.started_at,
                end_time=encounter.ended_at,
                frame_count=len(frame_embeddings),
                aggregated_embedding=track.aggregated_embedding,
                best_frame_id=best_image_id,
                best_frame_quality=best_quality,
                aggregation_strategy=track.strategy,
                aggregation_confidence=track.aggregation_confidence,
            )
            db.add(event)
        except ImportError:
            logger.debug("CameraEvent model not available — skipping event storage")

        logger.debug(
            f"Aggregated {len(frame_embeddings)} frames for encounter "
            f"(confidence: {track.aggregation_confidence:.3f})"
        )

    except ImportError as e:
        logger.debug(f"Temporal aggregation modules not available: {e}")
    except Exception as e:
        logger.warning(f"Temporal aggregation failed for encounter: {e}")

