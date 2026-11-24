import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

font_p = Path(r"C:\Windows\Fonts\Nirmala.ttc")
print("Nirmala exists:", font_p.exists())
try:
    font = ImageFont.truetype(str(font_p), 48)
    img = Image.new("RGB", (600, 200), (0,0,0))
    draw = ImageDraw.Draw(img)
    draw.text((20, 50), "अतीतों का दिल", font=font, fill=(0, 240, 255))
    out = r"C:\Users\ISHAAN SEN\.gemini\antigravity\brain\3ff47100-4ff0-4aee-9cd3-a7d4fb2ba2ad\test_nirmala_direct.png"
    img.save(out)
    print("Saved direct Nirmala test to:", out)
except Exception as e:
    print("Error:", e)
