# db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
 
load_dotenv()
 
# SQLite — stores everything in copilot.db in your project folder
# No server needed! The file is auto-created on first run.
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./copilot.db')
 
# connect_args needed for SQLite only (allows multi-thread access)
engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False}  # SQLite-specific
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
    """Create all tables. Call this once at app startup."""
    from db import models  # import to register models
    Base.metadata.create_all(bind=engine)
    print('SQLite database tables created: copilot.db')
 
