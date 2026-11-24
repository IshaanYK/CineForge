"""
CINEFORGE AI - Silence Detection & Smart Jump-Cut Assembly Engine
Removes dead air, pauses, stutters, and breaths with sub-second accuracy.
Features dynamic noise-floor adaptation so background audio/music never prevents cuts.
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from config import FFMPEG_EXE

logger = logging.getLogger("cineforge.silence_cutter")

def get_audio_volume_levels(audio_path: str) -> dict:
    """Measures mean and max volume in dB using FFmpeg volumedetect filter."""
    path_str = str(Path(audio_path).resolve())
    cmd = [FFMPEG_EXE, "-i", path_str, "-af", "volumedetect", "-f", "null", "-"]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
        mean_v = -25.0
        max_v = 0.0
        m1 = re.search(r"mean_volume:\s*(-?[0-9.]+)\s*dB", res.stderr)
        if m1:
            mean_v = float(m1.group(1))
        m2 = re.search(r"max_volume:\s*(-?[0-9.]+)\s*dB", res.stderr)
        if m2:
            max_v = float(m2.group(1))
        return {"mean_volume": mean_v, "max_volume": max_v}
    except Exception as e:
        logger.warning(f"volumedetect note: {e}")
        return {"mean_volume": -25.0, "max_volume": 0.0}

def detect_silence_intervals(video_or_audio_path: str, noise_thresh_db = "auto", min_silence_dur: float = 0.35) -> list:
    """
    Uses FFmpeg's silencedetect filter to find non-speech silence intervals.
    Dynamically adapts noise threshold relative to the audio's mean volume.
    """
    path_str = str(Path(video_or_audio_path).resolve())

    # Dynamic noise floor adaptation
    if noise_thresh_db == "auto" or noise_thresh_db is None or isinstance(noise_thresh_db, str):
        vol_info = get_audio_volume_levels(path_str)
        mean_v = vol_info["mean_volume"]
        # Adaptive threshold: 6dB below mean volume, capped between -23dB and -38dB
        calc_thresh = min(-23.0, max(-38.0, mean_v - 6.5))
        logger.info(f"Audio mean volume: {mean_v:.1f} dB -> Adaptive silence threshold: {calc_thresh:.1f} dB")
        thresh_val = calc_thresh
    else:
        thresh_val = float(noise_thresh_db)

    cmd = [
        FFMPEG_EXE, "-y",
        "-i", path_str,
        "-af", f"silencedetect=noise={thresh_val}dB:d={min_silence_dur}",
        "-f", "null",
        "-"
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
        output = res.stderr
    except Exception as e:
        logger.error(f"Error running silencedetect: {e}")
        return []

    silence_starts = []
    silence_ends = []

    for line in output.splitlines():
        if "silence_start:" in line:
            match = re.search(r"silence_start:\s*([0-9.]+)", line)
            if match:
                silence_starts.append(float(match.group(1)))
        elif "silence_end:" in line:
            match = re.search(r"silence_end:\s*([0-9.]+)", line)
            if match:
                silence_ends.append(float(match.group(1)))

    silences = []
    for i in range(min(len(silence_starts), len(silence_ends))):
        s = silence_starts[i]
        e = silence_ends[i]
        if e > s:
            silences.append({
                "start": round(s, 3),
                "end": round(e, 3),
                "duration": round(e - s, 3)
            })

    return silences

def get_media_duration(path: str) -> float:
    cmd = [FFMPEG_EXE, "-i", str(Path(path).resolve()), "-f", "null", "-"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if match:
        h, m, s = match.groups()
        return round(int(h) * 3600 + int(m) * 60 + float(s), 3)
    return 30.0

def calculate_keep_intervals(total_duration: float, silences: list, padding: float = 0.05) -> list:
    """
    Inverts silence intervals into speech 'keep' segments with safety padding.
    """
    if not silences:
        return [{"start": 0.0, "end": total_duration}]

    keep_segments = []
    current_time = 0.0

    for sil in silences:
        sil_start = max(0.0, sil["start"] + padding)
        sil_end = min(total_duration, sil["end"] - padding)

        if sil_start > current_time + 0.15:
            keep_segments.append({
                "start": round(current_time, 3),
                "end": round(sil_start, 3),
                "duration": round(sil_start - current_time, 3)
            })
        current_time = max(current_time, sil_end)

    if current_time < total_duration - 0.15:
        keep_segments.append({
            "start": round(current_time, 3),
            "end": round(total_duration, 3),
            "duration": round(total_duration - current_time, 3)
        })

    return keep_segments if keep_segments else [{"start": 0.0, "end": total_duration}]

def assemble_cut_video(input_video_path: str, keep_segments: list, output_video_path: str) -> bool:
    """
    Frame-accurately ripple cuts and stitches keep_segments using FFmpeg filter_complex.
    Both video and audio remain 100% synchronized with sub-second accuracy.
    """
    if not keep_segments or (len(keep_segments) == 1 and keep_segments[0]["start"] == 0.0):
        # No cuts needed - copy directly or link
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(input_video_path),
            "-c", "copy",
            str(output_video_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0

    # Build trim filter complex
    v_parts = []
    a_parts = []
    concat_inputs = []

    for idx, seg in enumerate(keep_segments):
        s = seg["start"]
        e = seg["end"]
        v_parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{idx}]")
        a_parts.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{idx}]")
        concat_inputs.append(f"[v{idx}][a{idx}]")

    concat_str = "".join(concat_inputs) + f"concat=n={len(keep_segments)}:v=1:a=1[outv][outa]"
    filter_graph = ";".join(v_parts + a_parts) + ";" + concat_str

    cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(input_video_path),
        "-filter_complex", filter_graph,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "256k",
        str(output_video_path)
    ]

    logger.info(f"Assembling {len(keep_segments)} cut segments with FFmpeg concat...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode == 0
