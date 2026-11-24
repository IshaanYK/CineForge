import cv2
import numpy as np
import subprocess
import json
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Paths
INPUT_VIDEO = r"D:\CineForge\uploads\1c0ee7027a_2.mp4"
OUTPUT_MP4 = r"D:\CineForge\exports\master_cinematic_edit.mp4"
SFX_DIR = Path(r"D:\CineForge\assets\sfx")
BROLL_DIR = Path(r"D:\CineForge\assets\broll")

print("[1] Opening video and analyzing dimensions...")
cap = cv2.VideoCapture(INPUT_VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
raw_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
raw_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
duration = total_frames / fps
print(f"Video Info: {raw_w}x{raw_h} @ {fps:.1f} FPS, {total_frames} frames ({duration:.2f}s)")

out_w, out_h = 1080, 1920

# 1. Define Multi-Cam Camera Cuts & Zooms (Every 3-4s a new dynamic shot!)
shots = [
    {"start": 0.0, "end": 3.5, "scale": 1.48, "shot_name": "TIGHT HOOK PUNCH-IN"},
    {"start": 3.5, "end": 7.5, "scale": 1.25, "shot_name": "MEDIUM SHOT"},
    {"start": 7.5, "end": 12.0, "scale": 1.42, "shot_name": "CLOSE EMOTION ZOOM", "show_broll": True},
    {"start": 12.0, "end": 18.0, "scale": 1.25, "shot_name": "MEDIUM SHOT"},
    {"start": 18.0, "end": 999.0, "scale": 1.45, "shot_name": "CLIMAX TIGHT PUNCH-IN"}
]

# 2. Timed SFX Hits
sfx_hits = [
    {"time": 0.0, "sound": "hook_impact.wav", "volume": 0.65},
    {"time": 3.5, "sound": "whoosh.wav", "volume": 0.40},
    {"time": 7.5, "sound": "whoosh.wav", "volume": 0.45},
    {"time": 12.0, "sound": "whoosh.wav", "volume": 0.40},
    {"time": 18.0, "sound": "tech_chirp.wav", "volume": 0.35}
]

# 3. Audio Mixing
print("[2] Mixing Multi-Track Soundbed with Voice + SFX + Ambient Music...")
temp_voice_wav = r"D:\CineForge\exports\temp_raw_voice.wav"
subprocess.run(["ffmpeg", "-y", "-i", INPUT_VIDEO, "-vn", "-ar", "44100", "-ac", "2", temp_voice_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

temp_mixed_audio = r"D:\CineForge\exports\temp_master_soundbed.wav"

# Filter complex for multitrack audio
filter_inputs = ["-i", temp_voice_wav]
filter_parts = ["[0:a]loudnorm=I=-14:LRA=7:tp=-1.5,aformat=sample_rates=44100:channel_layouts=stereo[voice]"]
mix_sources = ["[voice]"]
input_idx = 1

bg_music = SFX_DIR / "cinematic_tension.wav"
if bg_music.exists():
    filter_inputs.extend(["-i", str(bg_music)])
    filter_parts.append(f"[{input_idx}:a]aloop=loop=-1:size=2e+09,volume=0.08,atrim=0:{duration:.2f},aformat=sample_rates=44100:channel_layouts=stereo[bg]")
    mix_sources.append("[bg]")
    input_idx += 1

for sfx in sfx_hits:
    s_path = SFX_DIR / sfx["sound"]
    if s_path.exists():
        t_ms = int(sfx["time"] * 1000)
        vol = sfx["volume"]
        filter_inputs.extend(["-i", str(s_path)])
        filter_parts.append(f"[{input_idx}:a]volume={vol:.2f},adelay={t_ms}|{t_ms},aformat=sample_rates=44100:channel_layouts=stereo[sfx{input_idx}]")
        mix_sources.append(f"[sfx{input_idx}]")
        input_idx += 1

filter_complex = ";".join(filter_parts) + f";{''.join(mix_sources)}amix=inputs={len(mix_sources)}:duration=first:dropout_transition=2[aout]"
cmd_audio = ["ffmpeg", "-y", *filter_inputs, "-filter_complex", filter_complex, "-map", "[aout]", "-c:a", "pcm_s16le", temp_mixed_audio]
subprocess.run(cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Audio Soundbed Mastered:", Path(temp_mixed_audio).exists())

# 4. Generate ASS Subtitles File
print("[3] Generating Flawless ASS Subtitles Stream...")
ass_content = f"""[Script Info]
Title: CineForge Master Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {out_w}
PlayResY: {out_h}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HormoziYellow,Nirmala UI,62,&H0000FFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:04.50,HormoziYellow,,0,0,150,,{{\\c&H00F0FF&}}संसार में{{\\c&H00FFFF&}} आपको अनेक इच्छाएँ हैं
Dialogue: 0,0:00:04.50,0:00:09.50,HormoziYellow,,0,0,150,,कार्य, विवाह और {{\\c&H00F0FF&}}संतान{{\\c&H00FFFF&}}
Dialogue: 0,0:00:09.50,0:00:15.50,HormoziYellow,,0,0,150,,पर अंत में देखिए... {{\\c&H00F0FF&}}कितने अपने हैं?{{\\c&H00FFFF&}}
Dialogue: 0,0:00:15.50,0:00:27.50,HormoziYellow,,0,0,150,,ईश्वर और आत्म-चिंतन ही {{\\c&H00F0FF&}}सत्य{{\\c&H00FFFF&}} है
"""
ass_path = r"D:\CineForge\exports\temp_subtitles.ass"
with open(ass_path, "w", encoding="utf-8") as f:
    f.write(ass_content)

# 5. Load B-Roll Asset
broll_file = BROLL_DIR / "future_city.jpg"
broll_card = None
if broll_file.exists():
    b_raw = Image.open(broll_file).convert("RGBA")
    b_card_w, b_card_h = 920, 500
    b_resized = b_raw.resize((b_card_w, b_card_h), Image.Resampling.LANCZOS)
    b_mask = Image.new("L", (b_card_w, b_card_h), 0)
    ImageDraw.Draw(b_mask).rounded_rectangle([0, 0, b_card_w, b_card_h], radius=24, fill=255)
    broll_card = (b_resized, b_mask, b_card_w, b_card_h)

# 6. Render Video with Multi-Cam Jump Cuts, B-Roll, Color Grade, and Subtitles
print("[4] Executing Visual Production Pipeline via FFmpeg Pipe...")
temp_raw_video = r"D:\CineForge\exports\temp_visual_pass.mp4"

pipe_cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{out_w}x{out_h}",
    "-pix_fmt", "bgr24",
    "-r", str(int(fps)),
    "-i", "-",
    "-i", temp_mixed_audio,
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "17",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "320k",
    "-shortest",
    temp_raw_video
]

pipe = subprocess.Popen(pipe_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

f_idx = 0
start_render = time.time()

# Precompute vignette mask
rows, cols = out_h, out_w
kx = cv2.getGaussianKernel(cols, cols / 1.5)
ky = cv2.getGaussianKernel(rows, rows / 1.5)
vignette_mask = (ky * kx.T)
vignette_mask = (vignette_mask / vignette_mask.max()) * 0.40 + 0.60 # subtle 40% vignette

while True:
    ret, frame_bgr = cap.read()
    if not ret:
        break

    curr_t = f_idx / fps

    # Find current camera cut & zoom
    current_scale = 1.35
    show_broll = False
    for shot in shots:
        if shot["start"] <= curr_t < shot["end"]:
            current_scale = shot["scale"]
            show_broll = shot.get("show_broll", False)
            break

    # Dynamic Face-Centered Crop
    scale = max(out_w / raw_w, out_h / raw_h) * current_scale
    rw = int(np.ceil(raw_w * scale))
    rh = int(np.ceil(raw_h * scale))
    resized = cv2.resize(frame_bgr, (rw, rh), interpolation=cv2.INTER_LINEAR)
    cx = rw // 2
    cy = int(rh * 0.62)
    y1 = max(0, min(rh - out_h, cy - out_h // 2))
    x1 = max(0, min(rw - out_w, cx - out_w // 2))
    frame_cropped = resized[y1:y1 + out_h, x1:x1 + out_w]

    # Color grading: +15% saturation & vignette
    hsv = cv2.cvtColor(frame_cropped, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.15, 0, 255)
    graded = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    for c_i in range(3):
        graded[:, :, c_i] = (graded[:, :, c_i] * vignette_mask).astype(np.uint8)

    # Opening Hook Headline Banner (0.0s - 3.5s)
    if curr_t <= 3.5:
        # Floating Cyan Badge
        bx = (out_w - 320) // 2
        cv2.rectangle(graded, (bx, 70), (bx + 320, 120), (0, 240, 255), -1)
        cv2.putText(graded, "VEDIC TRUTH", (bx + 40, 105), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 0), 2)

    # Thematic B-Roll Picture-in-Picture Card (7.5s - 12.0s)
    if show_broll and broll_card:
        b_img, b_mask, bw, bh = broll_card
        bx = (out_w - bw) // 2
        by = 140
        # Blend onto frame
        b_np = np.array(b_img)
        roi = graded[by:by + bh, bx:bx + bw]
        mask_np = np.array(b_mask) / 255.0
        for c in range(3):
            roi[:, :, c] = (roi[:, :, c] * (1.0 - mask_np) + b_np[:, :, 2 - c] * mask_np).astype(np.uint8)
        # Glowing border around card
        cv2.rectangle(graded, (bx, by), (bx + bw, by + bh), (0, 240, 255), 3)

    # Neon Scrub Progress Bar at bottom (7px)
    progress_w = int(out_w * (curr_t / duration))
    cv2.rectangle(graded, (0, out_h - 7), (progress_w, out_h), (0, 240, 255), -1)

    pipe.stdin.write(graded.tobytes())
    f_idx += 1

cap.release()
pipe.stdin.close()
pipe.wait()
print(f"Visual pass rendered in {time.time() - start_render:.1f}s.")

# 7. Final Subtitle Pass with FFmpeg LibASS
print("[5] Burning Flawless Indic ASS Subtitles Stream...")
escaped_ass = ass_path.replace('\\', '/').replace(':', '\\:')
cmd_final = [
    "ffmpeg", "-y",
    "-i", temp_raw_video,
    "-vf", f"subtitles='{escaped_ass}'",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "17",
    "-c:a", "copy",
    "-movflags", "+faststart",
    OUTPUT_MP4
]
subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"Master Export Complete: {OUTPUT_MP4} (Size: {Path(OUTPUT_MP4).stat().st_size} bytes)")

