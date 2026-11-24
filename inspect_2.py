import sys
sys.path.append(r"D:\CineForge")
from speech_engine import transcribe_video_speech, extract_audio_wav

wav_p = r"D:\CineForge\uploads\b53_audio.wav"
extract_audio_wav(r"D:\CineForge\uploads\b53d65ee4f_2.mp4", wav_p)
t = transcribe_video_speech(wav_p)
print("Language:", t.get("language"))
print("Text:", t.get("text"))
for s in t.get("segments", []):
    print(f"[{s.get('start', 0):.1f}s - {s.get('end', 0):.1f}s] {s.get('text')}")

