from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

# Database URL - SQLite for simplicity (can be changed to PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./academic_recommender.db")

# Create engine
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import Base from models
from models import Base

# Create all tables
Base.metadata.create_all(bind=engine)
