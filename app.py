"""
CINEFORGE AI - Master FastAPI Server & Agent Engine
Hosts the local AI Video Editing workstation with real-time job orchestration,
byte-range video streaming, and Gemini 2.5 / local model routing.
"""

import os
import sys
import uuid
import time
import shutil
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional

import json
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    UPLOADS_DIR, EXPORTS_DIR, STATIC_DIR, PRESETS,
    DEFAULT_GEMINI_MODEL, GEMINI_PROXY_URL
)
from video_pipeline import process_video_autonomous

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cineforge.server")

def ensure_proxy_running() -> bool:
    """Ensures the B1 Gemini Web2API proxy is running on localhost:8081."""
    import urllib.request
    import subprocess
    try:
        with urllib.request.urlopen("http://127.0.0.1:8081/v1/models", timeout=2) as resp:
            if resp.status == 200:
                logger.info("⚡ Gemini B1 Web2API Proxy is verified active on http://127.0.0.1:8081")
                return True
    except Exception:
        pass

    proxy_script = BASE_DIR / "gemini-web2api" / "gemini_web2api.py"
    if proxy_script.exists():
        logger.info(f"Auto-spawning Gemini B1 Proxy from {proxy_script}...")
        try:
            subprocess.Popen(
                [sys.executable, str(proxy_script), "--port", "8081"],
                cwd=str(proxy_script.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            time.sleep(2.5)
            logger.info("⚡ Gemini B1 Proxy spawned successfully on http://127.0.0.1:8081")
            return True
        except Exception as e:
            logger.warning(f"Failed to auto-spawn proxy: {e}")
    return False

app = FastAPI(title="CineForge AI - Autonomous Video Editor", version="1.0.0")

@app.on_event("startup")
async def on_startup():
    ensure_proxy_running()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory Job State Store
JOBS: Dict[str, Dict[str, Any]] = {}

class ProcessRequest(BaseModel):
    raw_video_filename: str
    prompt: Optional[str] = ""
    preset: Optional[str] = "viral_short"
    aspect_ratio: Optional[str] = "auto"
    captions_enabled: Optional[bool] = True
    subtitle_lang: Optional[str] = "auto_en_hi"
    subtitle_style: Optional[str] = "hormozi"
    progress_bar: Optional[bool] = True
    hook_flash: Optional[bool] = True
    music_mode: Optional[str] = "auto"
    cut_mode: Optional[str] = "ai_smart"
    gemini_api_key: Optional[str] = ""
    gemini_proxy: Optional[str] = ""

# Mount Static Assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>CineForge AI is initializing...</h1>", status_code=200)
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/presets")
async def get_presets():
    return JSONResponse(PRESETS)

@app.get("/api/proxy/status")
async def get_proxy_status():
    import urllib.request
    try:
        req = urllib.request.Request("http://127.0.0.1:8081/v1/models")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return JSONResponse({
                "online": True,
                "proxy_url": "http://127.0.0.1:8081/v1/chat/completions",
                "models": [m["id"] for m in data.get("data", [])]
            })
    except Exception as e:
        return JSONResponse({
            "online": False,
            "error": str(e),
            "proxy_url": "http://127.0.0.1:8081/v1/chat/completions"
        })

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload raw video file into the studio uploads repository."""
    try:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"]:
            raise HTTPException(status_code=400, detail="Unsupported video format.")

        safe_uuid = uuid.uuid4().hex[:10]
        stored_filename = f"{safe_uuid}_{file.filename}"
        dest_path = UPLOADS_DIR / stored_filename

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size_mb = round(dest_path.stat().st_size / (1024 * 1024), 2)
        logger.info(f"Uploaded: {stored_filename} ({file_size_mb} MB)")

        return JSONResponse({
            "success": True,
            "filename": stored_filename,
            "original_name": file.filename,
            "size_mb": file_size_mb,
            "path": str(dest_path)
        })
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_job_thread(
    job_id: str,
    video_path: str,
    prompt: str,
    preset: str,
    api_key: str,
    proxy_url: str,
    aspect_ratio: str = "auto",
    captions_enabled: bool = True,
    music_mode: str = "auto",
    cut_mode: str = "ai_smart",
    subtitle_lang: str = "auto_en_hi",
    subtitle_style: str = "hormozi",
    progress_bar: bool = True,
    hook_flash: bool = True
):
    """Executes the autonomous AI video pipeline in a worker thread."""
    def notify(pct: int, msg: str):
        if job_id in JOBS:
            JOBS[job_id]["progress"] = pct
            JOBS[job_id]["status_message"] = msg
            JOBS[job_id]["logs"].append({
                "time": round(time.time() - JOBS[job_id]["start_time"], 1),
                "pct": pct,
                "msg": msg
            })
            logger.info(f"[{job_id}] [{pct}%] {msg}")

    try:
        notify(5, "Worker thread spawned. Starting silence & speech detection...")
        result = process_video_autonomous(
            raw_video_path=video_path,
            user_prompt=prompt,
            preset_id=preset,
            api_key=api_key,
            proxy_url=proxy_url,
            aspect_ratio=aspect_ratio,
            captions_enabled=captions_enabled,
            subtitle_lang=subtitle_lang,
            subtitle_style=subtitle_style,
            progress_bar=progress_bar,
            hook_flash=hook_flash,
            music_mode=music_mode,
            cut_mode=cut_mode,
            progress_callback=notify
        )
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["progress"] = 100
        JOBS[job_id]["result"] = result
        JOBS[job_id]["status_message"] = "Render Complete! Master file ready."
    except Exception as e:
        logger.error(f"Job {job_id} error: {e}", exc_info=True)
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
        notify(JOBS[job_id]["progress"], f"PIPELINE ERROR: {str(e)}")

@app.post("/api/process")
async def trigger_process(req: ProcessRequest, background_tasks: BackgroundTasks):
    """Triggers the autonomous editing agent on an uploaded video."""
    video_path = UPLOADS_DIR / req.raw_video_filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Raw video file not found on server.")

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    JOBS[job_id] = {
        "job_id": job_id,
        "filename": req.raw_video_filename,
        "preset": req.preset,
        "prompt": req.prompt,
        "status": "processing",
        "progress": 2,
        "status_message": "Queued in CineForge AI Director engine...",
        "start_time": time.time(),
        "logs": [],
        "result": None,
        "error": None
    }

    # Start thread
    t = threading.Thread(
        target=run_job_thread,
        args=(
            job_id,
            str(video_path),
            req.prompt,
            req.preset,
            req.gemini_api_key,
            req.gemini_proxy,
            req.aspect_ratio,
            req.captions_enabled,
            req.music_mode,
            req.cut_mode,
            req.subtitle_lang or "auto_en_hi",
            req.subtitle_style or "hormozi",
            req.progress_bar if req.progress_bar is not None else True,
            req.hook_flash if req.hook_flash is not None else True
        ),
        daemon=True
    )
    t.start()

    return JSONResponse({
        "success": True,
        "job_id": job_id,
        "message": "AI Director has taken over editing."
    })

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found.")
    job = JOBS[job_id]
    return JSONResponse(job)

@app.get("/api/stream/upload/{filename}")
async def stream_upload_video(filename: str):
    """Stream uploaded raw video with byte-range headers."""
    video_path = UPLOADS_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found.")
    return FileResponse(str(video_path), media_type="video/mp4")

@app.get("/api/stream/export/{filename}")
async def stream_export_video(filename: str):
    """Stream edited final video with byte-range headers."""
    video_path = EXPORTS_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Rendered video not found.")
    return FileResponse(str(video_path), media_type="video/mp4")

@app.get("/api/download/{filename}")
async def download_video(filename: str):
    """Force download the mastered MP4 file."""
    video_path = EXPORTS_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Export not found.")
    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"============================================================")
    print(f"  🎬 CINEFORGE AI - AUTONOMOUS VIDEO STUDIO RUNNING")
    print(f"  🌐 URL: http://127.0.0.1:{port}")
    print(f"  📁 Uploads: {UPLOADS_DIR}")
    print(f"  📁 Exports: {EXPORTS_DIR}")
    print(f"============================================================")
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False)
