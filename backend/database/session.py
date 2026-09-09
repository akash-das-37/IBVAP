import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

# SQLite connection URL
DATABASE_URL = settings.DATABASE_URL

# Ensure directory exists for sqlite file
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from . import models
    Base.metadata.create_all(bind=engine)
