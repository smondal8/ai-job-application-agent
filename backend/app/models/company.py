from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Company(Base, TimestampMixin):
    """Normalized Company Registry Record."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    normalized_name = Column(String(255), nullable=False, unique=True, index=True)
    domain = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)
    careers_url = Column(String(1024), nullable=True)
    location_headquarters = Column(String(255), nullable=True)

    # Relationships
    jobs = relationship("Job", back_populates="company_rel", cascade="all, delete-orphan")
