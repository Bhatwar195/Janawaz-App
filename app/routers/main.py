from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Complaint, Cluster
from app.templating import render

router = APIRouter()


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    trending = (
        db.query(Complaint)
        .order_by(Complaint.public_pressure_score.desc())
        .limit(5)
        .all()
    )
    total = db.query(Complaint).count()
    resolved = db.query(Complaint).filter(Complaint.status == "Resolved").count()
    pending = db.query(Complaint).filter(Complaint.status == "Pending").count()
    in_progress = db.query(Complaint).filter(Complaint.status == "In Progress").count()
    clusters = db.query(Cluster).all()

    return render(request, "main/home.html", dict(
        trending=trending,
        total=total,
        resolved=resolved,
        pending=pending,
        in_progress=in_progress,
        clusters=clusters,
    ))


@router.get("/map")
def map_view(request: Request, db: Session = Depends(get_db)):
    complaints = db.query(Complaint).all()
    clusters = db.query(Cluster).all()
    return render(request, "main/map.html", dict(complaints=complaints, clusters=clusters))
