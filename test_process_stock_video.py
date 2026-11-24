import urllib.request
import subprocess
from pathlib import Path

out_dir = Path(r"D:\CineForge\assets\broll_videos")
out_dir.mkdir(parents=True, exist_ok=True)

test_url = "https://upload.wikimedia.org/wikipedia/commons/f/f1/Sunrise_Timelapse_%2830174294051%29.webm"
dest_raw = out_dir / "temp_download.webm"
dest_vertical_mp4 = out_dir / "sunrise_timelapse_1080x1920.mp4"

print("Downloading Wikimedia video sample...")
req = urllib.request.Request(test_url, headers={'User-Agent': 'CineForgeAI/1.0'})
with urllib.request.urlopen(req, timeout=20) as resp, open(dest_raw, "wb") as f:
    f.write(resp.read())

print("Downloaded raw file:", dest_raw.stat().st_size, "bytes")

print("Processing into vertical 1080x1920 MP4 via FFmpeg...")
# Convert to 1080x1920 vertical crop, 30fps, 4s duration
cmd = [
    "ffmpeg", "-y",
    "-ss", "0",
    "-t", "4",
    "-i", str(dest_raw),
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "20",
    "-an",
    str(dest_vertical_mp4)
]
subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Finished! Output vertical stock video:", dest_vertical_mp4.exists(), dest_vertical_mp4.stat().st_size, "bytes")

