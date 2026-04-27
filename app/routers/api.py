from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Complaint, Cluster, Upvote
from app.auth import get_current_user

router = APIRouter(prefix="/api")


@router.get("/issues")
def get_issues(db: Session = Depends(get_db)):
    return [c.to_dict() for c in db.query(Complaint).all()]


@router.get("/clusters")
def get_clusters(db: Session = Depends(get_db)):
    return [c.to_dict() for c in db.query(Cluster).all()]


class ReportPayload(BaseModel):
    title: str
    description: str
    latitude: float
    longitude: float
    category: Optional[str] = "Other"
    address: Optional[str] = ""


@router.post("/report")
def report_api(
    payload: ReportPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    complaint = Complaint(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address=payload.address,
        status="Pending",
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return {"message": "Complaint submitted", "id": complaint.id}


class UpvotePayload(BaseModel):
    complaint_id: int


@router.post("/upvote")
def upvote_api(
    payload: UpvotePayload,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    existing = db.query(Upvote).filter(
        Upvote.user_id == user.id,
        Upvote.complaint_id == payload.complaint_id,
    ).first()
    if existing:
        db.delete(existing)
        action = "removed"
    else:
        db.add(Upvote(user_id=user.id, complaint_id=payload.complaint_id))
        action = "added"
    db.commit()
    complaint.calculate_pressure_score()
    db.commit()
    return {"action": action, "upvotes": complaint.upvote_count()}


class StatusPayload(BaseModel):
    complaint_id: int
    status: str


@router.put("/status")
def update_status_api(
    payload: StatusPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    if payload.status not in ["Pending", "In Progress", "Resolved"]:
        raise HTTPException(status_code=400, detail="Invalid status value")
    complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    complaint.status = payload.status
    db.commit()
    return {"message": "Status updated", "status": payload.status}
