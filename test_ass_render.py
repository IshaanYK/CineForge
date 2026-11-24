import subprocess
import os
from pathlib import Path

# Create an ASS subtitle file with perfect styling
ass_content = """[Script Info]
Title: CineForge Master Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HormoziYellow,Nirmala UI,62,&H0000FFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,160,1
Style: CategoryPill,Segoe UI,32,&H00000000,&H00000000,&H00F0FF00,&H00000000,1,0,0,0,100,100,0,0,1,0,0,8,40,40,140,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:04.50,HormoziYellow,,0,0,160,,{\\c&H00F0FF&}संसार में{\\c&H00FFFF&} आपको अनेक इच्छाएँ हैं
Dialogue: 0,0:00:04.50,0:00:09.00,HormoziYellow,,0,0,160,,कार्य, विवाह और {\\c&H00F0FF&}संतान{\\c&H00FFFF&}
Dialogue: 0,0:00:09.00,0:00:15.00,HormoziYellow,,0,0,160,,पर सोचिए... {\\c&H00F0FF&}कितने अपने हैं?{\\c&H00FFFF&}
"""

ass_file = r"C:\Users\ISHAAN SEN\.gemini\antigravity\brain\3ff47100-4ff0-4aee-9cd3-a7d4fb2ba2ad\test_master.ass"
with open(ass_file, "w", encoding="utf-8") as f:
    f.write(ass_content)

# Test burning with FFmpeg on test_cinematic_reframe.png
# Escaping path for FFmpeg subtitles filter: replace \ with /, escape :
escaped_ass = ass_file.replace('\\', '/').replace(':', '\\:')
out_png = r"C:\Users\ISHAAN SEN\.gemini\antigravity\brain\3ff47100-4ff0-4aee-9cd3-a7d4fb2ba2ad\test_ass_flawless.png"

cmd = [
    "ffmpeg", "-y",
    "-ss", "00:00:06",
    "-i", r"C:\Users\ISHAAN SEN\.gemini\antigravity\brain\3ff47100-4ff0-4aee-9cd3-a7d4fb2ba2ad\test_cinematic_reframe.png",
    "-vf", f"subtitles='{escaped_ass}'",
    "-update", "1",
    "-frames:v", "1",
    out_png
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("FFMPEG RETURN CODE:", res.returncode)
if res.returncode != 0:
    print("STDERR:", res.stderr[-400:])
else:
    print("SUCCESS: Rendered", out_png)
