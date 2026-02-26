import sqlite3
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .schemas import CollectionCreate, CollectionUpdate, FocusStartRequest, TodoCreate, TodoUpdate


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
                "INSERT OR IGNORE INTO focus_state (id, active, duration_minutes, end_time) VALUES (1, 0, 0, NULL)"
            )
            conn.execute(
                "INSERT OR IGNORE INTO users (id, nickname) VALUES (1, 'Windows用户')"
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

    def get_me(self) -> dict:
        with self._conn() as conn:
            row = conn.execute("SELECT id, nickname FROM users WHERE id = 1").fetchone()
        return {"id": row["id"], "nickname": row["nickname"]}


service = SQLiteService()
