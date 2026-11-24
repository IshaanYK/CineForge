import whisper
import json
import urllib.request
import os

print("[1] Loading Whisper model...")
model = whisper.load_model("base")

audio_file = r"D:\CineForge\uploads\test_audio_extract.wav"
print(f"[2] Transcribing {audio_file} with Hindi/Sanskrit domain prompt...")
res = model.transcribe(
    audio_file,
    language="hi",
    initial_prompt="सनातन धर्म, मंत्र, श्लोक, संतान गोपाल, पूजा, विधि, भक्ति, ॐ, भगवान"
)
raw_text = res.get("text", "").strip()
print("RAW WHISPER HINDI TEXT:", raw_text)

# Segments
segments = res.get("segments", [])
for s in segments:
    print(f"  [{s['start']:.1f}s -> {s['end']:.1f}s]: {s['text']}")

# Now query Gemini 2.5 Pro via local proxy
print("\n[3] Calling Gemini 2.5 Pro via B1 Proxy on 8081 for spiritual restoration...")
prompt = f"""You are a master Sanskrit/Hindi linguist and professional YouTube content producer.
A creator uploaded an Indian devotional / mantra chanting video.
The automated speech recognition returned this phonetic transcript:
\"{raw_text}\"

Task:
1. Identify the exact Hindi or Sanskrit mantra / spiritual guidance the speaker is chanting or reciting.
2. Provide the corrected, holy, authentic Hindi Devanagari text for video captions.
3. Provide a high-CTR YouTube Shorts Title & Hook in Hindi/English.
4. Output JSON:
{{
  "is_devotional": true,
  "detected_topic": "...",
  "corrected_devanagari": "...",
  "english_meaning": "...",
  "youtube_shorts_title": "...",
  "viral_hook": "..."
}}
"""

payload = {
    "model": "gemini-2.5-pro",
    "messages": [{"role": "user", "content": prompt}],
    "response_format": {"type": "json_object"}
}

req = urllib.request.Request(
    "http://127.0.0.1:8081/v1/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        content = res_data["choices"][0]["message"]["content"]
        print("\n--- GEMINI 2.5 PRO SPIRITUAL RESTORATION ---")
        print(content)
except Exception as e:
    print("Gemini error:", e)

