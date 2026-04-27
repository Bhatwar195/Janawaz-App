from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False, index=True)
    password   = Column(String(256), nullable=False)
    is_admin   = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    complaints = relationship("Complaint", back_populates="author")
    upvotes    = relationship("Upvote", back_populates="voter")


class Cluster(Base):
    __tablename__ = "clusters"
    id              = Column(Integer, primary_key=True, index=True)
    center_lat      = Column(Float, nullable=False)
    center_lng      = Column(Float, nullable=False)
    center_address  = Column(String(500), nullable=True)
    score           = Column(Float, default=0.0)
    complaint_count = Column(Integer, default=0)
    created_at      = Column(DateTime, default=datetime.utcnow)
    complaints      = relationship("Complaint", back_populates="cluster")

    def to_dict(self):
        return {
            "id":              self.id,
            "center_lat":      self.center_lat,
            "center_lng":      self.center_lng,
            "center_address":  self.center_address or "",
            "score":           self.score,
            "complaint_count": self.complaint_count,
        }


class Complaint(Base):
    __tablename__ = "complaints"
    id                    = Column(Integer, primary_key=True, index=True)
    user_id               = Column(Integer, ForeignKey("users.id"), nullable=False)
    title                 = Column(String(200), nullable=False)
    description           = Column(Text, nullable=False)
    category              = Column(String(50), nullable=False, default="Other")
    image_filename        = Column(String(512), nullable=True)  # Cloudinary URL or local filename
    latitude              = Column(Float, nullable=False)
    longitude             = Column(Float, nullable=False)
    address               = Column(String(500), nullable=True)
    status                = Column(String(20), default="Pending")
    cluster_id            = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    public_pressure_score = Column(Float, default=0.0)
    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author      = relationship("User", back_populates="complaints")
    cluster     = relationship("Cluster", back_populates="complaints")
    upvotes     = relationship("Upvote", back_populates="complaint", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="complaint", cascade="all, delete-orphan")

    def upvote_count(self):
        return len(self.upvotes)

    def calculate_pressure_score(self):
        upvote_weight = self.upvote_count() * 2
        days_old = max((datetime.utcnow() - self.created_at).days, 0) + 1
        urgency_map = {
            "Pothole":     1.5,
            "Garbage":     1.3,
            "Water Issue": 1.8,
            "Electricity": 1.4,
            "Other":       1.0,
        }
        urgency = urgency_map.get(self.category, 1.0)
        self.public_pressure_score = round((upvote_weight + days_old) * urgency, 2)
        return self.public_pressure_score

    def resolve_image_url(self) -> Optional[str]:
        """Return the correct public URL for the image regardless of storage backend."""
        if not self.image_filename:
            return None
        if self.image_filename.startswith("http"):
            return self.image_filename          # Cloudinary full URL
        return f"/uploads/{self.image_filename}"  # Local dev

    def to_dict(self):
        return {
            "id":             self.id,
            "title":          self.title,
            "description":    self.description,
            "category":       self.category,
            "latitude":       self.latitude,
            "longitude":      self.longitude,
            "address":        self.address or "",
            "status":         self.status,
            "upvotes":        self.upvote_count(),
            "pressure_score": self.public_pressure_score,
            "image":          self.resolve_image_url(),   # Always a usable URL or None
            "created_at":     self.created_at.strftime("%Y-%m-%d %H:%M"),
            "author":         self.author.name if self.author else "Unknown",
            "cluster_id":     self.cluster_id,
        }


class Upvote(Base):
    __tablename__ = "upvotes"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)
    voter        = relationship("User", back_populates="upvotes")
    complaint    = relationship("Complaint", back_populates="upvotes")
    __table_args__ = (UniqueConstraint("user_id", "complaint_id", name="unique_upvote"),)


class Escalation(Base):
    __tablename__ = "escalations"
    id           = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    escalated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason       = Column(Text, nullable=False)
    level        = Column(String(50), default="Ward Officer")
    created_at   = Column(DateTime, default=datetime.utcnow)
    complaint    = relationship("Complaint", back_populates="escalations")
