import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Load .env for local development (no-op on Render)
load_dotenv()

from app.database import engine, Base
from app.routers import auth, main, complaints, admin, api
from app.seed import seed_admin

# Build all tables before the first request
Base.metadata.create_all(bind=engine)

# Secret key from environment — required in production
SECRET_KEY = os.getenv("SECRET_KEY", "janawaz-local-dev-secret-change-in-production")
if SECRET_KEY == "janawaz-local-dev-secret-change-in-production":
    print("[WARNING] SECRET_KEY is using the default value. Set SECRET_KEY env var in production.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_admin()
    yield


app = FastAPI(
    title="Janawaz – Your City, Your Voice",
    description="Hyperlocal civic issue reporting platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=86400,  # Session expires after 24 hours
)

# Static files (CSS, JS) — always served locally
STATIC_DIR = os.path.join(os.path.dirname(__file__), "app", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Only mount local uploads if using SQLite/local storage (not Cloudinary)
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
if not os.getenv("CLOUDINARY_CLOUD_NAME"):
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(main.router)
app.include_router(complaints.router)
app.include_router(admin.router)
app.include_router(api.router)
