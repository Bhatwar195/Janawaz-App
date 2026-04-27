import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# Load .env file when running locally (ignored on Render where vars are set directly)
load_dotenv()

# On Render/Neon this is a full postgresql:// URL set via environment variable.
# Locally, if DATABASE_URL is not set, fall back to SQLite so development still works.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    # Local development fallback — SQLite
    BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "janawaz.db")
    print("[INFO] DATABASE_URL not set — using local SQLite (janawaz.db)")
elif DATABASE_URL.startswith("postgres://"):
    # Neon and older Heroku-style URLs use postgres:// but SQLAlchemy 2.x requires postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False; PostgreSQL does not but the arg is ignored safely
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
