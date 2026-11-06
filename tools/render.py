import json, sys, os, subprocess, math
from PIL import Image, ImageDraw, ImageFont

spec = json.load(open(sys.argv[1])); out = sys.argv[2]
W, H, FPS, DUR = 1080, 1920, 30, 8.5
hue = spec["hue"]; screens = spec["screens"]; n = len(screens)
seg = DUR / n
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_BIG = ImageFont.truetype(B, 108); F_LAB = ImageFont.truetype(B, 44)
F_SUB = ImageFont.truetype(B, 46); F_BRAND = ImageFont.truetype(B, 34)
GOLD = (255, 205, 60); WHITE = (255, 255, 255)
tmp = out + "_f"; os.makedirs(tmp, exist_ok=True)

def bg(t):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(0, H, 8):
        k = y / H
        c = tuple(int(hue[i] * (1 - 0.75 * k)) for i in range(3))
        d.rectangle([0, y, W, y + 8], fill=c)
    off = int(t * 120) % 160
    for x in range(-H, W + H, 160):
        d.line([(x + off, 0), (x + off + H, H)], fill=tuple(min(255, v + 18) for v in [int(h * 0.9) for h in hue]), width=26)
    return im

def wrap(d, text, font, maxw):
    words, lines, cur = text.replace(" ?", "\u00a0?").replace(" :", "\u00a0:").split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

for f in range(int(DUR * FPS)):
    t = f / FPS; i = min(int(t / seg), n - 1); s = screens[i]; lt = t - i * seg
    im = bg(t); d = ImageDraw.Draw(im)
    pop = 1.0 if (i == 0) else min(1.0, 0.85 + lt * 1.2)
    font = ImageFont.truetype(B, int(108 * pop))
    lines = s["lines"]; lh = int(130 * pop)
    y0 = H // 2 - len(lines) * lh // 2 - 60
    if "label" in s:
        lw = d.textlength(s["label"], font=F_LAB)
        d.rounded_rectangle([W/2 - lw/2 - 30, y0 - 130, W/2 + lw/2 + 30, y0 - 50], 20, fill=(0, 0, 0))
        d.text((W/2, y0 - 90), s["label"], font=F_LAB, fill=GOLD, anchor="mm")
    for k, L in enumerate(lines):
        col = GOLD if (s.get("gold") and k == len(lines) - 1) or (not s.get("gold") and k == 1) else WHITE
        d.text((W/2, y0 + k * lh + lh/2), L, font=font, fill=col, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    if s.get("sub"):
        ys = y0 + len(lines) * lh + 70
        for j, L in enumerate(wrap(d, s["sub"], F_SUB, W - 160)):
            d.text((W/2, ys + j * 62), L, font=F_SUB, fill=WHITE, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((W/2, H - 230), "@le.declic.business", font=F_BRAND, fill=WHITE, anchor="mm")
    d.rectangle([0, H - 24, int(W * t / DUR), H], fill=GOLD)
    im.save(f"{tmp}/{f:04d}.png")

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/%04d.png",
    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-crf", "22", "-preset", "veryfast", "-c:a", "aac", "-movflags", "+faststart", out], check=True)
subprocess.run(["rm", "-rf", tmp])
