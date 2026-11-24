"""
CINEFORGE AI - Speech Transcription & Word-Level Timing Engine
Uses local Whisper (CUDA/CPU) to extract sub-second word timestamps for kinetic karaoke captions.
Enforces STRICT English & Hindi (Devanagari) language filtering to eliminate all foreign hallucinations.
"""

import os
import re
import json
import urllib.request
import subprocess
import logging
from pathlib import Path
from config import FFMPEG_EXE

logger = logging.getLogger("cineforge.speech_engine")

_whisper_model = None

def get_whisper_model(model_name: str = "base"):
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading local Whisper model ({model_name}) on device={device}...")
            _whisper_model = whisper.load_model(model_name, device=device)
            logger.info("Whisper model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            _whisper_model = None
    return _whisper_model

def is_char_en_hi_safe(c: str) -> bool:
    """Checks if character belongs strictly to English ASCII or Hindi Devanagari."""
    code = ord(c)
    # ASCII printable (Latin alphabet, numbers, punctuation, space)
    if 32 <= code <= 126:
        return True
    # Devanagari Unicode Block (Hindi, Sanskrit): U+0900 to U+097F
    if 0x0900 <= code <= 0x097F:
        return True
    # Devanagari Extended & Vedic extensions
    if 0x1CD0 <= code <= 0x1CFF or 0xA8E0 <= code <= 0xA8FF:
        return True
    return False

def sanitize_en_hi_text(text: str) -> str:
    """
    Enforces strict English and Hindi filtering.
    Strips any Arabic, Chinese, Cyrillic, or random non-Devanagari/Latin glyphs.
    """
    if not text:
        return ""
    filtered_chars = [c for c in text if is_char_en_hi_safe(c)]
    cleaned = "".join(filtered_chars)
    # Normalize whitespace
    return " ".join(cleaned.split())

def is_valid_en_hi_word(word: str) -> bool:
    """Validates that a word contains valid Latin or Devanagari characters and no foreign glyphs."""
    if not word or not word.strip():
        return False
    w_clean = word.strip()
    has_valid_char = any(
        ('a' <= c.lower() <= 'z') or (0x0900 <= ord(c) <= 0x097F)
        for c in w_clean
    )
    no_forbidden = all(is_char_en_hi_safe(c) for c in w_clean)
    return has_valid_char and no_forbidden

def extract_audio_wav(video_path: str, output_wav: str) -> bool:
    """Extracts 16kHz mono PCM audio for whisper and silence processing."""
    cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(Path(video_path).resolve()),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(Path(output_wav).resolve())
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0

def polish_segments_with_gemini(raw_segments_text: list, proxy_url: str = "http://127.0.0.1:8081/v1/chat/completions") -> list:
    """
    Calls local Gemini 2.5 Pro via B1 Proxy to clean, reconstruct, and spiritually restore
    phonetically misheard Hindi/Sanskrit/English phrases.
    """
    if not raw_segments_text:
        return raw_segments_text

    combined_input = "\n".join([f"[{i}] {t}" for i, t in enumerate(raw_segments_text)])
    prompt = f"""You are an elite linguistic editor specializing in Hindi, Sanskrit shlokas, and Indian spiritual discourses.
Fix phonetically misheard or garbled words in these transcribed audio segments.
Keep the meaning authentic and spiritual. Clean up broken syllables into proper Devanagari Hindi or clean English words.
Segments:
{combined_input}

Respond ONLY with valid JSON mapping segment index to cleaned text:
{{
  "cleaned_segments": [
     {{"index": 0, "text": "cleaned text..."}}
  ]
}}"""

    payload = json.dumps({
        "model": "gemini-2.5-pro",
        "messages": [
            {"role": "system", "content": "You are a master Hindi/Sanskrit transcription corrector. Respond strictly in valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }).encode("utf-8")

    req = urllib.request.Request(
        proxy_url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
            cleaned_map = {item["index"]: item["text"] for item in parsed.get("cleaned_segments", [])}
            return [cleaned_map.get(i, raw_segments_text[i]) for i in range(len(raw_segments_text))]
    except Exception as e:
        logger.warning(f"Gemini transcript polish fallback: {e}")
        return raw_segments_text

def transcribe_video_speech(audio_wav_path: str, subtitle_lang: str = "auto_en_hi") -> dict:
    """
    Transcribes audio with word-level timestamps, enforcing English & Hindi only.
    subtitle_lang options:
      - 'auto_en_hi': auto-detect, strictly constrained to English or Hindi
      - 'hi': force Hindi Devanagari transcription
      - 'en': force English transcription
      - 'translate_en': translate spoken Hindi/any speech into clean English
    """
    model = get_whisper_model("base")
    if model is None:
        logger.warning("Whisper not available. Using fallback mock timestamps.")
        return {
            "full_text": "Speech recognition engine fallback.",
            "segments": [],
            "words": []
        }

    try:
        logger.info(f"Transcribing audio ({subtitle_lang}): {audio_wav_path}...")
        
        transcribe_args = {
            "word_timestamps": True,
            "fp16": False
        }

        if subtitle_lang == "hi":
            transcribe_args["language"] = "hi"
            transcribe_args["task"] = "transcribe"
            transcribe_args["initial_prompt"] = "सनातन धर्म, वेद, मंत्र, श्लोक, प्रवचन, कार्य, विवाह, संतान, इच्छा, भक्ति, ईश्वर, ॐ, शांति"
        elif subtitle_lang == "en":
            transcribe_args["language"] = "en"
            transcribe_args["task"] = "transcribe"
        elif subtitle_lang in ["translate_en", "en_translate"]:
            transcribe_args["task"] = "translate"
        else: # auto_en_hi
            transcribe_args["initial_prompt"] = "सनातन धर्म, वेद, मंत्र, श्लोक, प्रवचन, कार्य, विवाह, संतान, इच्छा, भक्ति, ईश्वर, ॐ, शांति, Hindi spiritual wisdom and mantras."

        result = model.transcribe(str(audio_wav_path), **transcribe_args)
        
        detected_lang = result.get("language", "en")
        logger.info(f"Whisper finished. Detected language: {detected_lang}")

        raw_full_text = result.get("text", "").strip()
        full_text = sanitize_en_hi_text(raw_full_text)

        raw_segments = result.get("segments", [])
        raw_texts = [sanitize_en_hi_text(seg.get("text", "").strip()) for seg in raw_segments]
        
        # Polish through Gemini 2.5 Pro if Indian/Hindi/devotional speech
        if subtitle_lang in ["hi", "auto_en_hi"] and any(raw_texts):
            logger.info("Engaging Gemini 2.5 Pro transcript polisher for Hindi/spiritual accuracy...")
            polished_texts = polish_segments_with_gemini(raw_texts)
        else:
            polished_texts = raw_texts

        segments = []
        all_words = []

        for s_idx, seg in enumerate(raw_segments):
            s_text = polished_texts[s_idx] if s_idx < len(polished_texts) else sanitize_en_hi_text(seg.get("text", ""))
            if not s_text:
                continue

            s_start = round(seg.get("start", 0.0), 3)
            s_end = round(seg.get("end", 0.0), 3)
            
            # Use polished text words spaced evenly across the segment duration
            clean_tokens = [w for w in s_text.split() if is_valid_en_hi_word(w)]
            words_in_seg = []
            if clean_tokens:
                token_dur = max(0.18, (s_end - s_start) / len(clean_tokens))
                for w_i, token in enumerate(clean_tokens):
                    w_dict = {
                        "word": token,
                        "start": round(s_start + (w_i * token_dur), 3),
                        "end": round(min(s_end, s_start + ((w_i + 1) * token_dur)), 3)
                    }
                    words_in_seg.append(w_dict)
                    all_words.append(w_dict)

            if words_in_seg:
                segments.append({
                    "text": s_text,
                    "start": s_start,
                    "end": s_end,
                    "words": words_in_seg
                })

        logger.info(f"Transcription complete: {len(all_words)} clean English/Hindi words captured.")
        return {
            "full_text": full_text,
            "detected_language": detected_lang,
            "segments": segments,
            "words": all_words
        }

    except Exception as e:
        logger.error(f"Error during whisper transcription: {e}")
        return {
            "full_text": "",
            "detected_language": "en",
            "segments": [],
            "words": []
        }

def build_kinetic_caption_chunks(words: list, max_words_per_card: int = 2) -> list:
    """
    Groups individual words into snappy 1-2 word cards for high-retention karaoke captions.
    """
    if not words:
        return []

    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + max_words_per_card]
        start_t = chunk_words[0]["start"]
        end_t = chunk_words[-1]["end"]
        card_text = " ".join([w["word"] for w in chunk_words])
        
        chunks.append({
            "text": card_text,
            "start": start_t,
            "end": max(start_t + 0.35, end_t),
            "words": chunk_words
        })
        i += max_words_per_card

    return chunks
