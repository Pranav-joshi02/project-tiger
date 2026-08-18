"""Report generation endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tiger import Tiger

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/tigers.csv")
def tiger_csv(db: Annotated[Session, Depends(get_db)]):
    """Export tiger catalogue as CSV."""
    tigers = db.query(Tiger).order_by(Tiger.code).all()
    header = "tiger_code,name,sex,status,total_observations,first_seen,last_seen"
    rows = [header]
    for t in tigers:
        rows.append(
            f"{t.code},{t.name or ''},{t.sex.value},{t.status.value},"
            f"{t.total_observations},{t.first_seen or ''},{t.last_seen or ''}"
        )
    return Response(
        "\n".join(rows),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tiger-report.csv"},
    )


@router.get("/summary")
def report_summary(db: Annotated[Session, Depends(get_db)]):
    """Generate a summary report."""
    from sqlalchemy import func
    from app.models.image import Image
    from app.models.run import Run
    from app.models.alert import Alert
    from app.models.review import Review

    return {
        "data_notice": "DEMONSTRATION DATA",
        "total_images": db.query(func.count(Image.id)).scalar() or 0,
        "total_tigers": db.query(func.count(Tiger.id)).scalar() or 0,
        "total_runs": db.query(func.count(Run.id)).scalar() or 0,
        "total_alerts": db.query(func.count(Alert.id)).scalar() or 0,
        "total_reviews": db.query(func.count(Review.id)).scalar() or 0,
    }
