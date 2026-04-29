# memory/memory_manager.py
from db.database import SessionLocal, Base, engine
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

class UserMemory(Base):
    __tablename__ = 'user_memory'
    id          = Column(Integer, primary_key=True)
    employee_id = Column(Integer, index=True)
    key         = Column(String)
    value       = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)

# Create table if not exists
Base.metadata.create_all(bind=engine)

def save_memory(employee_id: int, key: str, value: str):
    db = SessionLocal()
    try:
        # Update if exists, insert if not
        existing = db.query(UserMemory).filter(
            UserMemory.employee_id == employee_id,
            UserMemory.key == key
        ).first()
        if existing:
            existing.value = value
        else:
            db.add(UserMemory(employee_id=employee_id, key=key, value=value))
        db.commit()
    finally:
        db.close()

def get_memory(employee_id: int) -> dict:
    db = SessionLocal()
    try:
        records = db.query(UserMemory).filter(
            UserMemory.employee_id == employee_id
        ).all()
        return {r.key: r.value for r in records}
    finally:
        db.close()