from fastapi import APIRouter, HTTPException

from .schemas import AIAdviceRequest, AIConfigUpdate, ApiResponse, CollectionCreate, CollectionUpdate, FocusStartRequest, StatsInterruptRequest, StatsRecordRequest, TodoCreate, TodoUpdate
from .services import service

router = APIRouter(prefix="/api")


@router.get("/todos", response_model=ApiResponse)
def list_todos():
    return ApiResponse(data=service.list_todos())


@router.post("/todos", response_model=ApiResponse)
def create_todo(payload: TodoCreate):
    todo = service.create_todo(payload)
    return ApiResponse(data=todo)


@router.patch("/todos/{todo_id}/toggle", response_model=ApiResponse)
def toggle_todo(todo_id: int):
    todo = service.toggle_todo(todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="todo not found")
    return ApiResponse(data=todo)


@router.put("/todos/{todo_id}", response_model=ApiResponse)
def update_todo(todo_id: int, payload: TodoUpdate):
    todo = service.update_todo(todo_id, payload)
    if todo is None:
        raise HTTPException(status_code=404, detail="todo not found")
    return ApiResponse(data=todo)


@router.delete("/todos/{todo_id}", response_model=ApiResponse)
def delete_todo(todo_id: int):
    deleted = service.delete_todo(todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="todo not found")
    return ApiResponse(data={"deleted": True})


@router.get("/collections", response_model=ApiResponse)
def list_collections():
    return ApiResponse(data=service.list_collections())


@router.post("/collections", response_model=ApiResponse)
def create_collection(payload: CollectionCreate):
    collection = service.create_collection(payload)
    return ApiResponse(data=collection)


@router.put("/collections/{collection_id}", response_model=ApiResponse)
def update_collection(collection_id: int, payload: CollectionUpdate):
    collection = service.update_collection(collection_id, payload)
    if collection is None:
        raise HTTPException(status_code=404, detail="collection not found")
    return ApiResponse(data=collection)


@router.delete("/collections/{collection_id}", response_model=ApiResponse)
def delete_collection(collection_id: int):
    deleted = service.delete_collection(collection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="collection not found")
    return ApiResponse(data={"deleted": True})


@router.get("/focus/status", response_model=ApiResponse)
def focus_status():
    return ApiResponse(data=service.focus_status())


@router.post("/focus/start", response_model=ApiResponse)
def start_focus(payload: FocusStartRequest):
    return ApiResponse(data=service.start_focus(payload))


@router.post("/focus/stop", response_model=ApiResponse)
def stop_focus():
    return ApiResponse(data=service.stop_focus())


@router.get("/stats", response_model=ApiResponse)
def get_stats(days: int | None = None):
    normalized_days = None
    if days is not None and days > 0:
        normalized_days = days
    return ApiResponse(data=service.get_stats(normalized_days))


@router.post("/stats/record", response_model=ApiResponse)
def record_stats(payload: StatsRecordRequest):
    return ApiResponse(data=service.record_pomodoro_with_detail(payload.duration_minutes, payload.todo_id, payload.todo_title))


@router.post("/stats/interrupt", response_model=ApiResponse)
def record_interrupt(payload: StatsInterruptRequest):
    return ApiResponse(data=service.record_interrupt(payload.duration_minutes, payload.todo_id, payload.todo_title))


@router.get("/me", response_model=ApiResponse)
def get_me():
    return ApiResponse(data=service.get_me())


@router.get("/ai/config", response_model=ApiResponse)
def get_ai_config():
    return ApiResponse(data=service.get_ai_config())


@router.put("/ai/config", response_model=ApiResponse)
def save_ai_config(payload: AIConfigUpdate):
    return ApiResponse(data=service.save_ai_config(payload))


@router.post("/ai/advice", response_model=ApiResponse)
def generate_ai_advice(payload: AIAdviceRequest):
    return ApiResponse(data=service.generate_ai_advice(payload.days, payload.prompt))
