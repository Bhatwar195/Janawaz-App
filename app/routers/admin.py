from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Complaint, Cluster
from app.auth import get_current_user
from app.templating import render, flash

router = APIRouter(prefix="/admin")


def guard(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user or not user.is_admin:
        return None
    return user


@router.get("")
@router.get("/")
def panel(request: Request, db: Session = Depends(get_db)):
    user = guard(request, db)
    if not user:
        flash(request, "Admin access required.", "error")
        return RedirectResponse("/", status_code=302)

    complaints = db.query(Complaint).order_by(Complaint.created_at.desc()).all()
    clusters = db.query(Cluster).all()
    total = len(complaints)
    pending = sum(1 for c in complaints if c.status == "Pending")
    in_progress = sum(1 for c in complaints if c.status == "In Progress")
    resolved = sum(1 for c in complaints if c.status == "Resolved")

    return render(request, "admin/panel.html", dict(
        complaints=complaints, clusters=clusters,
        total=total, pending=pending, in_progress=in_progress, resolved=resolved,
    ))


@router.post("/update_status/{complaint_id}")
def update_status(
    request: Request,
    complaint_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    user = guard(request, db)
    if not user:
        return RedirectResponse("/", status_code=302)

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if complaint and status in ["Pending", "In Progress", "Resolved"]:
        complaint.status = status
        db.commit()
        flash(request, f"Status updated to {status}.", "success")
    return RedirectResponse("/admin", status_code=302)


@router.post("/delete/{complaint_id}")
def delete_complaint(
    request: Request,
    complaint_id: int,
    db: Session = Depends(get_db),
):
    user = guard(request, db)
    if not user:
        return RedirectResponse("/", status_code=302)

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if complaint:
        db.delete(complaint)
        db.commit()
        flash(request, "Complaint deleted.", "info")
    return RedirectResponse("/admin", status_code=302)
