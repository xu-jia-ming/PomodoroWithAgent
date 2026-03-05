import sqlite3
import os
import sys
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .agent import PomodoroAdvisorAgent
from .schemas import AIConfigUpdate, CollectionCreate, CollectionUpdate, FocusStartRequest, PlanSegmentInput, TodoCreate, TodoUpdate


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class SQLiteService:
    def __init__(self) -> None:
        self.db_path = self._resolve_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _resolve_db_path(self) -> Path:
        explicit_path = os.getenv("POMODORO_DB_PATH")
        if explicit_path:
            return Path(explicit_path).expanduser()

        if getattr(sys, "frozen", False):
            appdata = Path(os.getenv("APPDATA", Path.home()))
            return appdata / "PomodoroTable" / "backend-data" / "pomodoro.db"

        return Path(__file__).resolve().parent.parent / "data" / "pomodoro.db"

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    estimated_pomodoros INTEGER NOT NULL,
                    timer_mode TEXT NOT NULL DEFAULT 'countdown',
                    focus_minutes INTEGER NOT NULL DEFAULT 25,
                    completed INTEGER NOT NULL DEFAULT 0,
                    completed_count INTEGER NOT NULL DEFAULT 0,
                    collection_id INTEGER NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    todo_id INTEGER NULL,
                    todo_title TEXT NULL,
                    status TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS focus_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    active INTEGER NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    end_time TEXT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    nickname TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    provider TEXT NOT NULL DEFAULT 'openai_compatible',
                    base_url TEXT NULL,
                    model TEXT NOT NULL DEFAULT 'gpt-4o-mini',
                    api_key TEXT NULL,
                    temperature REAL NOT NULL DEFAULT 0.3,
                    max_tokens INTEGER NOT NULL DEFAULT 700,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NULL
                )
                """
            )
            conn.execute(
                "INSERT OR IGNORE INTO focus_state (id, active, duration_minutes, end_time) VALUES (1, 0, 0, NULL)"
            )
            conn.execute(
                "INSERT OR IGNORE INTO users (id, nickname) VALUES (1, 'Windows用户')"
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO ai_settings
                (id, provider, base_url, model, api_key, temperature, max_tokens, enabled, updated_at)
                VALUES (1, 'openai_compatible', NULL, 'gpt-4o-mini', NULL, 0.3, 700, 0, NULL)
                """
            )
            todo_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(todos)").fetchall()
            }
            if "completed_count" not in todo_columns:
                conn.execute("ALTER TABLE todos ADD COLUMN completed_count INTEGER NOT NULL DEFAULT 0")
            if "timer_mode" not in todo_columns:
                conn.execute("ALTER TABLE todos ADD COLUMN timer_mode TEXT NOT NULL DEFAULT 'countdown'")
            if "focus_minutes" not in todo_columns:
                conn.execute("ALTER TABLE todos ADD COLUMN focus_minutes INTEGER NOT NULL DEFAULT 25")
            self._seed_demo_data(conn)

    def _seed_demo_data(self, conn) -> None:
        todos_count = conn.execute("SELECT COUNT(*) AS c FROM todos").fetchone()["c"]
        sessions_count = conn.execute("SELECT COUNT(*) AS c FROM sessions").fetchone()["c"]
        if todos_count > 0 or sessions_count > 0:
            return

        conn.execute("INSERT INTO collections (name) VALUES ('学习')")
        study_collection_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        conn.execute("INSERT INTO collections (name) VALUES ('工作')")
        work_collection_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        conn.execute(
            "INSERT INTO todos (title, estimated_pomodoros, timer_mode, focus_minutes, completed, completed_count, collection_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("算法复习", 6, "countdown", 25, 1, 8, study_collection_id),
        )
        todo1 = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        conn.execute(
            "INSERT INTO todos (title, estimated_pomodoros, timer_mode, focus_minutes, completed, completed_count, collection_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("英语听力", 4, "countdown", 30, 1, 5, study_collection_id),
        )
        todo2 = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        conn.execute(
            "INSERT INTO todos (title, estimated_pomodoros, timer_mode, focus_minutes, completed, completed_count, collection_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("日报整理", 3, "countup", 25, 1, 6, work_collection_id),
        )
        todo3 = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        now = _now_utc().replace(minute=0, second=0, microsecond=0)
        todo_map = [
            (todo1, "算法复习"),
            (todo2, "英语听力"),
            (todo3, "日报整理"),
        ]
        session_records = []
        for day_offset in range(6, -1, -1):
            day_time = now - timedelta(days=day_offset)
            completed_times = 1 + (day_offset % 4)
            for index in range(completed_times):
                end_time = day_time + timedelta(hours=9 + index * 2)
                start_time = end_time - timedelta(minutes=25)
                todo_id, todo_title = todo_map[(day_offset + index) % len(todo_map)]
                session_records.append(
                    (
                        start_time.isoformat(),
                        end_time.isoformat(),
                        25,
                        todo_id,
                        todo_title,
                        "completed",
                    )
                )
            if day_offset % 3 == 0:
                interrupt_end = day_time + timedelta(hours=15)
                interrupt_start = interrupt_end - timedelta(minutes=8)
                todo_id, todo_title = todo_map[day_offset % len(todo_map)]
                session_records.append(
                    (
                        interrupt_start.isoformat(),
                        interrupt_end.isoformat(),
                        8,
                        todo_id,
                        todo_title,
                        "interrupted",
                    )
                )

        conn.executemany(
            """
            INSERT INTO sessions (start_time, end_time, duration_minutes, todo_id, todo_title, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            session_records,
        )

    def list_todos(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, title, estimated_pomodoros, timer_mode, focus_minutes, completed, completed_count, collection_id FROM todos ORDER BY id DESC"
            ).fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "estimated_pomodoros": row["estimated_pomodoros"],
                "timer_mode": row["timer_mode"],
                "focus_minutes": row["focus_minutes"],
                "completed": bool(row["completed"]),
                "completed_count": row["completed_count"],
                "collection_id": row["collection_id"],
            }
            for row in rows
        ]

    def create_todo(self, payload: TodoCreate) -> dict:
        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO todos (title, estimated_pomodoros, timer_mode, focus_minutes, completed, completed_count, collection_id) VALUES (?, ?, ?, ?, 0, 0, ?)",
                (payload.title, payload.estimated_pomodoros, payload.timer_mode, payload.focus_minutes, payload.collection_id),
            )
            todo_id = cursor.lastrowid
            row = conn.execute(
                "SELECT id, title, estimated_pomodoros, timer_mode, focus_minutes, completed, completed_count, collection_id FROM todos WHERE id = ?",
                (todo_id,),
            ).fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "estimated_pomodoros": row["estimated_pomodoros"],
            "timer_mode": row["timer_mode"],
            "focus_minutes": row["focus_minutes"],
            "completed": bool(row["completed"]),
            "completed_count": row["completed_count"],
            "collection_id": row["collection_id"],
        }

    def update_todo(self, todo_id: int, payload: TodoUpdate) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT id FROM todos WHERE id = ?", (todo_id,)).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE todos SET title = ?, estimated_pomodoros = ?, timer_mode = ?, focus_minutes = ?, collection_id = ? WHERE id = ?",
                (payload.title, payload.estimated_pomodoros, payload.timer_mode, payload.focus_minutes, payload.collection_id, todo_id),
            )
            updated = conn.execute(
                "SELECT id, title, estimated_pomodoros, timer_mode, focus_minutes, completed, completed_count, collection_id FROM todos WHERE id = ?",
                (todo_id,),
            ).fetchone()
        return {
            "id": updated["id"],
            "title": updated["title"],
            "estimated_pomodoros": updated["estimated_pomodoros"],
            "timer_mode": updated["timer_mode"],
            "focus_minutes": updated["focus_minutes"],
            "completed": bool(updated["completed"]),
            "completed_count": updated["completed_count"],
            "collection_id": updated["collection_id"],
        }

    def delete_todo(self, todo_id: int) -> bool:
        with self._conn() as conn:
            cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        return cursor.rowcount > 0

    def toggle_todo(self, todo_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, title, estimated_pomodoros, timer_mode, focus_minutes, completed, completed_count, collection_id FROM todos WHERE id = ?",
                (todo_id,),
            ).fetchone()
            if row is None:
                return None
            next_completed = 0 if row["completed"] else 1
            conn.execute("UPDATE todos SET completed = ? WHERE id = ?", (next_completed, todo_id))
            updated = conn.execute(
                "SELECT id, title, estimated_pomodoros, timer_mode, focus_minutes, completed, completed_count, collection_id FROM todos WHERE id = ?",
                (todo_id,),
            ).fetchone()
        return {
            "id": updated["id"],
            "title": updated["title"],
            "estimated_pomodoros": updated["estimated_pomodoros"],
            "timer_mode": updated["timer_mode"],
            "focus_minutes": updated["focus_minutes"],
            "completed": bool(updated["completed"]),
            "completed_count": updated["completed_count"],
            "collection_id": updated["collection_id"],
        }

    def list_collections(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT c.id, c.name, COUNT(t.id) AS todo_count
                FROM collections c
                LEFT JOIN todos t ON t.collection_id = c.id
                GROUP BY c.id, c.name
                ORDER BY c.id DESC
                """
            ).fetchall()
        return [{"id": row["id"], "name": row["name"], "todo_count": row["todo_count"]} for row in rows]

    def create_collection(self, payload: CollectionCreate) -> dict:
        with self._conn() as conn:
            cursor = conn.execute("INSERT INTO collections (name) VALUES (?)", (payload.name,))
            collection_id = cursor.lastrowid
        return {"id": collection_id, "name": payload.name, "todo_count": 0}

    def update_collection(self, collection_id: int, payload: CollectionUpdate) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT id FROM collections WHERE id = ?", (collection_id,)).fetchone()
            if row is None:
                return None
            conn.execute("UPDATE collections SET name = ? WHERE id = ?", (payload.name, collection_id))
            todo_count_row = conn.execute(
                "SELECT COUNT(*) AS todo_count FROM todos WHERE collection_id = ?",
                (collection_id,),
            ).fetchone()
        return {"id": collection_id, "name": payload.name, "todo_count": todo_count_row["todo_count"]}

    def delete_collection(self, collection_id: int) -> bool:
        with self._conn() as conn:
            conn.execute("UPDATE todos SET collection_id = NULL WHERE collection_id = ?", (collection_id,))
            cursor = conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        return cursor.rowcount > 0

    def _read_focus(self) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT active, duration_minutes, end_time FROM focus_state WHERE id = 1"
            ).fetchone()
        return {
            "active": bool(row["active"]),
            "duration_minutes": row["duration_minutes"],
            "end_time": row["end_time"],
        }

    def focus_status(self) -> dict:
        focus = self._read_focus()
        if focus["active"] and focus["end_time"]:
            end_time = datetime.fromisoformat(focus["end_time"])
            if _now_utc() >= end_time:
                return self.stop_focus()
        return focus

    def start_focus(self, payload: FocusStartRequest) -> dict:
        end_time = _now_utc() + timedelta(minutes=payload.duration_minutes)
        with self._conn() as conn:
            conn.execute(
                "UPDATE focus_state SET active = 1, duration_minutes = ?, end_time = ? WHERE id = 1",
                (payload.duration_minutes, end_time.isoformat()),
            )
        return self._read_focus()

    def stop_focus(self) -> dict:
        with self._conn() as conn:
            conn.execute("UPDATE focus_state SET active = 0, duration_minutes = 0, end_time = NULL WHERE id = 1")
        return self._read_focus()

    def _range_count(self, start: datetime, end: datetime) -> int:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM sessions
                WHERE status = 'completed' AND end_time >= ? AND end_time < ?
                """,
                (start.isoformat(), end.isoformat()),
            ).fetchone()
        return row["c"]

    def get_stats(self, days: int | None = None) -> dict:
        now = _now_utc()
        day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        week_start = day_start - timedelta(days=day_start.weekday())
        stats_range_start = None if days is None else (day_start - timedelta(days=days - 1))

        range_condition = ""
        range_params: tuple = ()
        if stats_range_start is not None:
            range_condition = " AND end_time >= ?"
            range_params = (stats_range_start.isoformat(),)

        with self._conn() as conn:
            total_focus_row = conn.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) AS total_focus_minutes FROM sessions"
            ).fetchone()
            interrupt_row = conn.execute(
                "SELECT COUNT(*) AS interrupt_count FROM sessions WHERE status = 'interrupted'"
            ).fetchone()
            total_sessions_row = conn.execute("SELECT COUNT(*) AS total_sessions FROM sessions").fetchone()
            todos_row = conn.execute(
                "SELECT COUNT(*) AS total_todos, COALESCE(SUM(completed), 0) AS completed_todos FROM todos"
            ).fetchone()
            recent_rows = conn.execute(
                f"""
                SELECT id, start_time, end_time, duration_minutes, todo_id, todo_title, status
                FROM sessions
                WHERE 1 = 1 {range_condition}
                ORDER BY id DESC
                LIMIT 10
                """,
                range_params,
            ).fetchall()
            trend_rows = conn.execute(
                f"""
                SELECT substr(end_time, 1, 10) AS day, COUNT(*) AS count
                FROM sessions
                WHERE status = 'completed' {range_condition}
                GROUP BY substr(end_time, 1, 10)
                ORDER BY day ASC
                """,
                range_params,
            ).fetchall()
            completion_times_rows = conn.execute(
                f"""
                SELECT end_time
                FROM sessions
                WHERE status = 'completed' {range_condition}
                ORDER BY end_time DESC
                LIMIT 100
                """,
                range_params,
            ).fetchall()

        total_todos = todos_row["total_todos"]
        completed_todos = todos_row["completed_todos"]
        completion_rate = round((completed_todos / total_todos) * 100, 2) if total_todos else 0

        recent_sessions = [
            {
                "id": row["id"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "duration_minutes": row["duration_minutes"],
                "todo_id": row["todo_id"],
                "todo_title": row["todo_title"],
                "status": row["status"],
            }
            for row in reversed(recent_rows)
        ]

        return {
            "today_pomodoros": self._range_count(day_start, day_start + timedelta(days=1)),
            "week_pomodoros": self._range_count(week_start, week_start + timedelta(days=7)),
            "total_focus_minutes": total_focus_row["total_focus_minutes"],
            "interrupt_count": interrupt_row["interrupt_count"],
            "total_sessions": total_sessions_row["total_sessions"],
            "total_todos": total_todos,
            "completed_todos": completed_todos,
            "todo_completion_rate": completion_rate,
            "recent_sessions": recent_sessions,
            "completion_trend": [{"date": row["day"], "count": row["count"]} for row in trend_rows],
            "completion_times": [row["end_time"] for row in reversed(completion_times_rows)],
            "range_days": days,
        }

    def record_pomodoro_with_detail(self, duration_minutes: int, todo_id: int | None, todo_title: str | None) -> dict:
        end_time = _now_utc()
        start_time = end_time - timedelta(minutes=duration_minutes)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO sessions (start_time, end_time, duration_minutes, todo_id, todo_title, status)
                VALUES (?, ?, ?, ?, ?, 'completed')
                """,
                (start_time.isoformat(), end_time.isoformat(), duration_minutes, todo_id, todo_title),
            )
            if todo_id is not None:
                conn.execute(
                    "UPDATE todos SET completed = 1, completed_count = completed_count + 1 WHERE id = ?",
                    (todo_id,),
                )
        return self.get_stats()

    def record_interrupt(self, duration_minutes: int, todo_id: int | None, todo_title: str | None) -> dict:
        end_time = _now_utc()
        start_time = end_time - timedelta(minutes=duration_minutes)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO sessions (start_time, end_time, duration_minutes, todo_id, todo_title, status)
                VALUES (?, ?, ?, ?, ?, 'interrupted')
                """,
                (start_time.isoformat(), end_time.isoformat(), duration_minutes, todo_id, todo_title),
            )
        return self.get_stats()

    def _read_ai_settings_raw(self) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT provider, base_url, model, api_key, temperature, max_tokens, enabled, updated_at
                FROM ai_settings
                WHERE id = 1
                """
            ).fetchone()
        return {
            "provider": row["provider"],
            "base_url": row["base_url"],
            "model": row["model"],
            "api_key": row["api_key"],
            "temperature": row["temperature"],
            "max_tokens": row["max_tokens"],
            "enabled": bool(row["enabled"]),
            "updated_at": row["updated_at"],
        }

    def _mask_api_key(self, api_key: str | None) -> str | None:
        if not api_key:
            return None
        if len(api_key) <= 10:
            return f"{api_key[:2]}***"
        return f"{api_key[:4]}***{api_key[-4:]}"

    def get_ai_config(self) -> dict:
        config = self._read_ai_settings_raw()
        return {
            "provider": config["provider"],
            "base_url": config["base_url"],
            "model": config["model"],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"],
            "enabled": config["enabled"],
            "api_key_set": bool(config["api_key"]),
            "api_key_hint": self._mask_api_key(config["api_key"]),
            "updated_at": config["updated_at"],
        }

    def save_ai_config(self, payload: AIConfigUpdate) -> dict:
        current = self._read_ai_settings_raw()
        next_api_key = current["api_key"]
        if payload.clear_api_key:
            next_api_key = None
        elif payload.replace_api_key and payload.api_key:
            next_api_key = payload.api_key.strip()

        normalized_base_url = (payload.base_url or "").strip() or None
        now_text = _now_utc().isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE ai_settings
                SET provider = ?, base_url = ?, model = ?, api_key = ?, temperature = ?, max_tokens = ?, enabled = ?, updated_at = ?
                WHERE id = 1
                """,
                (
                    payload.provider.strip(),
                    normalized_base_url,
                    payload.model.strip(),
                    next_api_key,
                    float(payload.temperature),
                    int(payload.max_tokens),
                    1 if payload.enabled else 0,
                    now_text,
                ),
            )
        return self.get_ai_config()

    def _build_usage_context(self, days: int = 30) -> dict:
        now = _now_utc()
        start = now - timedelta(days=days)
        with self._conn() as conn:
            todo_rows = conn.execute(
                """
                SELECT id, title, focus_minutes, timer_mode, completed_count, estimated_pomodoros
                FROM todos
                ORDER BY id DESC
                LIMIT 120
                """
            ).fetchall()
            rows = conn.execute(
                """
                SELECT start_time, end_time, duration_minutes, todo_id, todo_title, status
                FROM sessions
                WHERE end_time >= ?
                ORDER BY end_time DESC
                LIMIT 1000
                """,
                (start.isoformat(),),
            ).fetchall()

        completed = []
        interrupted = []
        completed_by_hour: dict[int, int] = {}
        interrupted_by_hour: dict[int, int] = {}
        weekday_focus: dict[str, int] = {}
        todo_stats: dict[int, dict] = {}

        for row in rows:
            end_dt = datetime.fromisoformat(row["end_time"]).astimezone()
            hour = end_dt.hour
            weekday = end_dt.strftime("%A")
            duration = int(row["duration_minutes"])
            status = row["status"]
            if status == "completed":
                completed.append(duration)
                completed_by_hour[hour] = completed_by_hour.get(hour, 0) + 1
                weekday_focus[weekday] = weekday_focus.get(weekday, 0) + duration
                if row["todo_id"] is not None:
                    info = todo_stats.setdefault(
                        int(row["todo_id"]),
                        {"completed_count": 0, "interrupted_count": 0, "sum_completed_minutes": 0},
                    )
                    info["completed_count"] += 1
                    info["sum_completed_minutes"] += duration
            else:
                interrupted.append(duration)
                interrupted_by_hour[hour] = interrupted_by_hour.get(hour, 0) + 1
                if row["todo_id"] is not None:
                    info = todo_stats.setdefault(
                        int(row["todo_id"]),
                        {"completed_count": 0, "interrupted_count": 0, "sum_completed_minutes": 0},
                    )
                    info["interrupted_count"] += 1

        total_sessions = len(rows)
        completed_count = len(completed)
        interrupted_count = len(interrupted)
        average_completed_minutes = round(sum(completed) / completed_count, 2) if completed_count else 0
        interrupt_rate = round((interrupted_count / total_sessions) * 100, 2) if total_sessions else 0

        top_focus_hours = sorted(completed_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        top_interrupt_hours = sorted(interrupted_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        top_focus_weekdays = sorted(weekday_focus.items(), key=lambda x: x[1], reverse=True)[:3]

        recent_sessions = []
        for row in rows[:25]:
            recent_sessions.append(
                {
                    "end_time": row["end_time"],
                    "duration_minutes": row["duration_minutes"],
                    "status": row["status"],
                    "todo_title": row["todo_title"],
                }
            )

        todo_profiles = []
        for todo in todo_rows:
            info = todo_stats.get(todo["id"], {"completed_count": 0, "interrupted_count": 0, "sum_completed_minutes": 0})
            avg_completed = (
                round(info["sum_completed_minutes"] / info["completed_count"], 2)
                if info["completed_count"] > 0
                else 0
            )
            todo_profiles.append(
                {
                    "todo_id": todo["id"],
                    "title": todo["title"],
                    "focus_minutes": todo["focus_minutes"],
                    "timer_mode": todo["timer_mode"],
                    "estimated_pomodoros": todo["estimated_pomodoros"],
                    "historical_completed_count": todo["completed_count"],
                    "recent_completed_count": info["completed_count"],
                    "recent_interrupted_count": info["interrupted_count"],
                    "recent_avg_completed_minutes": avg_completed,
                }
            )

        return {
            "range_days": days,
            "total_sessions": total_sessions,
            "completed_sessions": completed_count,
            "interrupted_sessions": interrupted_count,
            "interrupt_rate_percent": interrupt_rate,
            "average_completed_minutes": average_completed_minutes,
            "top_focus_hours": [{"hour": h, "count": c} for h, c in top_focus_hours],
            "top_interrupt_hours": [{"hour": h, "count": c} for h, c in top_interrupt_hours],
            "top_focus_weekdays": [{"weekday": d, "focus_minutes": m} for d, m in top_focus_weekdays],
            "recent_sessions": list(reversed(recent_sessions)),
            "todo_profiles": todo_profiles[:50],
        }

    def _fallback_ai_advice(self, usage: dict, extra_prompt: str | None = None) -> str:
        focus_hours = usage.get("top_focus_hours", [])
        interrupt_hours = usage.get("top_interrupt_hours", [])
        best_hours = "、".join([f"{item['hour']:02d}:00" for item in focus_hours]) if focus_hours else "暂无明显高效时段"
        risky_hours = "、".join([f"{item['hour']:02d}:00" for item in interrupt_hours]) if interrupt_hours else "暂无明显高风险时段"
        avg_minutes = usage.get("average_completed_minutes", 0)
        interrupt_rate = usage.get("interrupt_rate_percent", 0)

        lines = [
            "1) 核心观察",
            f"- 最近{usage.get('range_days', 30)}天完成 {usage.get('completed_sessions', 0)} 次，中断 {usage.get('interrupted_sessions', 0)} 次，中断率约 {interrupt_rate}%。",
            f"- 你的高效时段：{best_hours}；高打断时段：{risky_hours}。",
            f"- 完成番茄平均时长约 {avg_minutes} 分钟。",
            "2) 今日调整建议",
            "- 把最重要任务安排在你的高效时段，减少临时切换任务。",
            "- 在高打断时段使用更短番茄（20~25分钟）并关闭通知。",
            "3) 未来7天策略",
            "- 每天固定 2 个深度专注窗口，优先完成高价值待办。",
            "- 若连续2次中断，下一次番茄改为更小目标并先完成最小可交付。",
            "4) 风险提醒",
            "- 若中断率持续高于35%，建议减少并行任务数量并复盘打断来源。",
        ]
        if extra_prompt:
            lines.append(f"\n补充需求：{extra_prompt}")
        lines.append("\n提示：当前为规则引擎建议；配置AI后可生成更个性化分析。")
        return "\n".join(lines)

    def _build_fallback_tuning_suggestions(self, usage: dict) -> list[dict]:
        suggestions: list[dict] = []
        for todo in usage.get("todo_profiles", [])[:8]:
            title = str(todo.get("title") or "").strip()
            if not title:
                continue
            current_minutes = int(todo.get("focus_minutes") or 25)
            avg_completed = float(todo.get("recent_avg_completed_minutes") or 0)
            interrupted_count = int(todo.get("recent_interrupted_count") or 0)

            suggested_title = title
            if len(title) <= 2 or title.isdigit():
                suggested_title = f"{title}-明确子任务" if title else "明确任务名称"

            suggested_minutes = current_minutes
            reason_parts = []
            if avg_completed and avg_completed < current_minutes * 0.65:
                suggested_minutes = max(15, min(current_minutes, int(round(max(avg_completed, 15)))))
                reason_parts.append("近期平均完成时长偏短，建议先降低单次目标时长")
            elif interrupted_count >= 3:
                suggested_minutes = max(20, current_minutes - 5)
                reason_parts.append("近期打断偏多，建议缩短专注周期减少放弃概率")
            elif avg_completed >= current_minutes * 1.05 and current_minutes < 50:
                suggested_minutes = min(50, current_minutes + 5)
                reason_parts.append("你能稳定完成当前周期，可小幅延长提升深度")

            if suggested_title != title:
                reason_parts.append("任务命名过于宽泛，建议改为可执行子任务名称")
            if not reason_parts:
                reason_parts.append("当前设置基本合理，可维持并持续观察完成率")

            suggestions.append(
                {
                    "todo_id": todo.get("todo_id"),
                    "current_title": title,
                    "suggested_title": suggested_title,
                    "current_focus_minutes": current_minutes,
                    "suggested_focus_minutes": int(max(1, min(180, suggested_minutes))),
                    "reason": "；".join(reason_parts),
                }
            )
            if len(suggestions) >= 5:
                break
        return suggestions

    def _fallback_ai_advice_structured(self, usage: dict, extra_prompt: str | None = None) -> dict:
        focus_hours = usage.get("top_focus_hours", [])
        interrupt_hours = usage.get("top_interrupt_hours", [])
        best_hours = "、".join([f"{item['hour']:02d}:00" for item in focus_hours]) if focus_hours else "暂无明显高效时段"
        risky_hours = "、".join([f"{item['hour']:02d}:00" for item in interrupt_hours]) if interrupt_hours else "暂无明显高风险时段"
        avg_minutes = usage.get("average_completed_minutes", 0)
        interrupt_rate = usage.get("interrupt_rate_percent", 0)

        headline = f"最近{usage.get('range_days', 30)}天中断率约{interrupt_rate}%，建议优先稳定高效时段并降低碎片化专注。"
        sections = [
            {
                "title": "核心观察",
                "bullets": [
                    f"最近{usage.get('range_days', 30)}天完成 {usage.get('completed_sessions', 0)} 次，中断 {usage.get('interrupted_sessions', 0)} 次。",
                    f"高效时段：{best_hours}；高打断时段：{risky_hours}。",
                    f"完成番茄平均时长约 {avg_minutes} 分钟。",
                ],
            },
            {
                "title": "今日调整建议",
                "bullets": [
                    "将最重要任务安排在高效时段，减少任务切换。",
                    "在高打断时段采用更小任务粒度并开启免打扰。",
                ],
            },
            {
                "title": "未来7天策略",
                "bullets": [
                    "每天固定2个深度专注窗口，优先处理高价值任务。",
                    "连续2次中断后，下一次番茄钟缩小目标并先完成最小可交付。",
                ],
            },
            {
                "title": "风险提醒",
                "bullets": [
                    "若中断率持续高于35%，建议减少并行任务并复盘打断来源。",
                    "避免只记录时长不关注产出，需绑定任务结果复盘。",
                ],
            },
        ]
        if extra_prompt:
            sections[1]["bullets"].append(f"已结合你的补充需求：{extra_prompt}")
        return {
            "headline": headline,
            "sections": sections,
            "task_tuning_suggestions": self._build_fallback_tuning_suggestions(usage),
        }

    def _sanitize_structured_advice(self, advice: dict) -> dict:
        default_titles = ["核心观察", "今日调整建议", "未来7天策略", "风险提醒"]
        sections = advice.get("sections") if isinstance(advice, dict) else None
        if not isinstance(sections, list):
            raise ValueError("sections must be list")

        normalized = []
        for index, title in enumerate(default_titles):
            section = sections[index] if index < len(sections) and isinstance(sections[index], dict) else {}
            raw_title = str(section.get("title") or title).strip()
            section_title = raw_title if raw_title in default_titles else title
            bullets_raw = section.get("bullets") if isinstance(section.get("bullets"), list) else []
            bullets = []
            for item in bullets_raw:
                text = str(item).replace("**", "").replace("`", "").replace("#", "").strip()
                if not text:
                    continue
                if text.startswith("- "):
                    text = text[2:].strip()
                bullets.append(text)
            if not bullets:
                bullets = ["暂无建议，请稍后重试。"]
            normalized.append({"title": section_title, "bullets": bullets[:5]})

        headline = str(advice.get("headline") or "").replace("**", "").replace("`", "").replace("#", "").strip()
        if not headline:
            headline = "已基于近期番茄钟记录生成专注建议。"

        raw_tuning = advice.get("task_tuning_suggestions") if isinstance(advice, dict) else None
        tuning_list = raw_tuning if isinstance(raw_tuning, list) else []
        normalized_tuning = []
        for item in tuning_list[:8]:
            if not isinstance(item, dict):
                continue
            current_title = str(item.get("current_title") or "").replace("**", "").replace("`", "").strip()
            suggested_title = str(item.get("suggested_title") or current_title).replace("**", "").replace("`", "").strip()
            reason = str(item.get("reason") or "").replace("**", "").replace("`", "").replace("#", "").strip()
            if not current_title:
                continue
            try:
                current_focus_minutes = int(item.get("current_focus_minutes") or 25)
            except Exception:
                current_focus_minutes = 25
            try:
                suggested_focus_minutes = int(item.get("suggested_focus_minutes") or current_focus_minutes)
            except Exception:
                suggested_focus_minutes = current_focus_minutes
            suggested_focus_minutes = max(1, min(180, suggested_focus_minutes))
            current_focus_minutes = max(1, min(180, current_focus_minutes))
            normalized_tuning.append(
                {
                    "todo_id": item.get("todo_id"),
                    "current_title": current_title,
                    "suggested_title": suggested_title or current_title,
                    "current_focus_minutes": current_focus_minutes,
                    "suggested_focus_minutes": suggested_focus_minutes,
                    "reason": reason or "根据近期完成与打断情况给出的调优建议。",
                }
            )
            if len(normalized_tuning) >= 5:
                break

        return {"headline": headline, "sections": normalized, "task_tuning_suggestions": normalized_tuning}

    def generate_ai_advice(self, days: int = 30, prompt: str | None = None) -> dict:
        usage = self._build_usage_context(days)
        config = self._read_ai_settings_raw()

        if not config["enabled"] or not config["api_key"]:
            structured = self._fallback_ai_advice_structured(usage, prompt)
            return {
                "used_ai": False,
                "provider": config["provider"],
                "generated_at": _now_utc().isoformat(),
                "advice": self._fallback_ai_advice(usage, prompt),
                "advice_structured": structured,
                "usage_snapshot": usage,
                "reason": "AI未启用或未配置API Key",
            }

        try:
            agent = PomodoroAdvisorAgent(config)
            structured_raw = agent.generate(usage, prompt)
            structured = self._sanitize_structured_advice(structured_raw)
            advice_text = "\n".join(
                [structured["headline"]]
                + [f"{section['title']}：{'；'.join(section['bullets'])}" for section in structured["sections"]]
            )
            return {
                "used_ai": True,
                "provider": config["provider"],
                "generated_at": _now_utc().isoformat(),
                "advice": advice_text,
                "advice_structured": structured,
                "usage_snapshot": usage,
                "reason": "ok",
            }
        except Exception as exc:
            structured = self._fallback_ai_advice_structured(usage, prompt)
            return {
                "used_ai": False,
                "provider": config["provider"],
                "generated_at": _now_utc().isoformat(),
                "advice": self._fallback_ai_advice(usage, prompt),
                "advice_structured": structured,
                "usage_snapshot": usage,
                "reason": "AI调用失败，已降级规则建议",
            }

    def _fallback_plan_optimization(self, title: str, segments: list[dict], prompt: str | None = None) -> dict:
        suggestions = []
        for item in segments[:30]:
            seg_id = str(item.get("id") or "")
            start = str(item.get("start") or "")
            end = str(item.get("end") or "")
            task = str(item.get("task") or "").strip()
            if not seg_id or not start or not end or not task:
                continue
            next_start = start
            next_end = end
            next_task = task
            reason = "建议增加缓冲并明确动作产出。"
            if task in {"早餐", "午餐", "晚餐"}:
                reason = "饮食时间可适度放宽，降低赶时间压力。"
            elif "实验室" in task or "通勤" in task or "路上" in task:
                reason = "通勤/移动常有不确定性，建议预留机动时间。"
            elif len(task) < 4:
                next_task = f"{task}（明确目标）"
                reason = "任务描述偏短，建议补充可执行目标。"
            suggestions.append(
                {
                    "segment_id": seg_id,
                    "suggested_start": next_start,
                    "suggested_end": next_end,
                    "suggested_task": next_task,
                    "reason": reason,
                }
            )
        return {
            "used_ai": False,
            "provider": self._read_ai_settings_raw().get("provider"),
            "generated_at": _now_utc().isoformat(),
            "reason": "AI未启用或调用失败，已使用规则建议",
            "raw_advice": f"已对计划《{title}》生成规则优化建议。",
            "suggestions": suggestions,
            "plan_title": title,
            "prompt_echo": prompt or "",
        }

    def _normalize_hhmm(self, value: str) -> str:
        text = str(value or "").strip()
        matched = re.match(r"^(\d{1,2}):(\d{2})$", text)
        if not matched:
            return ""
        hour = int(matched.group(1))
        minute = int(matched.group(2))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return ""
        return f"{hour:02d}:{minute:02d}"

    def _normalize_generated_segments(self, segments: list[dict]) -> list[dict]:
        normalized: list[dict] = []
        for index, item in enumerate(segments[:40]):
            start = self._normalize_hhmm(item.get("start"))
            end = self._normalize_hhmm(item.get("end"))
            task = str(item.get("task") or "").strip()
            if not start or not end or not task:
                continue
            normalized.append(
                {
                    "id": str(item.get("id") or f"seg-{index + 1}"),
                    "start": start,
                    "end": end,
                    "task": task,
                }
            )
        return normalized

    def _fallback_plan_schedule(self, goal: str, days: int, prompt: str | None = None) -> dict:
        core_goal = str(goal or "").strip() or "阶段学习目标"
        segments = [
            {"id": "seg-1", "start": "07:30", "end": "08:00", "task": "晨间回顾今日目标与关键任务"},
            {"id": "seg-2", "start": "09:00", "end": "10:30", "task": f"核心学习：{core_goal}（理论输入）"},
            {"id": "seg-3", "start": "10:45", "end": "12:00", "task": f"动手练习：围绕{core_goal}完成最小Demo"},
            {"id": "seg-4", "start": "14:00", "end": "15:30", "task": "项目实战：实现一个可运行功能并记录问题"},
            {"id": "seg-5", "start": "16:00", "end": "17:00", "task": "查漏补缺：修复问题并整理知识卡片"},
            {"id": "seg-6", "start": "20:00", "end": "20:30", "task": "当日复盘：记录进展、阻塞点、次日调整"},
            {"id": "seg-7", "start": "21:00", "end": "21:30", "task": "轻量预习：阅读明日学习材料"},
        ]
        return {
            "used_ai": False,
            "provider": self._read_ai_settings_raw().get("provider"),
            "generated_at": _now_utc().isoformat(),
            "reason": "AI未启用或调用失败，已使用规则计划模板",
            "plan": {
                "title": f"{core_goal}-30天学习计划",
                "note": f"按天执行固定节奏，围绕目标持续迭代，周期 {days} 天。",
                "review": "每日20:00复盘；每周末复盘本周产出并调整下周任务。",
                "segments": segments,
            },
            "prompt_echo": prompt or "",
        }

    def generate_plan_schedule(self, goal: str, days: int = 30, prompt: str | None = None) -> dict:
        normalized_goal = str(goal or "").strip()
        if not normalized_goal:
            return self._fallback_plan_schedule("阶段学习目标", days, prompt)

        config = self._read_ai_settings_raw()
        if not config["enabled"] or not config["api_key"]:
            return self._fallback_plan_schedule(normalized_goal, days, prompt)

        try:
            from langchain_core.output_parsers import JsonOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI
            from pydantic import BaseModel, Field

            class PlanGenerateSegment(BaseModel):
                start: str = Field(description="开始时间，格式HH:mm")
                end: str = Field(description="结束时间，格式HH:mm")
                task: str = Field(description="可执行任务描述")

            class PlanGenerateOutput(BaseModel):
                title: str = Field(description="计划标题")
                note: str = Field(description="计划说明")
                review: str = Field(description="复盘节奏")
                segments: list[PlanGenerateSegment] = Field(description="时间段计划，至少6条")

            llm_kwargs: dict = {
                "model": config["model"],
                "api_key": config["api_key"],
                "temperature": float(config["temperature"]),
                "max_tokens": int(config["max_tokens"]),
                "timeout": float(config.get("request_timeout_seconds", 45)),
            }
            base_url = (config.get("base_url") or "").strip()
            if base_url:
                llm_kwargs["base_url"] = base_url

            llm = ChatOpenAI(**llm_kwargs)
            parser = JsonOutputParser(pydantic_object=PlanGenerateOutput)
            prompt_tmpl = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "你是学习计划制定助手。只根据用户目标生成计划，不要引用番茄钟统计。"
                        " 输出必须是纯JSON，不要Markdown，不要解释。"
                        " segments 至少6条，时间必须是HH:mm，任务必须具体可执行。"
                        " 计划中必须包含至少1条复盘任务。"
                    ),
                    (
                        "human",
                        "用户目标：{goal}\n计划周期(天)：{days}\n补充约束：{extra_prompt}\n\n输出格式要求：{format_instructions}",
                    ),
                ]
            )
            chain = prompt_tmpl | llm | parser
            output = chain.invoke(
                {
                    "goal": normalized_goal,
                    "days": int(days or 30),
                    "extra_prompt": (prompt or "无"),
                    "format_instructions": parser.get_format_instructions(),
                }
            )
            segments_raw = output.get("segments") if isinstance(output, dict) else []
            segments = self._normalize_generated_segments(segments_raw or [])
            if len(segments) < 3:
                return self._fallback_plan_schedule(normalized_goal, days, prompt)

            return {
                "used_ai": True,
                "provider": config["provider"],
                "generated_at": _now_utc().isoformat(),
                "reason": "ok",
                "plan": {
                    "title": str(output.get("title") or f"{normalized_goal}-学习计划").strip(),
                    "note": str(output.get("note") or "").strip(),
                    "review": str(output.get("review") or "").strip(),
                    "segments": segments,
                },
                "prompt_echo": prompt or "",
            }
        except Exception:
            return self._fallback_plan_schedule(normalized_goal, days, prompt)

    def generate_plan_optimization(self, title: str, segments: list[PlanSegmentInput], prompt: str | None = None) -> dict:
        normalized_segments = [
            {"id": s.id, "start": s.start, "end": s.end, "task": s.task}
            for s in segments
            if s and s.id and s.start and s.end and s.task
        ]
        if not normalized_segments:
            return self._fallback_plan_optimization(title, [], prompt)

        config = self._read_ai_settings_raw()
        if not config["enabled"] or not config["api_key"]:
            return self._fallback_plan_optimization(title, normalized_segments, prompt)

        try:
            from langchain_core.output_parsers import JsonOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI
            from pydantic import BaseModel, Field
            import json

            class SegmentSuggestion(BaseModel):
                segment_id: str = Field(description="原计划事件ID")
                suggested_start: str = Field(description="建议开始时间，格式HH:mm")
                suggested_end: str = Field(description="建议结束时间，格式HH:mm")
                suggested_task: str = Field(description="建议事件描述")
                reason: str = Field(description="建议原因，简洁可执行")

            class PlanOptimizeOutput(BaseModel):
                summary: str = Field(description="一句话总结")
                suggestions: list[SegmentSuggestion] = Field(description="逐项建议，至少1条")

            llm_kwargs: dict = {
                "model": config["model"],
                "api_key": config["api_key"],
                "temperature": float(config["temperature"]),
                "max_tokens": int(config["max_tokens"]),
                "timeout": float(config.get("request_timeout_seconds", 45)),
            }
            base_url = (config.get("base_url") or "").strip()
            if base_url:
                llm_kwargs["base_url"] = base_url

            llm = ChatOpenAI(**llm_kwargs)
            parser = JsonOutputParser(pydantic_object=PlanOptimizeOutput)
            prompt_tmpl = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "你是个人计划优化助手。只基于用户给出的计划内容做优化，不要引用番茄钟统计。"
                        " 输出必须是纯JSON，不要Markdown，不要解释。"
                        " suggestions 每条都必须给 segment_id、suggested_start、suggested_end、suggested_task、reason。"
                        " segment_id 必须从输入事件中选择。时间格式HH:mm。"
                    ),
                    (
                        "human",
                        "计划标题：{title}\n计划事件(JSON)：\n{segments_json}\n用户补充需求：{extra_prompt}\n\n输出格式要求：{format_instructions}",
                    ),
                ]
            )
            chain = prompt_tmpl | llm | parser
            output = chain.invoke(
                {
                    "title": title,
                    "segments_json": json.dumps(normalized_segments, ensure_ascii=False, indent=2),
                    "extra_prompt": (prompt or "无"),
                    "format_instructions": parser.get_format_instructions(),
                }
            )
            suggestions_raw = output.get("suggestions") if isinstance(output, dict) else []
            suggestions = []
            valid_ids = {s["id"] for s in normalized_segments}
            for item in (suggestions_raw or []):
                seg_id = str(item.get("segment_id") or "")
                if seg_id not in valid_ids:
                    continue
                start = str(item.get("suggested_start") or "").strip()
                end = str(item.get("suggested_end") or "").strip()
                task = str(item.get("suggested_task") or "").strip()
                reason_text = str(item.get("reason") or "").strip() or "AI建议优化该事件安排。"
                if not start or not end or not task:
                    continue
                suggestions.append(
                    {
                        "segment_id": seg_id,
                        "suggested_start": start,
                        "suggested_end": end,
                        "suggested_task": task,
                        "reason": reason_text,
                    }
                )

            if not suggestions:
                return self._fallback_plan_optimization(title, normalized_segments, prompt)

            return {
                "used_ai": True,
                "provider": config["provider"],
                "generated_at": _now_utc().isoformat(),
                "reason": "ok",
                "raw_advice": str(output.get("summary") or "").strip(),
                "suggestions": suggestions,
                "plan_title": title,
                "prompt_echo": prompt or "",
            }
        except Exception:
            return self._fallback_plan_optimization(title, normalized_segments, prompt)

    def get_me(self) -> dict:
        with self._conn() as conn:
            row = conn.execute("SELECT id, nickname FROM users WHERE id = 1").fetchone()
        return {"id": row["id"], "nickname": row["nickname"]}


service = SQLiteService()
