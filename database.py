"""
database.py — SQLite persistence layer
DB file: <app_dir>/data/screenqc.db  (dev)
         ~/Library/Application Support/DesktopQC/data/screenqc.db  (bundled macOS)
         %APPDATA%/DesktopQC/data/screenqc.db  (bundled Windows)
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

if getattr(sys, "frozen", False):
    # Running as PyInstaller bundle — use persistent user data directory
    import platform
    if platform.system() == "Darwin":
        _APP_DIR = os.path.expanduser("~/Library/Application Support/DesktopQC")
    elif platform.system() == "Windows":
        _APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "DesktopQC")
    else:
        _APP_DIR = os.path.expanduser("~/.DesktopQC")
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_DIR  = os.path.join(_APP_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "screenqc.db")


def _conn() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS settings (
                id            INTEGER PRIMARY KEY,
                hospital_name TEXT NOT NULL,
                screen_model  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT NOT NULL,
                lastname TEXT NOT NULL DEFAULT '',
                password TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evaluations (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_name   TEXT    NOT NULL,
                evaluator_name  TEXT    NOT NULL,
                screen_model    TEXT    NOT NULL,
                screen_type     TEXT    NOT NULL,
                period          TEXT    NOT NULL,
                eval_datetime   TEXT    NOT NULL,
                overall_pass    INTEGER NOT NULL,
                is_baseline     INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS answers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id   INTEGER NOT NULL REFERENCES evaluations(id),
                item_id         TEXT    NOT NULL,
                passed          INTEGER NOT NULL,
                failed_channels TEXT    NOT NULL DEFAULT '[]',
                notes           TEXT    NOT NULL DEFAULT ''
            );
        """)
        # migration: เพิ่มคอลัมน์ lastname ถ้า DB เก่ายังไม่มี
        try:
            c.execute("ALTER TABLE users ADD COLUMN lastname TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError:
            pass


def save_settings(hospital: str, screen_model: str):
    """บันทึก/อัปเดตข้อมูลอุปกรณ์ (มีได้แถวเดียว)"""
    init_db()
    with _conn() as c:
        c.execute("DELETE FROM settings")
        c.execute(
            "INSERT INTO settings (hospital_name, screen_model) VALUES (?,?)",
            (hospital, screen_model),
        )


def get_settings() -> dict | None:
    """คืนข้อมูลอุปกรณ์ที่บันทึกไว้ หรือ None"""
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM settings LIMIT 1").fetchone()
        return dict(row) if row else None


def add_user(name: str, lastname: str, password: str) -> str | None:
    """เพิ่มผู้ใช้ คืน None ถ้าสำเร็จ หรือข้อความ error ถ้าชื่อ+นามสกุลซ้ำ"""
    init_db()
    with _conn() as c:
        dup = c.execute(
            "SELECT id FROM users WHERE name=? AND lastname=?", (name, lastname)
        ).fetchone()
        if dup:
            return "ชื่อ-นามสกุลนี้ถูกลงทะเบียนแล้ว"
        c.execute(
            "INSERT INTO users (name, lastname, password) VALUES (?,?,?)",
            (name, lastname, password),
        )
    return None


def get_all_users() -> list[dict]:
    """คืนรายชื่อผู้ใช้ทั้งหมด"""
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM users ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def verify_login(display_name: str, password: str) -> bool:
    """ตรวจสอบ login โดย display_name = 'ชื่อ นามสกุล'"""
    init_db()
    parts = display_name.strip().split(" ", 1)
    name = parts[0]
    lastname = parts[1] if len(parts) > 1 else ""
    with _conn() as c:
        row = c.execute(
            "SELECT id FROM users WHERE name=? AND lastname=? AND password=?",
            (name, lastname, password),
        ).fetchone()
        return row is not None


def verify_user_password(user_id: int, password: str) -> bool:
    """ตรวจสอบว่ารหัสถูกต้องหรือไม่"""
    init_db()
    with _conn() as c:
        row = c.execute(
            "SELECT id FROM users WHERE id=? AND password=?", (user_id, password)
        ).fetchone()
        return row is not None


def update_user(user_id: int, name: str, lastname: str, password: str) -> str | None:
    """แก้ไขชื่อ-นามสกุล-รหัส คืน None ถ้าสำเร็จ หรือข้อความ error ถ้าซ้ำ"""
    init_db()
    with _conn() as c:
        dup = c.execute(
            "SELECT id FROM users WHERE name=? AND lastname=? AND id!=?",
            (name, lastname, user_id),
        ).fetchone()
        if dup:
            return "ชื่อ-นามสกุลนี้ถูกลงทะเบียนแล้ว"
        c.execute(
            "UPDATE users SET name=?, lastname=?, password=? WHERE id=?",
            (name, lastname, password, user_id),
        )
    return None


def delete_user(user_id: int):
    """ลบผู้ใช้"""
    init_db()
    with _conn() as c:
        c.execute("DELETE FROM users WHERE id=?", (user_id,))


def save_evaluation(session: dict) -> int:
    """บันทึก session ลง DB และคืน evaluation_id"""
    init_db()
    answers = session.get("answers", {})
    overall_pass = session.get("overall_pass", False)

    with _conn() as c:
        cur = c.execute(
            """INSERT INTO evaluations
               (hospital_name, evaluator_name, screen_model,
                screen_type, period, eval_datetime, overall_pass)
               VALUES (?,?,?,?,?,?,?)""",
            (
                session.get("hospital_name", ""),
                session.get("evaluator_name", ""),
                session.get("screen_model", ""),
                session.get("screen_type", ""),
                session.get("period", ""),
                session.get("eval_datetime", datetime.now().strftime("%d/%m/%Y %H:%M")),
                1 if overall_pass else 0,
            ),
        )
        eval_id = cur.lastrowid

        for item_id, ans in answers.items():
            c.execute(
                """INSERT INTO answers
                   (evaluation_id, item_id, passed, failed_channels, notes)
                   VALUES (?,?,?,?,?)""",
                (
                    eval_id,
                    item_id,
                    1 if ans.get("passed") else 0,
                    json.dumps(ans.get("failed_channels", [])),
                    ans.get("notes", ""),
                ),
            )

        return eval_id


def update_answer_note(evaluation_id: int, item_id: str, note: str):
    """อัปเดตหมายเหตุของคำตอบหนึ่งรายการ"""
    init_db()
    with _conn() as c:
        c.execute(
            "UPDATE answers SET notes=? WHERE evaluation_id=? AND item_id=?",
            (note, evaluation_id, item_id),
        )


def set_as_baseline(evaluation_id: int):
    """ตั้งค่า evaluation นี้เป็น baseline (ยกเลิก baseline เก่าของ type+period เดิมก่อน)"""
    init_db()
    with _conn() as c:
        row = c.execute(
            "SELECT screen_type, period FROM evaluations WHERE id=?",
            (evaluation_id,),
        ).fetchone()
        if not row:
            return
        c.execute(
            "UPDATE evaluations SET is_baseline=0 WHERE screen_type=? AND period=?",
            (row["screen_type"], row["period"]),
        )
        c.execute(
            "UPDATE evaluations SET is_baseline=1 WHERE id=?",
            (evaluation_id,),
        )


def get_eval_rank(screen_type: str, period: str, eval_id: int) -> int:
    """คืนลำดับของ evaluation นี้ในชุด screen_type+period (นับจาก 1)"""
    init_db()
    with _conn() as c:
        row = c.execute(
            "SELECT COUNT(*) FROM evaluations WHERE screen_type=? AND period=? AND id<=?",
            (screen_type, period, eval_id),
        ).fetchone()
        return row[0] if row else 1


def get_evaluations_before(screen_type: str, period: str, before_id: int) -> list[dict]:
    """คืน evaluations ก่อนหน้า before_id ของ type+period เดียวกัน (ล่าสุดก่อน) พร้อม rank"""
    init_db()
    with _conn() as c:
        rows = c.execute(
            """SELECT e.id, e.hospital_name, e.evaluator_name, e.eval_datetime, e.overall_pass,
                      (SELECT COUNT(*) FROM evaluations e2
                       WHERE e2.screen_type=e.screen_type AND e2.period=e.period AND e2.id<=e.id
                      ) AS rank
               FROM evaluations e
               WHERE e.screen_type=? AND e.period=? AND e.id<?
               ORDER BY e.id DESC""",
            (screen_type, period, before_id),
        ).fetchall()
        return [dict(r) for r in rows]


def get_baseline(screen_type: str, period: str, before_id: int = 0) -> dict | None:
    """คืน evaluation ครั้งก่อนหน้า (id < before_id) ของ type+period เดียวกัน"""
    init_db()
    with _conn() as c:
        row = c.execute(
            """SELECT * FROM evaluations
               WHERE screen_type=? AND period=? AND id<?
               ORDER BY id DESC LIMIT 1""",
            (screen_type, period, before_id),
        ).fetchone()
        if not row:
            return None
        return _load_full(c, dict(row))


def get_evaluation(evaluation_id: int) -> dict | None:
    """คืน evaluation พร้อม answers"""
    init_db()
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM evaluations WHERE id=?", (evaluation_id,)
        ).fetchone()
        if not row:
            return None
        return _load_full(c, dict(row))


def search_evaluations(
    hospital: str = "",
    evaluator: str = "",
    screen_type: str = "",
    period: str = "",
    date_from: str = "",
    date_to: str = "",
    screen_model: str = "",
    limit: int = 200,
) -> list[dict]:
    """ค้นหา evaluations — คืน list of dict (ไม่รวม answers เพื่อความเร็ว)"""
    init_db()
    sql  = "SELECT * FROM evaluations WHERE 1=1"
    args = []
    if hospital:
        sql  += " AND hospital_name LIKE ?"
        args.append(f"%{hospital}%")
    if evaluator:
        sql  += " AND evaluator_name LIKE ?"
        args.append(f"%{evaluator}%")
    if screen_model:
        sql  += " AND screen_model LIKE ?"
        args.append(f"%{screen_model}%")
    if screen_type:
        sql  += " AND screen_type=?"
        args.append(screen_type)
    if period:
        sql  += " AND period=?"
        args.append(period)
    # eval_datetime เก็บในรูป "YYYY-MM-DD HH:MM:SS" → ตัดแค่ 10 ตัวแรก
    # date_from / date_to ใส่เป็น "YYYY-MM-DD"
    if date_from:
        sql  += " AND substr(eval_datetime,1,10) >= ?"
        args.append(date_from)
    if date_to:
        sql  += " AND substr(eval_datetime,1,10) <= ?"
        args.append(date_to)
    sql += " ORDER BY id DESC LIMIT ?"
    args.append(limit)

    with _conn() as c:
        rows = c.execute(sql, args).fetchall()
        return [dict(r) for r in rows]


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_full(c: sqlite3.Connection, ev: dict) -> dict:
    """เพิ่ม answers dict เข้า evaluation dict"""
    rows = c.execute(
        "SELECT * FROM answers WHERE evaluation_id=?", (ev["id"],)
    ).fetchall()
    ev["answers"] = {
        r["item_id"]: {
            "passed":          bool(r["passed"]),
            "failed_channels": json.loads(r["failed_channels"]),
            "notes":           r["notes"],
        }
        for r in rows
    }
    return ev
