"""
Drift Chameleon wrap v3 for modely-2025-premium.
JDM drift livery optimized for Unreal Engine PBR Improved Lighting (2026.26.200.11):
  - Smooth chameleon bands that catch specular as car rotates
  - Bold diagonal neon stripes with bright edges (look like reflections under UE)
  - Clean vector shapes = small PNG, <1MB
  - Alpha mask = panels only, transparent gaps (matches official examples)
Orientation: top=hood/front, bottom=trunk/rear, middle=glass roof.
"""
import os, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from collections import deque

ROOT = "/home/user/custom-wraps/modely-2025-premium"
TPL = os.path.join(ROOT, "template.png")
OUT_DIR = os.path.join(ROOT, "example")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "Drift_Chameleon.png")

W = H = 1024

# ---------- Load template & build panel mask via flood-fill ----------
# True panel pixels = white regions completely enclosed by black outlines
# (not connected to the image border). Outside white (connected to border)
# and panel-seam black lines are transparent -- matches official wraps.
tpl = Image.open(TPL).convert('RGB')
tpl_arr = np.array(tpl)
brightness = tpl_arr.min(axis=2)
is_white = brightness > 180
outside = np.zeros((H,W), dtype=bool)
q = deque()
for x in range(W):
    for y in (0, H-1):
        if is_white[y,x] and not outside[y,x]:
            outside[y,x] = True; q.append((x,y))
for y in range(H):
    for x in (0, W-1):
        if is_white[y,x] and not outside[y,x]:
            outside[y,x] = True; q.append((x,y))
while q:
    x,y = q.popleft()
    for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if 0<=nx<W and 0<=ny<H and is_white[ny,nx] and not outside[ny,nx]:
            outside[ny,nx] = True; q.append((nx,ny))
panel = is_white & ~outside
mask_img = Image.fromarray((panel*255).astype(np.uint8), 'L')
mask_img = mask_img.filter(ImageFilter.GaussianBlur(0.8))
mask_img = mask_img.point(lambda p: 255 if p > 30 else 0)

# ---------- 1) Chameleon base using large gradient polygons (vector-friendly) ----------
# We paint diagonal bands of color - few colors = small PNG
img = Image.new('RGB', (W,H), (40, 10, 70))
draw = ImageDraw.Draw(img, 'RGBA')

# Diagonal bands from bottom-left to top-right
# Each band is a thick polygon with gradient approximated by 2-3 color layers
bands = [
    # (width_px, (r,g,b))
    (180, (35, 8, 65)),     # deep purple
    (260, (130, 18, 160)), # magenta
    (220, (15, 110, 185)), # cyan
    (240, (200, 35, 110)), # hot pink
    (240, (30, 10, 55)),   # deep shadow
    (220, (160, 25, 180)), # magenta again
    (260, (20, 130, 200)), # cyan again
]

def band_poly(y_center, width, angle_deg=-32):
    """Return polygon coords (list of 4 points) for a diagonal band across the image."""
    a = math.radians(angle_deg)
    dx = math.cos(a) * width/2
    dy = math.sin(a) * width/2
    # perpendicular direction for the long axis of the band
    px, py = -math.sin(a), math.cos(a)
    L = 1600  # long enough to cover image
    cx, cy = W/2, y_center
    pts = [
        (cx - dx + px*L, cy - dy + py*L),
        (cx + dx + px*L, cy + dy + py*L),
        (cx + dx - px*L, cy + dy - py*L),
        (cx - dx - px*L, cy - dy - py*L),
    ]
    return pts

# Draw bands from back to front so they overlap nicely
y_start = -400
for (bw, col) in bands:
    y_start += bw
    pts = band_poly(y_start, bw)
    draw.polygon(pts, fill=col)

# Add a couple of soft "specular" light bands (white-ish low opacity) to simulate metallic reflection
for spec_y, spec_w, spec_a in [(-150, 200, 50), (1100, 260, 40)]:
    pts = band_poly(spec_y, spec_w)
    draw.polygon(pts, fill=(255,255,255,spec_a))

# Second set of bands at a slightly different angle for iridescent feel
img2 = Image.new('RGB', (W,H), (0,0,0))
d2 = ImageDraw.Draw(img2, 'RGBA')
y2 = -300
for (bw, col) in [(200,(70,10,130)),(240,(200,40,140)),(260,(30,150,220)),(280,(230,60,90)),(260,(130,20,170))]:
    y2 += bw
    pts = band_poly(y2, bw, angle_deg=-38)
    d2.polygon(pts, fill=col)
img = Image.blend(img, img2, 0.45)

# ---------- 2) Drift stripes (bold vector lines) ----------
draw = ImageDraw.Draw(img, 'RGBA')
# Helper to draw a thick stripe from offset direction
def diag_stripe(offset, width, color, alpha=255, angle_deg=-32):
    a = math.radians(angle_deg)
    # perpendicular direction
    px, py = -math.sin(a), math.cos(a)
    dx, dy = math.cos(a), math.sin(a)
    L = 1600
    cx = W/2 + px*offset
    cy = H/2 + py*offset
    pts = [
        (cx - dx*width/2 + (-px)*L, cy - dy*width/2 + (-py)*L),
        (cx + dx*width/2 + (-px)*L, cy + dy*width/2 + (-py)*L),
        (cx + dx*width/2 + px*L,    cy + dy*width/2 + py*L),
        (cx - dx*width/2 + px*L,    cy - dy*width/2 + py*L),
    ]
    draw.polygon(pts, fill=color+(alpha,))

# Main hot-pink stripe
diag_stripe(120, 110, (255, 30, 140), 210)
# White bright highlight edge (specular core) - very important for UE reflections
diag_stripe(75, 6, (255, 255, 255), 240)
# Cyan accent stripe
diag_stripe(-20, 38, (0, 230, 255), 220)
diag_stripe(-40, 3, (220, 255, 255), 240)
# Purple shadow stripe
diag_stripe(240, 50, (130, 0, 210), 150)
# Magenta counter-stripe at reverse angle
def diag_stripe2(offset, width, color, alpha=255, angle_deg=20):
    a = math.radians(angle_deg)
    px, py = -math.sin(a), math.cos(a)
    dx, dy = math.cos(a), math.sin(a)
    L = 1600
    cx = W/2 + px*offset
    cy = H/2 + py*offset
    pts = [
        (cx - dx*width/2 + (-px)*L, cy - dy*width/2 + (-py)*L),
        (cx + dx*width/2 + (-px)*L, cy + dy*width/2 + (-py)*L),
        (cx + dx*width/2 + px*L,    cy + dy*width/2 + py*L),
        (cx - dx*width/2 + px*L,    cy - dy*width/2 + py*L),
    ]
    draw.polygon(pts, fill=color+(alpha,))
diag_stripe2(-280, 22, (255, 80, 180), 150, angle_deg=25)

# Soft glow near the pink stripe using a wider translucent band
glow = Image.new('RGBA', (W,H), (0,0,0,0))
gd = ImageDraw.Draw(glow)
diag_stripe_g = lambda off,w,c,a: gd.polygon(band_poly(off,w,angle_deg=-32), fill=c+(a,))
# use diag_stripe approach on glow
def g_stripe(gd, offset, width, color, alpha, angle_deg=-32):
    a = math.radians(angle_deg)
    px, py = -math.sin(a), math.cos(a)
    dx, dy = math.cos(a), math.sin(a)
    L = 1600
    cx = W/2 + px*offset; cy = H/2 + py*offset
    pts = [
        (cx - dx*width/2 + (-px)*L, cy - dy*width/2 + (-py)*L),
        (cx + dx*width/2 + (-px)*L, cy + dy*width/2 + (-py)*L),
        (cx + dx*width/2 + px*L,    cy + dy*width/2 + py*L),
        (cx - dx*width/2 + px*L,    cy - dy*width/2 + py*L),
    ]
    gd.polygon(pts, fill=color+(alpha,))
g_stripe(gd, 120, 200, (255,30,140), 50)
g_stripe(gd, -20, 140, (0,230,255), 40)
glow = glow.filter(ImageFilter.GaussianBlur(18))
img = Image.alpha_composite(img.convert('RGBA'), glow).convert('RGB')
draw = ImageDraw.Draw(img, 'RGBA')

# Re-draw crisp stripe edges on top of glow for sharp specular look
diag_stripe(120, 110, (255, 30, 140), 230)
diag_stripe(75, 6, (255, 255, 255), 250)
diag_stripe(-20, 38, (0, 230, 255), 235)
diag_stripe(-40, 3, (230,255,255), 250)

# ---------- 3) Fonts ----------
def font(sz):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", sz)
    except:
        return ImageFont.load_default()

F_XL = font(120)
F_L  = font(72)
F_M  = font(32)
F_S  = font(22)
F_XS = font(16)

def ctext(cx, cy, text, f, color=(255,255,255), stroke=None):
    if stroke is None:
        stroke = max(1, f.size//10)
    bbox = draw.textbbox((0,0), text, font=f, stroke_width=stroke)
    tw = bbox[2]-bbox[0]; th = bbox[3]-bbox[1]
    draw.text((cx - tw/2 - bbox[0], cy - th/2 - bbox[1]),
              text, fill=color+(255,), font=f,
              stroke_width=stroke, stroke_fill=(0,0,0,255))

# ---------- 4) Hood (top trapezoid y ~ 110-340) ----------
ctext(512, 140, "TOKYO UNDERGROUND", F_XS, (255,255,255), stroke=1)
ctext(512, 215, "DRIFT", F_L, (255, 60, 160))
ctext(512, 285, "KING",  F_M, (0, 235, 255))

# ---------- 5) Doors - race number 86 ----------
# Door layout: two panels per side (upper door ~y340-565, lower door ~y570-770),
# plus rear quarter panel below. Keep 86 circle inside upper door.
def race_num(cx, cy, num):
    r = 52
    draw.ellipse([cx-r-4, cy-r-4, cx+r+4, cy+r+4], fill=(255,255,255,250))
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255,30,140,250))
    ctext(cx, cy+3, str(num), font(90), (255,255,255), stroke=3)
race_num(162, 455, 86)
race_num(862, 455, 86)

# ---------- 6) Sponsor decals (place each inside one panel so they don't cross seams) ----------
# Upper door (below 86): y~510-555  ; lower door: y~585-720
for (x,y,s,fs) in [
    (162, 540, "TURBO", F_XS),    # upper door, below 86
    (130, 620, "BRIDE", F_S),     # lower door upper
    (140, 710, "DRIFT", F_XS),    # lower door lower
    (862, 540, "JDM", F_XS),
    (895, 620, "NEON", F_S),
    (885, 710, "2JZ", F_XS),
]:
    ctext(x, y, s, fs, (255,255,255), stroke=2)

# Mirrors highlight
for mx in (305, 719):
    draw.ellipse([mx-18,380-12,mx+18,380+12], outline=(0,230,255,255), width=3)
    draw.ellipse([mx-7,380-4,mx+7,380+4], fill=(255,255,255,220))

# ---------- 7) Rear trunk (bottom) ----------
ctext(512, 900, "TOUGE", F_M, (255, 60, 160))
ctext(512, 960, "NIGHT RACER", F_XS, (255,255,255), stroke=1)

# ---------- 8) Bumper hash marks ----------
for i, off in enumerate(range(40, W-40, 60)):
    col = (255,50,150,220) if i%2==0 else (0,220,255,220)
    draw.polygon([(off,90),(off+32,90),(off+16,112)], fill=col)
for i, off in enumerate(range(40, W-40, 60)):
    col = (0,220,255,220) if i%2==0 else (255,50,150,220)
    draw.polygon([(off,935),(off+32,935),(off+16,913)], fill=col)

# ---------- 9) Apply panel mask (transparent outside panels) ----------
rgba = img.convert('RGBA')
rgba.putalpha(mask_img)

# ---------- 10) Save PNG (try 1024, then downscale if needed) ----------
rgba.save(OUT, 'PNG', optimize=True)
fsize = os.path.getsize(OUT)
print(f"1024px: {fsize/1024:.1f} KB")

if fsize > 1_000_000:
    rgba768 = rgba.resize((768,768), Image.LANCZOS)
    m768 = mask_img.resize((768,768), Image.LANCZOS).point(lambda p: 255 if p>128 else 0)
    rgba768.putalpha(m768)
    rgba768.save(OUT, 'PNG', optimize=True)
    fsize = os.path.getsize(OUT)
    print(f"768px: {fsize/1024:.1f} KB")

if fsize > 1_000_000:
    rgba512 = rgba.resize((512,512), Image.LANCZOS)
    m512 = mask_img.resize((512,512), Image.LANCZOS).point(lambda p: 255 if p>128 else 0)
    rgba512.putalpha(m512)
    rgba512.save(OUT, 'PNG', optimize=True)
    fsize = os.path.getsize(OUT)
    print(f"512px: {fsize/1024:.1f} KB")

print(f"Final: {fsize/1024:.1f} KB  -> {OUT}")
