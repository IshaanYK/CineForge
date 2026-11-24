import urllib.request
import json
import time

payload = {
    "raw_video_filename": "340e1ef530_WhatsApp Video 2026-10-04 at 10.32.39.mp4",
    "prompt": "Clean edit, preserve original rhythm, master audio cleanly",
    "preset": "viral_short",
    "aspect_ratio": "9:16",
    "captions_enabled": True,
    "music_mode": "auto",
    "cut_mode": "ai_smart"
}

req = urllib.request.Request(
    "http://127.0.0.1:8080/api/process",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print("Started job:", res)
    job_id = res["job_id"]

for i in range(45):
    time.sleep(2)
    with urllib.request.urlopen(f"http://127.0.0.1:8080/api/status/{job_id}") as sresp:
        status_data = json.loads(sresp.read().decode("utf-8"))
        pct = status_data.get("progress")
        msg = status_data.get("status_message")
        print(f"[{pct}%] {msg}")
        if status_data.get("status") == "completed":
            print("SUCCESS! Result:", status_data.get("result"))
            break
        elif status_data.get("status") == "failed":
            print("FAILED! Error:", status_data.get("error"))
            break
