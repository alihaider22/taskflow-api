from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

app = FastAPI(title="TaskFlow API", description="A simple task manager API", version="1.0.0")


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
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


# empty tasks list
tasks: List[Task] = []

def find_task_by_id(task_id: UUID) -> Optional[Task]:
    for task in tasks:
        if task.id == task_id:
            return task
    return None


@app.get("/")
async def root():
    return {"message": "Welcome to TaskFlow API!", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


@app.get("/api/v1/tasks/", response_model=List[Task])
def get_all_tasks():
    return tasks


@app.post("/api/v1/tasks/", response_model=Task)
def create_task(task_data: TaskCreate):
    
    new_task = Task(
        id=uuid4(),
        title=task_data.title,
        description=task_data.description,
        is_completed=False,
        created_at = datetime.now(),
        updated_at = datetime.now()
    )
    tasks.append(new_task)
    return new_task


@app.get("/api/v1/tasks/{task_id}", response_model=Task)
def get_task(task_id: UUID):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return task


@app.put("/api/v1/tasks/{task_id}", response_model=Task)
def update_task(task_id: UUID, task_data: TaskUpdate):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.is_completed is not None:
        task.is_completed = task_data.is_completed
    
    task.updated_at = datetime.now()
    
    return task


@app.delete("/api/v1/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    tasks.remove(task)
    return None


