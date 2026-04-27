from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, get_current_user
from app.templating import render, flash

router = APIRouter()


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return RedirectResponse("/", status_code=302)
    return render(request, "auth/login.html")


@router.post("/login")
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.strip()).first()
    if user and verify_password(password, user.password):
        request.session["user_id"] = user.id
        flash(request, f"Welcome back, {user.name}!", "success")
        return RedirectResponse("/", status_code=302)
    flash(request, "Invalid email or password.", "error")
    return RedirectResponse("/login", status_code=302)


@router.get("/register")
def register_page(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return RedirectResponse("/", status_code=302)
    return render(request, "auth/register.html")


@router.post("/register")
def register_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    name = name.strip()
    email = email.strip()

    if not all([name, email, password]):
        flash(request, "All fields are required.", "error")
        return RedirectResponse("/register", status_code=302)
    if password != confirm_password:
        flash(request, "Passwords do not match.", "error")
        return RedirectResponse("/register", status_code=302)
    if db.query(User).filter(User.email == email).first():
        flash(request, "Email already registered.", "error")
        return RedirectResponse("/register", status_code=302)

    user = User(name=name, email=email, password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    flash(request, "Account created successfully!", "success")
    return RedirectResponse("/", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "You have been logged out.", "info")
    return RedirectResponse("/login", status_code=302)
