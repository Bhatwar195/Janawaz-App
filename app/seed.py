from app.database import SessionLocal
from app.models import User
from app.auth import hash_password


def seed_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@janawaz.com").first()
        if not existing:
            admin = User(
                name="Admin",
                email="admin@janawaz.com",
                password=hash_password("admin123"),
                is_admin=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
