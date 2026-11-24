import urllib.request
import json
import time

payload = {
    "raw_video_filename": "test_raw.mp4",
    "prompt": "Viral short with punch zooms and electric cyan pills",
    "preset": "viral_short",
    "gemini_api_key": "",
    "gemini_proxy": "http://127.0.0.1:8081/v1/chat/completions"
}

req = urllib.request.Request(
    "http://127.0.0.1:8080/api/process",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    job = json.loads(resp.read().decode("utf-8"))
print("Dispatched Job ID:", job["job_id"])

job_id = job["job_id"]
for _ in range(40):
    time.sleep(2)
    with urllib.request.urlopen(f"http://127.0.0.1:8080/api/status/{job_id}") as s_resp:
        status = json.loads(s_resp.read().decode("utf-8"))
        pct = status.get("progress", 0)
        msg = status.get("status_message", "")
        print(f"[{pct}%] {msg}")
        if status.get("status") == "completed":
            print("\n✨ PIPELINE SUCCESS WITH B1 GEMINI PROXY!")
            res = status.get("result", {})
            print("Title:", res.get("title"))
            print("EDL Notes:", res.get("edl", {}).get("ai_director_notes"))
            print("Output File:", res.get("output_filename"))
            break
        elif status.get("status") == "failed":
            print("\n❌ Pipeline failed:", status.get("error"))
            break
