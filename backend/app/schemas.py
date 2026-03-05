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


class AIConfigUpdate(BaseModel):
    provider: str = Field(default="openai_compatible", min_length=1, max_length=64)
    base_url: Optional[str] = Field(default=None, max_length=300)
    model: str = Field(default="gpt-4o-mini", min_length=1, max_length=120)
    temperature: float = Field(default=0.3, ge=0, le=1.5)
    max_tokens: int = Field(default=700, ge=64, le=8192)
    enabled: bool = False
    api_key: Optional[str] = Field(default=None, max_length=500)
    replace_api_key: bool = False
    clear_api_key: bool = False


class AIAdviceRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=180)
    prompt: Optional[str] = Field(default=None, max_length=1000)


class PlanSegmentInput(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    start: str = Field(min_length=1, max_length=5)
    end: str = Field(min_length=1, max_length=5)
    task: str = Field(min_length=1, max_length=200)


class AIPlanOptimizeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    segments: list[PlanSegmentInput] = Field(default_factory=list, min_items=1, max_items=80)
    prompt: Optional[str] = Field(default=None, max_length=1000)


class AIPlanGenerateRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=300)
    days: int = Field(default=30, ge=1, le=180)
    prompt: Optional[str] = Field(default=None, max_length=1000)
