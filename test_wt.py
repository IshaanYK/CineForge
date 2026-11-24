import whisper
model = whisper.load_model("base")
res = model.transcribe(r"D:\CineForge\uploads\b53_audio.wav", language="hi", word_timestamps=False)
print("WITHOUT word_timestamps:")
print(res.get("text"))
for seg in res.get("segments", []):
    print(f"[{seg.get('start', 0):.1f} - {seg.get('end', 0):.1f}] {seg.get('text')}")

