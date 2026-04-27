from typing import Optional
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Complaint, Upvote, Escalation
from app.auth import get_current_user
from app.clustering import run_clustering
from app.templating import render, flash
from app.cloudinary_helper import upload_image, CLOUDINARY_ENABLED

router = APIRouter()


def image_url(image_filename: Optional[str]) -> Optional[str]:
    """
    Build the correct image URL depending on storage backend.
    - Cloudinary: image_filename IS already a full https:// URL
    - Local:      image_filename is just 'abc123.jpg', prefix /uploads/
    """
    if not image_filename:
        return None
    if CLOUDINARY_ENABLED or image_filename.startswith("http"):
        return image_filename
    return f"/uploads/{image_filename}"


@router.get("/report")
def report_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        flash(request, "Please log in to report an issue.", "error")
        return RedirectResponse("/login", status_code=302)
    return render(request, "complaints/report.html")


@router.post("/report")
async def report_post(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form("Other"),
    latitude: str = Form(...),
    longitude: str = Form(...),
    address: str = Form(""),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    if not title.strip() or not description.strip() or not latitude or not longitude:
        flash(request, "Title, description, and location are required.", "error")
        return RedirectResponse("/report", status_code=302)

    # Upload image via Cloudinary or local storage
    image_filename = await upload_image(image)

    complaint = Complaint(
        user_id=user.id,
        title=title.strip(),
        description=description.strip(),
        category=category,
        image_filename=image_filename,
        latitude=float(latitude),
        longitude=float(longitude),
        address=address.strip(),
        status="Pending",
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    complaint.calculate_pressure_score()
    db.commit()
    run_clustering(db)

    flash(request, "Complaint submitted successfully!", "success")
    return RedirectResponse("/dashboard", status_code=302)


@router.get("/complaint/{complaint_id}")
def detail(request: Request, complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        return RedirectResponse("/", status_code=302)
    user = get_current_user(request, db)
    user_upvoted = False
    if user:
        user_upvoted = (
            db.query(Upvote)
            .filter(Upvote.user_id == user.id, Upvote.complaint_id == complaint_id)
            .first()
        ) is not None
    return render(request, "complaints/detail.html", dict(
        complaint=complaint,
        user_upvoted=user_upvoted,
        image_url=image_url(complaint.image_filename),
    ))


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        flash(request, "Please log in to view your dashboard.", "error")
        return RedirectResponse("/login", status_code=302)
    user_complaints = (
        db.query(Complaint)
        .filter(Complaint.user_id == user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    # Attach resolved image URLs to each complaint for the template
    for c in user_complaints:
        c._image_url = image_url(c.image_filename)
    return render(request, "complaints/dashboard.html", dict(
        complaints=user_complaints,
        image_url_fn=image_url,
    ))


@router.post("/upvote/{complaint_id}")
def upvote(request: Request, complaint_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        flash(request, "Please log in to upvote.", "error")
        return RedirectResponse("/login", status_code=302)

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        return RedirectResponse("/", status_code=302)

    existing = (
        db.query(Upvote)
        .filter(Upvote.user_id == user.id, Upvote.complaint_id == complaint_id)
        .first()
    )
    if existing:
        db.delete(existing)
        flash(request, "Upvote removed.", "info")
    else:
        db.add(Upvote(user_id=user.id, complaint_id=complaint_id))
        flash(request, "Upvote added!", "success")

    db.commit()
    complaint.calculate_pressure_score()
    db.commit()
    return RedirectResponse(f"/complaint/{complaint_id}", status_code=302)


@router.post("/escalate/{complaint_id}")
def escalate(
    request: Request,
    complaint_id: int,
    reason: str = Form(...),
    level: str = Form("Ward Officer"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        return RedirectResponse("/", status_code=302)

    if not reason.strip():
        flash(request, "Escalation reason is required.", "error")
        return RedirectResponse(f"/complaint/{complaint_id}", status_code=302)

    db.add(Escalation(
        complaint_id=complaint_id,
        escalated_by=user.id,
        reason=reason.strip(),
        level=level,
    ))
    db.commit()
    flash(request, f"Issue escalated to {level}.", "success")
    return RedirectResponse(f"/complaint/{complaint_id}", status_code=302)
