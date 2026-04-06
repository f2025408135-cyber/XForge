from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Task Schemas ---
class TaskBase(BaseModel):
    attack_type: str

class TaskCreate(TaskBase):
    target_id: int

class Task(TaskBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Target Schemas ---
class TargetBase(BaseModel):
    domain: str

class TargetCreate(TargetBase):
    pass

class Target(TargetBase):
    id: int
    is_active: bool
    created_at: datetime
    tasks: List[Task] = []

    class Config:
        from_attributes = True
