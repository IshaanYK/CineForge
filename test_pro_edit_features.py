import cv2
import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import sys

sys.path.append(r"D:\CineForge")
from video_pipeline import get_unicode_font, fit_frame_to_target

# Load raw frame
cap = cv2.VideoCapture(r"D:\CineForge\uploads\1c0ee7027a_2.mp4")
ret, raw_frame = cap.read()
cap.release()
assert ret, "Could not read frame from 1c0ee7027a_2.mp4"

target_w, target_h = 1080, 1920

# 1. Smart Subject Framing (Face focused, no AC)
framed = fit_frame_to_target(raw_frame, target_w, target_h, fit_mode="smart_fill")

# 2. Cinematic Color Grade (Contrast + Saturation Boost + Radial Vignette)
def apply_cinematic_grade(bgr_img: np.ndarray) -> np.ndarray:
    # Convert to HSV to boost saturation cleanly
    hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.18, 0, 255) # +18% saturation
    # Mild contrast S-curve on V
    v = hsv[:, :, 2] / 255.0
    v = np.clip(1.0 / (1.0 + np.exp(-6.5 * (v - 0.5))), 0, 1.0) * 255.0
    hsv[:, :, 2] = v
    graded = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # Subtle radial vignette on edges
    rows, cols = graded.shape[:2]
    kernel_x = cv2.getGaussianKernel(cols, cols / 1.6)
    kernel_y = cv2.getGaussianKernel(rows, rows / 1.6)
    kernel = kernel_y * kernel_x.T
    mask = kernel / kernel.max()
    mask = 0.35 + 0.65 * mask # gentle dark corners
    for i in range(3):
        graded[:, :, i] = np.clip(graded[:, :, i] * mask, 0, 255).astype(np.uint8)
    return graded

graded = apply_cinematic_grade(framed)
pil_canvas = Image.fromarray(cv2.cvtColor(graded, cv2.COLOR_BGR2RGB))
draw = ImageDraw.Draw(pil_canvas)

# 3. Dynamic B-Roll Overlay Card (Picture-in-Picture with glowing border & drop shadow)
# Let's test overlaying a thematic B-Roll image (e.g. sunrise_hills.jpg or cyber image)
broll_path = Path(r"C:\Users\ISHAAN SEN\.gemini\antigravity-ide\scratch\reelforge-ai\assets\sunrise_hills.jpg")
if not broll_path.exists():
    broll_path = Path(r"D:\CineForge\assets\broll\ai_humanoid.jpg")

if broll_path.exists():
    broll_img = Image.open(broll_path).convert("RGBA")
    card_w, card_h = 920, 520
    broll_resized = broll_img.resize((card_w, card_h), Image.Resampling.LANCZOS)
    
    # Create rounded card with glowing hairline border
    card_mask = Image.new("L", (card_w, card_h), 0)
    draw_mask = ImageDraw.Draw(card_mask)
    draw_mask.rounded_rectangle([0, 0, card_w, card_h], radius=24, fill=255)
    
    # Position card in upper third (Y = 160)
    card_x = (target_w - card_w) // 2
    card_y = 160
    
    # Shadow layer
    shadow = Image.new("RGBA", (card_w + 40, card_h + 40), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([20, 20, card_w + 20, card_h + 20], radius=24, fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    pil_canvas.paste(shadow, (card_x - 20, card_y - 10), shadow)
    
    # Paste B-roll card
    pil_canvas.paste(broll_resized, (card_x, card_y), card_mask)
    
    # Glowing border on top
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=24,
        outline=(0, 240, 255),
        width=3
    )
    
    # Topic pill over B-roll
    pill_font = get_unicode_font(28, text="संसार और जीवन")
    draw.rounded_rectangle(
        [card_x + 24, card_y + card_h - 60, card_x + 280, card_y + card_h - 16],
        radius=14,
        fill=(1, 1, 2)
    )
    draw.text((card_x + 40, card_y + card_h - 54), "🌌 ब्रह्मांड और कर्म", font=pill_font, fill=(0, 240, 255))

# 4. Floating Animated Emoji Badge (e.g. 💍 विवाह / 👨‍👩‍👧 संतान)
emoji_font = get_unicode_font(42, text="💍")
label_font = get_unicode_font(34, text="विवाह और संतान")
badge_y = 740
badge_w = 420
badge_x = (target_w - badge_w) // 2

# Glassmorphic pill
draw.rounded_rectangle(
    [badge_x, badge_y, badge_x + badge_w, badge_y + 64],
    radius=20,
    fill=(10, 15, 26),
    outline=(255, 230, 0),
    width=2
)
draw.text((badge_x + 28, badge_y + 8), "💍 👨‍👩‍👧", font=emoji_font, fill=(255, 230, 0))
draw.text((badge_x + 150, badge_y + 14), "विवाह और संतान", font=label_font, fill=(255, 255, 255))

# 5. Neon Subtitle below chest mic (88% height)
sub_font = get_unicode_font(64, text="आखिर कितने अपने हैं?")
sub_text = "आखिर कितने अपने हैं?"
s_bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
sw = s_bbox[2] - s_bbox[0]
sx = (target_w - sw) // 2
sy = int(target_h * 0.88)

for dx, dy in [(-4,-4), (4,4), (-4,4), (4,-4), (0,4), (0,-4), (4,0), (-4,0)]:
    draw.text((sx + dx, sy + dy), sub_text, font=sub_font, fill=(0, 0, 0))
draw.text((sx, sy), sub_text, font=sub_font, fill=(255, 230, 0))

# 6. Neon Progress Bar at very bottom (7px)
draw.rectangle([0, target_h - 8, int(target_w * 0.35), target_h], fill=(0, 240, 255))

out_path = r"C:\Users\ISHAAN SEN\.gemini\antigravity\brain\3ff47100-4ff0-4aee-9cd3-a7d4fb2ba2ad\test_pro_editor_masterpiece.png"
pil_canvas.save(out_path)
print("SUCCESS: Rendered", out_path)

