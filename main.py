import os
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in environment variables")

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Model
class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="TaskFlow API", description="A simple task manager API", version="1.0.0")

# Pydantic Models
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, description="The title of the task")
    description: Optional[str] = Field(None, max_length=500, description="A brief description of the task")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100, description="The title of the task")
    description: Optional[str] = Field(None, max_length=500, description="A brief description of the task")
    is_completed: Optional[bool] = Field(None, description="Indicates if the task is completed")

class Task(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def get_task_by_id(db: Session, task_id: UUID) -> Optional[TaskModel]:
    return db.query(TaskModel).filter(TaskModel.id == task_id).first()

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to TaskFlow API!", "version": "1.0.0", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/v1/tasks/", response_model=List[Task])
def get_all_tasks(completed: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(TaskModel)
    
    if completed is not None:
        query = query.filter(TaskModel.is_completed == completed)
    
    tasks = query.order_by(TaskModel.created_at.desc()).all()
    return [Task.model_validate(task) for task in tasks]

@app.post("/api/v1/tasks/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    db_task = TaskModel(
        title=task_data.title,
        description=task_data.description,
        is_completed=False
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return Task.model_validate(db_task)

@app.get("/api/v1/tasks/{task_id}", response_model=Task)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return Task.model_validate(task)

@app.put("/api/v1/tasks/{task_id}", response_model=Task)
def update_task(task_id: UUID, task_data: TaskUpdate, db: Session = Depends(get_db)):
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    # Update only provided fields
    update_data = task_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # Update timestamp
    task.updated_at = func.now()
    
    db.commit()
    db.refresh(task)
    
    return Task.model_validate(task)

@app.patch("/api/v1/tasks/{task_id}", response_model=Task)
def toggle_task_status(task_id: UUID, db: Session = Depends(get_db)):
    """Toggle task completion status"""
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    task.is_completed = not task.is_completed
    task.updated_at = func.now()
    
    db.commit()
    db.refresh(task)
    
    return Task.model_validate(task)

@app.delete("/api/v1/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    """Delete a task"""
    task = get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    db.delete(task)
    db.commit()
    return None
