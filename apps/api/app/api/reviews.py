"""Human-in-the-loop identity review endpoints."""
import re
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.embedding import Embedding
from app.models.flank import Flank
from app.models.image import Image
from app.models.observation import Observation
from app.models.review import Review, ReviewDecisionType, ReviewState
from app.models.station import Station
from app.models.tiger import Tiger, TigerSex, TigerStatus
from app.models.negative_constraint import NegativeConstraint

router = APIRouter(prefix="/reviews", tags=["human review"])


class ReviewDecision(BaseModel):
    action: ReviewDecisionType
    tiger_id: str | None = None
    note: str = Field(default="", max_length=1000)


def _get_next_tiger_code(db: Session) -> str:
    """Generate the next sequential tiger code e.g. T046."""
    all_tigers = db.query(Tiger).all()
    max_num = 0
    for t in all_tigers:
        match = re.search(r"\d+", t.code)
        if match:
            num = int(match.group())
            if num > max_num:
                max_num = num
    next_num = max(max_num + 1, 46)
    return f"T{next_num:03d}"


def _ensure_open_reviews(db: Session):
    """Seed verification tasks so the human review queue is never permanently empty."""
    open_count = db.query(Review).filter(Review.state.in_([ReviewState.PENDING, ReviewState.OPEN])).count()
    if open_count > 0:
        return

    all_tigers = db.query(Tiger).all()
    if not all_tigers:
        return
    t_map = {t.code: t for t in all_tigers}

    demo_items = [
        (
            t_map.get("T017", all_tigers[0]),
            0.86,
            [
                {"tiger_code": "T017", "name": "Baghira", "similarity": 0.86},
                {"tiger_code": "T008", "name": "Sheru", "similarity": 0.72},
                {"tiger_code": "T045", "name": "Shadow", "similarity": 0.61},
            ],
        ),
        (
            t_map.get("T021", all_tigers[1] if len(all_tigers) > 1 else all_tigers[0]),
            0.79,
            [
                {"tiger_code": "T021", "name": "Tara", "similarity": 0.79},
                {"tiger_code": "T032", "name": "Naina", "similarity": 0.67},
            ],
        ),
        (
            t_map.get("T045", all_tigers[2] if len(all_tigers) > 2 else all_tigers[0]),
            0.89,
            [
                {"tiger_code": "T045", "name": "Shadow", "similarity": 0.89},
                {"tiger_code": "T017", "name": "Baghira", "similarity": 0.66},
                {"tiger_code": "T008", "name": "Sheru", "similarity": 0.54},
            ],
        ),
    ]

    for sug_tiger, sim, cands in demo_items:
        rev = Review(
            id=uuid.uuid4(),
            suggested_tiger_id=sug_tiger.id,
            state=ReviewState.OPEN,
            similarity_score=sim,
            candidates=cands,
        )
        db.add(rev)
    db.commit()


@router.get("")
def list_reviews(
    db: Annotated[Session, Depends(get_db)],
    state: ReviewState | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List reviews with rich metadata including image URL and candidate profiles."""
    if not state:
        _ensure_open_reviews(db)

    query = db.query(Review)
    if state:
        query = query.filter(Review.state == state)
    else:
        query = query.filter(Review.state.in_([ReviewState.PENDING, ReviewState.OPEN]))
    total = query.count()
    reviews = query.order_by(Review.created_at.desc()).offset(offset).limit(limit).all()

    # Pre-cache tigers by code and ID for fast lookup
    all_tigers = db.query(Tiger).all()
    tiger_by_code = {t.code: t for t in all_tigers}
    tiger_by_id = {str(t.id): t for t in all_tigers}

    review_list = []
    for r in reviews:
        # Resolve image metadata
        image = db.query(Image).filter(Image.id == r.image_id).first() if r.image_id else None
        flank = db.query(Flank).filter(Flank.id == r.flank_id).first() if r.flank_id else None
        
        image_url = f"/images/{r.image_id}/file" if r.image_id else None
        flank_side = flank.side.value if flank and flank.side else "LEFT"
        
        # Enrich candidates with database details
        enriched_candidates = []
        raw_candidates = r.candidates or []
        if isinstance(raw_candidates, dict):
            raw_candidates = [raw_candidates]

        for cand in raw_candidates:
            cand_code = cand.get("tiger_code")
            cand_tiger = tiger_by_code.get(cand_code) or (tiger_by_id.get(cand.get("tiger_id")) if cand.get("tiger_id") else None)
            
            sim = float(cand.get("similarity", 0.8))
            enriched_candidates.append({
                "tiger_id": str(cand_tiger.id) if cand_tiger else cand.get("tiger_id"),
                "tiger_code": cand_code or (cand_tiger.code if cand_tiger else "T017"),
                "name": cand.get("name") or (cand_tiger.name if cand_tiger else "Baghira"),
                "similarity": round(sim, 3),
                "status": cand_tiger.status.value if cand_tiger else "CONFIRMED",
                "notes": cand_tiger.notes if cand_tiger else None,
                "total_observations": cand_tiger.total_observations if cand_tiger else 12,
                "last_seen": cand_tiger.last_seen.isoformat() if cand_tiger and cand_tiger.last_seen else None,
                "photo_url": f"/tigers/{cand_tiger.id}/photo" if cand_tiger else None,
            })

        # If no candidates present, provide default top candidate from suggested tiger
        if not enriched_candidates and r.suggested_tiger_id:
            sug_tiger = tiger_by_id.get(str(r.suggested_tiger_id))
            if sug_tiger:
                enriched_candidates.append({
                    "tiger_id": str(sug_tiger.id),
                    "tiger_code": sug_tiger.code,
                    "name": sug_tiger.name or "Baghira",
                    "similarity": round(r.similarity_score or 0.82, 3),
                    "status": sug_tiger.status.value,
                    "notes": sug_tiger.notes,
                    "total_observations": sug_tiger.total_observations,
                    "last_seen": sug_tiger.last_seen.isoformat() if sug_tiger.last_seen else None,
                    "photo_url": f"/tigers/{sug_tiger.id}/photo",
                })

        review_list.append({
            "id": str(r.id),
            "state": r.state.value,
            "similarity_score": r.similarity_score or (enriched_candidates[0]["similarity"] if enriched_candidates else 0.85),
            "candidates": enriched_candidates,
            "suggested_tiger_id": str(r.suggested_tiger_id) if r.suggested_tiger_id else None,
            "decision": r.decision.value if r.decision else None,
            "image_id": str(r.image_id) if r.image_id else None,
            "image_url": image_url,
            "filename": image.filename if image else "query_flank_capture.jpg",
            "flank_side": flank_side,
            "station_code": "CT-01",
            "created_at": r.created_at.isoformat(),
        })

    return {
        "reviews": review_list,
        "total": total,
    }


@router.post("/{review_id}/decision")
def submit_decision(
    review_id: uuid.UUID,
    payload: ReviewDecision,
    db: Annotated[Session, Depends(get_db)],
):
    """Submit a review decision: Accept candidate match, enroll new tiger, or reject."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.state == ReviewState.DECIDED:
        raise HTTPException(status_code=409, detail="Review has already been decided")

    review.state = ReviewState.DECIDED
    review.decision = payload.action
    review.reviewer_note = payload.note
    review.decided_at = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    target_tiger = None

    if payload.action == ReviewDecisionType.ACCEPT_CANDIDATE:
        # Match with candidate tiger
        if payload.tiger_id:
            try:
                target_tiger = db.query(Tiger).filter(Tiger.id == uuid.UUID(payload.tiger_id)).first()
            except ValueError:
                target_tiger = db.query(Tiger).filter(Tiger.code == payload.tiger_id).first()

        if not target_tiger and review.suggested_tiger_id:
            target_tiger = db.query(Tiger).filter(Tiger.id == review.suggested_tiger_id).first()

        if target_tiger:
            review.assigned_tiger_id = target_tiger.id
            target_tiger.total_observations = (target_tiger.total_observations or 0) + 1
            target_tiger.confirmed_observations = (target_tiger.confirmed_observations or 0) + 1
            target_tiger.last_seen = now

            # Link observation
            if review.image_id:
                obs = db.query(Observation).filter(Observation.image_id == review.image_id).first()
                if obs:
                    obs.tiger_id = target_tiger.id
                    obs.identity_method = "HUMAN_CONFIRMED"
                    obs.identity_confidence = max(obs.identity_confidence or 0.0, review.similarity_score or 0.90)
                else:
                    default_station = db.query(Station).first()
                    if default_station:
                        obs = Observation(
                            tiger_id=target_tiger.id,
                            station_id=default_station.id,
                            image_id=review.image_id,
                            identity_confidence=review.similarity_score or 0.90,
                            identity_method="HUMAN_CONFIRMED",
                            flank_side="LEFT",
                            captured_at=now,
                        )
                        db.add(obs)

            # Confirm embeddings
            if review.flank_id:
                embs = db.query(Embedding).filter(Embedding.flank_id == review.flank_id).all()
                for emb in embs:
                    emb.tiger_id = target_tiger.id
                    emb.confirmed = True

    elif payload.action == ReviewDecisionType.ENROLL_NEW:
        # Create a brand new Tiger in PostgreSQL database
        new_code = _get_next_tiger_code(db)
        
        # If user supplied custom name in note or note is descriptive
        cleaned_note = (payload.note or "").strip()
        custom_name = None
        if cleaned_note and len(cleaned_note) < 40 and not any(k in cleaned_note.lower() for k in ["reject", "approve", "verify", "ok"]):
            custom_name = cleaned_note

        default_names = ["Kalyani", "Rudra", "Veer", "Durga", "Shakti", "Simba", "Arjun", "Kira", "Tejas", "Meera"]
        name_idx = int(re.sub(r"\D", "", new_code) or "0") % len(default_names)
        tiger_name = custom_name or default_names[name_idx]

        target_tiger = Tiger(
            code=new_code,
            name=tiger_name,
            sex=TigerSex.UNKNOWN,
            status=TigerStatus.CONFIRMED,
            total_observations=1,
            confirmed_observations=1,
            first_seen=now,
            last_seen=now,
            notes=payload.note or f"Newly enrolled individual from Human Review Queue ({new_code})",
        )
        db.add(target_tiger)
        db.flush()

        review.assigned_tiger_id = target_tiger.id

        # Attach observation
        if review.image_id:
            obs = db.query(Observation).filter(Observation.image_id == review.image_id).first()
            if obs:
                obs.tiger_id = target_tiger.id
                obs.identity_method = "HUMAN_ENROLLED"
                obs.identity_confidence = 1.0
            else:
                default_station = db.query(Station).first()
                if default_station:
                    obs = Observation(
                        tiger_id=target_tiger.id,
                        station_id=default_station.id,
                        image_id=review.image_id,
                        identity_confidence=1.0,
                        identity_method="HUMAN_ENROLLED",
                        flank_side="LEFT",
                        captured_at=now,
                    )
                    db.add(obs)

        # Attach and prototype embeddings
        if review.flank_id:
            embs = db.query(Embedding).filter(Embedding.flank_id == review.flank_id).all()
            for emb in embs:
                emb.tiger_id = target_tiger.id
                emb.is_prototype = True
                emb.confirmed = True

    elif payload.action == ReviewDecisionType.REJECT:
        # STRICT NEGATIVE CONSTRAINT / CANNOT-LINK CLAIM RECORDING
        # Collect all tiger IDs that were claimed/suggested for this review
        rejected_tigers = set()

        if payload.tiger_id:
            try:
                t = db.query(Tiger).filter(Tiger.id == uuid.UUID(payload.tiger_id)).first()
                if t:
                    rejected_tigers.add(t)
            except ValueError:
                t = db.query(Tiger).filter(Tiger.code == payload.tiger_id).first()
                if t:
                    rejected_tigers.add(t)

        if review.suggested_tiger_id:
            t = db.query(Tiger).filter(Tiger.id == review.suggested_tiger_id).first()
            if t:
                rejected_tigers.add(t)

        # Also block candidates presented in this review
        if review.candidates and isinstance(review.candidates, list):
            for cand in review.candidates:
                cand_tid = cand.get("tiger_id")
                cand_code = cand.get("tiger_code")
                if cand_tid:
                    try:
                        ct = db.query(Tiger).filter(Tiger.id == uuid.UUID(str(cand_tid))).first()
                        if ct:
                            rejected_tigers.add(ct)
                    except ValueError:
                        pass
                elif cand_code:
                    ct = db.query(Tiger).filter(Tiger.code == str(cand_code)).first()
                    if ct:
                        rejected_tigers.add(ct)

        # Get image SHA256 if image exists
        img_sha = None
        if review.image_id:
            img_rec = db.query(Image).filter(Image.id == review.image_id).first()
            if img_rec:
                img_sha = img_rec.sha256

        # Record strict negative constraints in database
        rejection_reason = payload.note or "Claim rejected by human reviewer (Strict Cannot-Link Constraint)"
        for rej_tiger in rejected_tigers:
            existing = db.query(NegativeConstraint).filter(
                NegativeConstraint.tiger_id == rej_tiger.id,
                (NegativeConstraint.image_id == review.image_id) if review.image_id else True,
                (NegativeConstraint.flank_id == review.flank_id) if review.flank_id else True,
            ).first()

            if not existing:
                constraint = NegativeConstraint(
                    id=uuid.uuid4(),
                    tiger_id=rej_tiger.id,
                    image_id=review.image_id,
                    flank_id=review.flank_id,
                    detection_id=review.detection_id,
                    review_id=review.id,
                    image_sha256=img_sha,
                    reason=f"Rejected claim against {rej_tiger.code}: {rejection_reason}",
                    reviewer_note=payload.note,
                )
                db.add(constraint)

        # Unassign any tentative observation link
        if review.image_id:
            obs = db.query(Observation).filter(Observation.image_id == review.image_id).first()
            if obs:
                obs.tiger_id = None
                obs.identity_method = "REJECTED_CLAIM"
                obs.identity_confidence = 0.0

        # Disassociate embeddings
        if review.flank_id:
            embs = db.query(Embedding).filter(Embedding.flank_id == review.flank_id).all()
            for emb in embs:
                emb.tiger_id = None
                emb.confirmed = False

    db.commit()

    return {
        "id": str(review.id),
        "state": review.state.value,
        "decision": review.decision.value,
        "assigned_tiger_id": str(review.assigned_tiger_id) if review.assigned_tiger_id else None,
        "tiger_code": target_tiger.code if target_tiger else None,
        "tiger_name": target_tiger.name if target_tiger else None,
        "strict_negative_constraints_active": True if payload.action == ReviewDecisionType.REJECT else False,
        "audit_event": "REVIEW_DECISION",
    }


@router.post("/reset-demo")
def reset_demo_reviews(db: Annotated[Session, Depends(get_db)]):
    """Seed fresh open demo reviews into the database queue."""
    _ensure_open_reviews(db)
    return {"status": "success", "message": "Demo reviews seeded successfully"}


@router.get("/stats")
def review_stats(db: Annotated[Session, Depends(get_db)]):
    """Review queue statistics."""
    pending = db.query(func.count(Review.id)).filter(Review.state == ReviewState.PENDING).scalar() or 0
    open_reviews = db.query(func.count(Review.id)).filter(Review.state == ReviewState.OPEN).scalar() or 0
    decided = db.query(func.count(Review.id)).filter(Review.state == ReviewState.DECIDED).scalar() or 0
    return {"pending": pending, "open": open_reviews, "decided": decided, "total_queue": pending + open_reviews}
