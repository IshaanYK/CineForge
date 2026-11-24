"""
CINEFORGE AI - Configuration & Studio Presets
Author: Ishaan Sen (Agent ARISE)
Design System: design-md-linear.app (Obsidian #010102, Cyan #00F0FF, Laser Yellow #FFE600)
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
ASSETS_DIR = BASE_DIR / "assets"
SFX_DIR = ASSETS_DIR / "sfx"
MUSIC_DIR = ASSETS_DIR / "music"
STATIC_DIR = BASE_DIR / "static"

for d in [UPLOADS_DIR, EXPORTS_DIR, ASSETS_DIR, SFX_DIR, MUSIC_DIR, STATIC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# FFmpeg Executable Resolution
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = "ffmpeg"

# Fonts (Full Unicode, Latin & Devanagari / Indic Support)
WIN_FONTS = Path(r"C:\Windows\Fonts")
IMPACT_FONT = WIN_FONTS / "impact.ttf"
ARIAL_BOLD = WIN_FONTS / "arialbd.ttf"
NIRMALA_FONT = WIN_FONTS / "Nirmala.ttc"
SEGOE_BOLD = WIN_FONTS / "segoeuib.ttf"
CONSOLAS_BOLD = WIN_FONTS / "consolab.ttf"

# AI Brain Settings (Gemini B1 Web2API Proxy - Zero Cost)
GEMINI_PROXY_URL = os.getenv("GEMINI_PROXY_URL") or "http://127.0.0.1:8081/v1/chat/completions"
DEFAULT_MODEL = "gemini-2.5-pro"
DEFAULT_GEMINI_MODEL = DEFAULT_MODEL
GEMINI_API_KEY = ""
PROXY_DIR = BASE_DIR / "gemini-web2api"

# Studio Presets
STUDIO_PRESETS = {
    "viral_short": {
        "id": "viral_short",
        "name": "⚡ Viral Short (Hormozi / Fireship Style)",
        "description": "Smart prompt/silence cuts, dynamic 1.15x punch zooms, kinetic subtitles, mirror-blur aspect fit, and speech normalization.",
        "aspect_ratio": "9:16",
        "resolution": [1080, 1920],
        "fit_mode": "mirror_blur",
        "silence_thresh_db": "auto",
        "silence_min_dur": 0.35,
        "punch_zoom": True,
        "zoom_scale": 1.15,
        "caption_style": "hormozi_kinetic",
        "sfx_enabled": False,
        "bg_music": None,
        "music_volume": 0.0,
        "color_grade": "vibrant_contrast"
    },
    "cinematic_doc": {
        "id": "cinematic_doc",
        "name": "🎬 Cinematic 16:9 (Vox / Aperture Style)",
        "description": "Aspect-fit widescreen framing with mirror blur background, natural pauses, -14 LUFS broadcast speech.",
        "aspect_ratio": "16:9",
        "resolution": [1920, 1080],
        "fit_mode": "mirror_blur",
        "silence_thresh_db": "auto",
        "silence_min_dur": 0.60,
        "punch_zoom": False,
        "zoom_scale": 1.05,
        "caption_style": "minimal_cinema",
        "sfx_enabled": False,
        "bg_music": None,
        "music_volume": 0.0,
        "color_grade": "cinematic_moody"
    },
    "clean_podcast": {
        "id": "clean_podcast",
        "name": "🎙️ Clean Talking Head (Original Aspect)",
        "description": "Preserves original resolution & aspect ratio, cuts pauses > 0.4s, normalizes speech to -14 LUFS, zero audio clash.",
        "aspect_ratio": "original",
        "fit_mode": "original",
        "silence_thresh_db": "auto",
        "silence_min_dur": 0.40,
        "punch_zoom": False,
        "caption_style": "clean_pill",
        "sfx_enabled": False,
        "bg_music": None,
        "color_grade": "natural_crisp"
    },
    "custom_prompt": {
        "id": "custom_prompt",
        "name": "🧠 Prompt-Driven Director (Gemini 2.5)",
        "description": "The AI Director cuts, structures, adds intro headline cards, and edits based on your exact prompt.",
        "aspect_ratio": "9:16",
        "resolution": [1080, 1920],
        "fit_mode": "mirror_blur",
        "silence_thresh_db": "auto",
        "silence_min_dur": 0.35,
        "punch_zoom": True,
        "caption_style": "hormozi_kinetic",
        "sfx_enabled": False,
        "bg_music": None,
        "color_grade": "vibrant_contrast"
    }
}

PRESETS = STUDIO_PRESETS
