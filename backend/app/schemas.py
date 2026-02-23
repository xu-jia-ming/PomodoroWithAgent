from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: object | None = None


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    estimated_pomodoros: int = Field(ge=1, le=20)
    timer_mode: str = Field(default="countdown")
    focus_minutes: int = Field(default=25, ge=1, le=180)
    collection_id: Optional[int] = None


class TodoUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    estimated_pomodoros: int = Field(ge=1, le=20)
    timer_mode: str = Field(default="countdown")
    focus_minutes: int = Field(default=25, ge=1, le=180)
    collection_id: Optional[int] = None


class TodoItem(BaseModel):
    id: int
    title: str
    estimated_pomodoros: int
    timer_mode: str = "countdown"
    focus_minutes: int = 25
    completed: bool
    completed_count: int = 0
    collection_id: Optional[int] = None


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CollectionUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CollectionItem(BaseModel):
    id: int
    name: str
    todo_count: int


class FocusStartRequest(BaseModel):
    duration_minutes: int = Field(ge=1, le=180)


class FocusStatus(BaseModel):
    active: bool
    duration_minutes: int
    end_time: Optional[datetime] = None


class StatsItem(BaseModel):
    today_pomodoros: int
    week_pomodoros: int
    total_focus_minutes: int


class StatsRecordRequest(BaseModel):
    duration_minutes: int = Field(ge=1, le=180)
    todo_id: Optional[int] = None
    todo_title: Optional[str] = None


class StatsInterruptRequest(BaseModel):
    duration_minutes: int = Field(ge=0, le=180)
    todo_id: Optional[int] = None
    todo_title: Optional[str] = None


class UserInfo(BaseModel):
    id: int
    nickname: str
