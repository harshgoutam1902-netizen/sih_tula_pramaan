"""
Database configuration and session management.
DEMO PROTOTYPE: Uses SQLite instead of PostgreSQL
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment - defaults to SQLite for demo
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tulapramaan_demo.db")

# Create engine with SQLite-specific configuration
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    # SQLite-specific settings
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    poolclass=StaticPool if DATABASE_URL.startswith("sqlite") else None
)

# Enable foreign keys for SQLite
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes to get database session.
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables - USE WITH CAUTION."""
    Base.metadata.drop_all(bind=engine)
