from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        age_group TEXT,
        teacher_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        duration_seconds REAL,
        confidence_score REAL,
        grade TEXT,
        confidence_label TEXT,
        confidence_threshold REAL,
        analysis_quality_score REAL,
        model_analysis TEXT,
        analysis_profile TEXT,
        emotion_happy REAL,
        emotion_neutral REAL,
        emotion_sad REAL,
        emotion_anxious REAL,
        emotion_surprised REAL,
        eye_center_pct REAL,
        eye_away_pct REAL,
        blink_count INTEGER,
        posture_score REAL,
        slouch_pct REAL,
        gesture_positive_pct REAL,
        gesture_nervous_pct REAL,
        wpm REAL,
        filler_count INTEGER,
        filler_words TEXT,
        pause_count INTEGER,
        voice_energy REAL,
        pitch_variation REAL,
        transcript TEXT,
        word_count INTEGER,
        total_fillers INTEGER,
        long_pauses TEXT,
        llm_feedback TEXT,
        face_impression TEXT,
        tips_text TEXT,
        tips_path TEXT,
        visualization_emotion TEXT,
        visualization_gaze TEXT,
        visualization_speech TEXT,
        visualization_trend TEXT,
        visualization_radar TEXT,
        visualization_spectrogram TEXT,
        visualization_chromagram TEXT,
        report_path TEXT,
        video_path TEXT,
        highlight_reel_path TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS calibrations (
        user_id TEXT PRIMARY KEY,
        posture_baseline REAL,
        eye_baseline REAL,
        emotion_baseline REAL,
        gesture_baseline REAL,
        voice_baseline REAL,
        face_impression TEXT,
        confidence_threshold REAL DEFAULT 0.55,
        completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """,
]


@dataclass(slots=True)
class UserRecord:
    id: str
    name: str
    role: str
    age_group: str | None = None
    teacher_id: str | None = None


class DatabaseError(RuntimeError):
    pass


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def init_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        _ensure_session_columns(connection)
        connection.commit()


def _ensure_session_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(sessions)").fetchall()
    }
    extra_columns = {
        "grade": "TEXT",
        "confidence_label": "TEXT",
        "confidence_threshold": "REAL",
        "analysis_quality_score": "REAL",
        "model_analysis": "TEXT",
        "analysis_profile": "TEXT",
        "face_impression": "TEXT",
        "word_count": "INTEGER",
        "total_fillers": "INTEGER",
        "long_pauses": "TEXT",
        "tips_text": "TEXT",
        "tips_path": "TEXT",
        "visualization_emotion": "TEXT",
        "visualization_gaze": "TEXT",
        "visualization_speech": "TEXT",
        "visualization_trend": "TEXT",
        "visualization_radar": "TEXT",
        "visualization_spectrogram": "TEXT",
        "visualization_chromagram": "TEXT",
        "report_path": "TEXT",
    }
    for column_name, column_type in extra_columns.items():
        if column_name not in existing_columns:
            connection.execute(f"ALTER TABLE sessions ADD COLUMN {column_name} {column_type}")


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def upsert_user(db_path: Path, user: UserRecord | dict[str, Any]) -> dict[str, Any]:
    payload = user if isinstance(user, dict) else user.__dict__
    payload.setdefault("age_group", None)
    payload.setdefault("teacher_id", None)
    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO users (id, name, role, age_group, teacher_id)
            VALUES (:id, :name, :role, :age_group, :teacher_id)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                role=excluded.role,
                age_group=excluded.age_group,
                teacher_id=excluded.teacher_id;
            """,
            payload,
        )
        connection.commit()
    return get_user_by_id(db_path, str(payload["id"])) or payload


def get_user_by_id(db_path: Path, user_id: str) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_dict(row)


def get_latest_user(db_path: Path) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 1").fetchone()
    return _row_to_dict(row)


def save_session(db_path: Path, session_data: dict[str, Any]) -> int:
    data = dict(session_data)
    if isinstance(data.get("filler_words"), (dict, list)):
        data["filler_words"] = json.dumps(data["filler_words"])
    if isinstance(data.get("llm_feedback"), (dict, list)):
        data["llm_feedback"] = json.dumps(data["llm_feedback"])
    if isinstance(data.get("face_impression"), (dict, list)):
        data["face_impression"] = json.dumps(data["face_impression"])
    if isinstance(data.get("confidence_label"), (dict, list)):
        data["confidence_label"] = json.dumps(data["confidence_label"])
    if isinstance(data.get("model_analysis"), (dict, list)):
        data["model_analysis"] = json.dumps(data["model_analysis"])
    if isinstance(data.get("analysis_profile"), (dict, list)):
        data["analysis_profile"] = json.dumps(data["analysis_profile"])
    if isinstance(data.get("long_pauses"), (dict, list)):
        data["long_pauses"] = json.dumps(data["long_pauses"])

    columns = [
        "user_id",
        "duration_seconds",
        "confidence_score",
        "grade",
        "confidence_label",
        "confidence_threshold",
        "analysis_quality_score",
        "model_analysis",
        "analysis_profile",
        "emotion_happy",
        "emotion_neutral",
        "emotion_sad",
        "emotion_anxious",
        "emotion_surprised",
        "eye_center_pct",
        "eye_away_pct",
        "blink_count",
        "posture_score",
        "slouch_pct",
        "gesture_positive_pct",
        "gesture_nervous_pct",
        "wpm",
        "filler_count",
        "filler_words",
        "pause_count",
        "voice_energy",
        "pitch_variation",
        "transcript",
        "word_count",
        "total_fillers",
        "long_pauses",
        "llm_feedback",
        "face_impression",
        "tips_text",
        "tips_path",
        "visualization_emotion",
        "visualization_gaze",
        "visualization_speech",
        "visualization_trend",
        "visualization_radar",
        "visualization_spectrogram",
        "visualization_chromagram",
        "report_path",
        "video_path",
        "highlight_reel_path",
    ]
    values = {column: data.get(column) for column in columns}

    with _connect(db_path) as connection:
        cursor = connection.execute(
            f"""
            INSERT INTO sessions ({', '.join(columns)})
            VALUES ({', '.join(':' + column for column in columns)});
            """,
            values,
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_session_by_id(db_path: Path, session_id: int) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    result = _row_to_dict(row)
    if result and result.get("filler_words"):
        try:
            result["filler_words"] = json.loads(result["filler_words"])
        except json.JSONDecodeError:
            pass
    if result and result.get("llm_feedback"):
        try:
            result["llm_feedback"] = json.loads(result["llm_feedback"])
        except json.JSONDecodeError:
            pass
    if result and result.get("face_impression"):
        try:
            result["face_impression"] = json.loads(result["face_impression"])
        except json.JSONDecodeError:
            pass
    if result and result.get("confidence_label"):
        try:
            result["confidence_label"] = json.loads(result["confidence_label"])
        except json.JSONDecodeError:
            pass
    if result and result.get("model_analysis"):
        try:
            result["model_analysis"] = json.loads(result["model_analysis"])
        except json.JSONDecodeError:
            pass
    if result and result.get("analysis_profile"):
        try:
            result["analysis_profile"] = json.loads(result["analysis_profile"])
        except json.JSONDecodeError:
            pass
    if result and result.get("long_pauses"):
        try:
            result["long_pauses"] = json.loads(result["long_pauses"])
        except json.JSONDecodeError:
            pass
    return result


def get_sessions_for_user(db_path: Path, user_id: str, limit: int | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM sessions WHERE user_id = ? ORDER BY timestamp ASC"
    params: tuple[Any, ...] = (user_id,)
    if limit is not None:
        query += " LIMIT ?"
        params = (user_id, limit)
    with _connect(db_path) as connection:
        rows = connection.execute(query, params).fetchall()
    results = []
    for row in rows:
        item = dict(row)
        if item.get("filler_words"):
            try:
                item["filler_words"] = json.loads(item["filler_words"])
            except json.JSONDecodeError:
                pass
        if item.get("llm_feedback"):
            try:
                item["llm_feedback"] = json.loads(item["llm_feedback"])
            except json.JSONDecodeError:
                pass
        if item.get("face_impression"):
            try:
                item["face_impression"] = json.loads(item["face_impression"])
            except json.JSONDecodeError:
                pass
        if item.get("confidence_label"):
            try:
                item["confidence_label"] = json.loads(item["confidence_label"])
            except json.JSONDecodeError:
                pass
        if item.get("model_analysis"):
            try:
                item["model_analysis"] = json.loads(item["model_analysis"])
            except json.JSONDecodeError:
                pass
        if item.get("analysis_profile"):
            try:
                item["analysis_profile"] = json.loads(item["analysis_profile"])
            except json.JSONDecodeError:
                pass
        if item.get("long_pauses"):
            try:
                item["long_pauses"] = json.loads(item["long_pauses"])
            except json.JSONDecodeError:
                pass
        results.append(item)
    return results


def get_last_session_for_user(db_path: Path, user_id: str) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    result = _row_to_dict(row)
    if result and result.get("filler_words"):
        try:
            result["filler_words"] = json.loads(result["filler_words"])
        except json.JSONDecodeError:
            pass
    if result and result.get("llm_feedback"):
        try:
            result["llm_feedback"] = json.loads(result["llm_feedback"])
        except json.JSONDecodeError:
            pass
    if result and result.get("face_impression"):
        try:
            result["face_impression"] = json.loads(result["face_impression"])
        except json.JSONDecodeError:
            pass
    if result and result.get("confidence_label"):
        try:
            result["confidence_label"] = json.loads(result["confidence_label"])
        except json.JSONDecodeError:
            pass
    if result and result.get("model_analysis"):
        try:
            result["model_analysis"] = json.loads(result["model_analysis"])
        except json.JSONDecodeError:
            pass
    if result and result.get("analysis_profile"):
        try:
            result["analysis_profile"] = json.loads(result["analysis_profile"])
        except json.JSONDecodeError:
            pass
    if result and result.get("long_pauses"):
        try:
            result["long_pauses"] = json.loads(result["long_pauses"])
        except json.JSONDecodeError:
            pass
    return result


def get_all_users(db_path: Path) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def save_calibration(db_path: Path, user_id: str, calibration_data: dict[str, Any]) -> None:
    face_impression = calibration_data.get("face_impression")
    if isinstance(face_impression, (dict, list)):
        face_impression = json.dumps(face_impression)
    payload = {
        "user_id": user_id,
        "posture_baseline": calibration_data.get("posture_baseline"),
        "eye_baseline": calibration_data.get("eye_baseline"),
        "emotion_baseline": calibration_data.get("emotion_baseline"),
        "gesture_baseline": calibration_data.get("gesture_baseline"),
        "voice_baseline": calibration_data.get("voice_baseline"),
        "face_impression": face_impression,
        "confidence_threshold": calibration_data.get("confidence_threshold", 0.55),
    }
    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO calibrations (
                user_id, posture_baseline, eye_baseline, emotion_baseline,
                gesture_baseline, voice_baseline, face_impression, confidence_threshold
            ) VALUES (
                :user_id, :posture_baseline, :eye_baseline, :emotion_baseline,
                :gesture_baseline, :voice_baseline, :face_impression, :confidence_threshold
            )
            ON CONFLICT(user_id) DO UPDATE SET
                posture_baseline=excluded.posture_baseline,
                eye_baseline=excluded.eye_baseline,
                emotion_baseline=excluded.emotion_baseline,
                gesture_baseline=excluded.gesture_baseline,
                voice_baseline=excluded.voice_baseline,
                face_impression=excluded.face_impression,
                confidence_threshold=excluded.confidence_threshold,
                completed_at=CURRENT_TIMESTAMP;
            """,
            payload,
        )
        connection.commit()


def get_calibration(db_path: Path, user_id: str) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute("SELECT * FROM calibrations WHERE user_id = ?", (user_id,)).fetchone()
    result = _row_to_dict(row)
    if result and result.get("face_impression"):
        try:
            result["face_impression"] = json.loads(result["face_impression"])
        except Exception:
            pass
    return result


def get_teacher_students(db_path: Path, teacher_id: str) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM users WHERE teacher_id = ? OR id = ? ORDER BY created_at DESC",
            (teacher_id, teacher_id),
        ).fetchall()
    return [dict(row) for row in rows]


def get_teacher_session_rows(db_path: Path, teacher_id: str) -> list[dict[str, Any]]:
    students = {row["id"] for row in get_teacher_students(db_path, teacher_id)}
    if not students:
        return []
    placeholders = ",".join("?" for _ in students)
    with _connect(db_path) as connection:
        rows = connection.execute(
            f"SELECT * FROM sessions WHERE user_id IN ({placeholders}) ORDER BY timestamp DESC",
            tuple(students),
        ).fetchall()
    return [dict(row) for row in rows]


def execute_query(db_path: Path, query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    return [dict(row) for row in rows]
