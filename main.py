from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

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

@app.post("/tasks/", response_model=Task)
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

