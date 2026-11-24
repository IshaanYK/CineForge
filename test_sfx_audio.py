import wave
import struct
from pathlib import Path

SFX_DIR = Path(r"D:\CineForge\assets\sfx")

def mix_multitrack_audio_with_sfx(voice_wav_path: str, sfx_events: list, bg_music_path: str, output_wav_path: str):
    """
    Mixes voice audio with SFX hits and subtle background music.
    - Voice normalized to clear prominence (volume = 1.0)
    - SFX hits timed to cuts and hooks
    - Background music ducked to -20 dB (volume = 0.10)
    """
    with wave.open(voice_wav_path, 'r') as vw:
        sr = vw.getframerate()
        n_channels = vw.getnchannels()
        sampwidth = vw.getsampwidth()
        n_frames = vw.getnframes()
        v_data = vw.readframes(n_frames)

    duration = n_frames / sr
    target_samples = int(duration * 44100)
    target_sr = 44100
    
    # We will write out at 44100 Hz 16-bit mono
    # Use ffmpeg for ultra-reliable high-quality resampling and mixing
    import subprocess
    
    filter_inputs = ["-i", voice_wav_path]
    filter_parts = ["[0:a]loudnorm=I=-14:LRA=7:tp=-1.5,aformat=sample_rates=44100:channel_layouts=stereo[voice]"]
    mix_sources = ["[voice]"]
    
    input_idx = 1
    
    # 1. Background Music if exists
    if bg_music_path and Path(bg_music_path).exists():
        filter_inputs.extend(["-i", str(bg_music_path)])
        filter_parts.append(f"[{input_idx}:a]aloop=loop=-1:size=2e+09,volume=0.10,atrim=0:{duration:.2f},aformat=sample_rates=44100:channel_layouts=stereo[bg]")
        mix_sources.append("[bg]")
        input_idx += 1
        
    # 2. SFX Triggers (hook impact, whoosh, tech chirp)
    for sfx in sfx_events:
        sound_file = SFX_DIR / sfx.get("sound", "whoosh.wav")
        if sound_file.exists():
            t_ms = int(sfx.get("time", 0.0) * 1000)
            vol = sfx.get("volume", 0.35)
            filter_inputs.extend(["-i", str(sound_file)])
            filter_parts.append(f"[{input_idx}:a]volume={vol:.2f},adelay={t_ms}|{t_ms},aformat=sample_rates=44100:channel_layouts=stereo[sfx{input_idx}]")
            mix_sources.append(f"[sfx{input_idx}]")
            input_idx += 1

    # Amix all sources together
    filter_complex = ";".join(filter_parts) + f";{''.join(mix_sources)}amix=inputs={len(mix_sources)}:duration=first:dropout_transition=2[aout]"
    
    cmd = [
        "ffmpeg", "-y",
        *filter_inputs,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "pcm_s16le",
        output_wav_path
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0

# Test run
voice = r"D:\CineForge\uploads\test_audio_extract.wav"
out = r"D:\CineForge\exports\test_sfx_mix.wav"
bg = r"D:\CineForge\assets\sfx\cinematic_tension.wav"
sfx = [
    {"time": 0.0, "sound": "hook_impact.wav", "volume": 0.65},
    {"time": 3.5, "sound": "whoosh.wav", "volume": 0.40},
    {"time": 8.0, "sound": "whoosh.wav", "volume": 0.40},
    {"time": 14.0, "sound": "tech_chirp.wav", "volume": 0.30}
]

ok = mix_multitrack_audio_with_sfx(voice, sfx, bg, out)
print("AUDIO SFX MIX RESULT:", ok, "Output exists:", Path(out).exists(), "Size:", Path(out).stat().st_size if Path(out).exists() else 0)

