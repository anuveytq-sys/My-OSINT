#!/usr/bin/env python3
"""Local web dashboard for My-OSINT. Keeps main.py and the existing scan engine intact."""
from __future__ import annotations
import json, os, re, sqlite3, subprocess, threading, time, uuid, sys
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file, abort

from core.engine import run_modules
from core.result import Result
from email_modules.github import validate_github
from email_modules.reddit import validate_reddit
from email_modules.instagram import validate_instagram
from email_modules.twitter import validate_twitter
from phone_modules.basic_info import validate_phone
from phone_modules.enhanced_info import validate_phone_enhanced

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("MYOSINT_DB", ROOT / "myosint_history.sqlite3"))
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
TASKS: dict[str, dict] = {}
TASKS_LOCK = threading.Lock()

EMAIL_MODULES = [validate_github, validate_reddit, validate_instagram, validate_twitter]
PHONE_MODULES = [validate_phone, validate_phone_enhanced]

def now():
    return datetime.now(timezone.utc).isoformat()

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS scans (
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, target TEXT NOT NULL,
            status TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
            result_json TEXT NOT NULL DEFAULT '[]', logs_json TEXT NOT NULL DEFAULT '[]'
        )""")

def emit(task_id, message, level="info"):
    with TASKS_LOCK:
        task = TASKS.get(task_id)
        if task:
            task["logs"].append({"time": now(), "message": str(message)[:1200], "level": level})
            task["updated_at"] = now()

def result_dict(r):
    if isinstance(r, dict):
        return r
    return {"site": getattr(r, "site", "Unknown"),
            "exists": getattr(r, "exists", None),
            "info": getattr(r, "info", {}) or {},
            "error": getattr(r, "error", None)}

def save_task(task_id):
    with TASKS_LOCK:
        t = TASKS.get(task_id)
        if not t:
            return
        snap = dict(t)
        snap["logs"] = list(t["logs"])
        snap["results"] = list(t["results"])
    with db() as con:
        con.execute("""INSERT OR REPLACE INTO scans
        (id,kind,target,status,started_at,finished_at,result_json,logs_json)
        VALUES (?,?,?,?,?,?,?,?)""",
        (snap["id"], snap["kind"], snap["target"], snap["status"], snap["started_at"],
         snap.get("finished_at"), json.dumps(snap["results"], ensure_ascii=False),
         json.dumps(snap["logs"], ensure_ascii=False)))

def run_task(task_id):
    with TASKS_LOCK:
        task = TASKS[task_id]
        kind, target = task["kind"], task["target"]
        task["status"] = "running"
    emit(task_id, f"Starting {kind} scan for {target}")
    try:
        if kind == "email":
            emit(task_id, "Running the existing GitHub, Reddit, Instagram and X checks.")
            emit(task_id, "The existing engine will also attempt Holehe and configured SpiderFoot email modules.")
            raw = run_modules(target, EMAIL_MODULES)
            results = [result_dict(x) for x in raw]
        elif kind == "phone":
            emit(task_id, "Running number validation, carrier/region metadata and enhanced phone checks.")
            emit(task_id, "The existing engine will also attempt configured PhoneInfoga and SpiderFoot modules.")
            raw = run_modules(target, PHONE_MODULES)
            results = [result_dict(x) for x in raw]
        else:
            emit(task_id, "Launching the existing user-scanner command.")
            proc = subprocess.Popen(
                [sys.executable, "-m", "user_scanner", "-u", target], cwd=str(ROOT),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                bufsize=1, errors="replace"
            )
            output = []
            for line in proc.stdout or []:
                line = line.rstrip()
                if line:
                    output.append(line[:1200])
                    emit(task_id, line, "output")
            code = proc.wait(timeout=600)
            results = [{"site": "user-scanner", "exists": None,
                        "info": {"output": output, "exit_code": code},
                        "error": None if code == 0 else f"user-scanner exited with code {code}"}]
        with TASKS_LOCK:
            task = TASKS[task_id]
            task["results"] = results
            task["status"] = "completed"
            task["finished_at"] = now()
        emit(task_id, f"Scan completed. {len(results)} result item(s) returned.", "success")
    except subprocess.TimeoutExpired:
        with TASKS_LOCK:
            TASKS[task_id]["status"] = "failed"
            TASKS[task_id]["finished_at"] = now()
        emit(task_id, "Username scan timed out after 10 minutes.", "error")
    except Exception as exc:
        with TASKS_LOCK:
            TASKS[task_id]["status"] = "failed"
            TASKS[task_id]["finished_at"] = now()
        emit(task_id, f"Scan failed: {type(exc).__name__}: {exc}", "error")
    save_task(task_id)

def valid_target(kind, target):
    if not target or len(target) > 320 or any(ord(c) < 32 for c in target):
        return False
    if kind == "email":
        return bool(re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", target))
    if kind == "phone":
        return bool(re.fullmatch(r"\+?[0-9][0-9\s().-]{6,}", target))
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", target))

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "app": "My-OSINT Desktop", "time": now()})

@app.post("/api/scans")
def start_scan():
    data = request.get_json(silent=True) or {}
    kind = str(data.get("kind", "")).lower()
    target = str(data.get("target", "")).strip()
    if kind not in {"email", "phone", "username"}:
        return jsonify({"error": "Choose email, phone, or username."}), 400
    if not valid_target(kind, target):
        hint = {"email":"Enter a valid email address.", "phone":"Enter a phone number with country code, e.g. +919876543210.", "username":"Use 1–80 letters, digits, dots, underscores or hyphens."}[kind]
        return jsonify({"error": hint}), 400
    task_id = uuid.uuid4().hex
    task = {"id": task_id, "kind": kind, "target": target, "status": "queued",
            "started_at": now(), "finished_at": None, "updated_at": now(),
            "logs": [], "results": []}
    with TASKS_LOCK:
        TASKS[task_id] = task
    save_task(task_id)
    threading.Thread(target=run_task, args=(task_id,), daemon=True).start()
    return jsonify({"id": task_id, "status": "queued"}), 202

@app.get("/api/scans/<task_id>")
def scan_status(task_id):
    with TASKS_LOCK:
        t = TASKS.get(task_id)
        if t:
            return jsonify({**t, "logs": list(t["logs"]), "results": list(t["results"])})
    with db() as con:
        row = con.execute("SELECT * FROM scans WHERE id=?", (task_id,)).fetchone()
    if not row:
        return jsonify({"error": "Scan not found."}), 404
    return jsonify({"id":row["id"], "kind":row["kind"], "target":row["target"],
        "status":row["status"], "started_at":row["started_at"], "finished_at":row["finished_at"],
        "results":json.loads(row["result_json"]), "logs":json.loads(row["logs_json"])})

@app.get("/api/history")
def history():
    with db() as con:
        rows = con.execute("SELECT id,kind,target,status,started_at,finished_at FROM scans ORDER BY started_at DESC LIMIT 50").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/scans/<task_id>/export")
def export_scan(task_id):
    with TASKS_LOCK:
        t = TASKS.get(task_id)
        if t:
            payload = {**t, "logs": list(t["logs"]), "results": list(t["results"])}
        else:
            with db() as con:
                row = con.execute("SELECT * FROM scans WHERE id=?", (task_id,)).fetchone()
            if not row:
                abort(404)
            payload = {"id":row["id"],"kind":row["kind"],"target":row["target"],"status":row["status"],
                       "started_at":row["started_at"],"finished_at":row["finished_at"],
                       "results":json.loads(row["result_json"]),"logs":json.loads(row["logs_json"])}
    from flask import Response
    return Response(json.dumps(payload, indent=2, ensure_ascii=False),
                    mimetype="application/json",
                    headers={"Content-Disposition": f'attachment; filename="myosint-{task_id[:8]}.json"'})

@app.errorhandler(500)
def server_error(_):
    return jsonify({"error":"Internal server error. Check the terminal running My-OSINT Desktop."}), 500

init_db()

if __name__ == "__main__":
    # Local-only by default. Do not expose publicly without authentication and hardening.
    app.run(host=os.environ.get("MYOSINT_HOST", "127.0.0.1"),
            port=int(os.environ.get("MYOSINT_PORT", "5050")), debug=False, threaded=True)
