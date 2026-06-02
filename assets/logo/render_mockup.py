"""
Jersey back mockup — HFS no estilo do "10" collegiate da blusa branca,
renderizado sobre a blusa azul. Bandeira do Brasil DENTRO das letras.
"""
from PIL import Image, ImageDraw, ImageFont, ImageChops
from scipy.ndimage import binary_dilation
import numpy as np, math

# ── Paleta ─────────────────────────────────────────────────────────
BLUE       = ( 26,  63, 180)
BLUE_DARK  = ( 13,  36, 128)
BLUE_CUFF  = ( 10,  28, 100)
BLACK      = (  0,   0,   0)
GOLD       = (255, 215,   0)
GREEN_BRA  = (  0, 158,  60)
DARK_INNER = ( 22,  20,   0)
WHITE      = (255, 255, 255)

W, H = 900, 1000


# ── Helpers ────────────────────────────────────────────────────────
def draw_star(drw, cx, cy, ro, ri, color):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = ro if i % 2 == 0 else ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    drw.polygon(pts, fill=color)


def flag_patch(drw, x, y, w=58, h=38):
    drw.rectangle([x, y, x+w, y+h], fill=(0, 150, 56))
    pts = [(x+w//2, y+4), (x+w-3, y+h//2),
           (x+w//2, y+h-4), (x+3, y+h//2)]
    drw.polygon(pts, fill=(255, 215, 0))
    cx2, cy2 = x+w//2, y+h//2
    drw.ellipse([cx2-9, cy2-9, cx2+9, cy2+9], fill=(26, 63, 180))


def dilate_mask(arr, radius):
    """Circular dilation of a 2D uint8 array."""
    yi, xi = np.ogrid[-radius:radius+1, -radius:radius+1]
    struct = (xi**2 + yi**2) <= radius**2
    return binary_dilation(arr > 127, structure=struct).astype(np.uint8) * 255


def paste_solid(img_rgba, color_rgb, mask_arr):
    """Paste opaque color onto img wherever mask_arr > 0."""
    layer = Image.new("RGBA", img_rgba.size, color_rgb + (255,))
    img_rgba.paste(layer, mask=Image.fromarray(mask_arr, "L"))


def clip_composite(base, overlay_rgba, mask_arr):
    """Alpha-composite overlay onto base, restricted to mask_arr region.
    Multiplies overlay's own alpha by mask so background pixels (alpha=0)
    inside the mask don't go opaque-black."""
    r, g, b, a = overlay_rgba.split()
    mask_pil = Image.fromarray(mask_arr.astype(np.uint8), "L")
    clipped_a = ImageChops.multiply(a, mask_pil)
    clipped = Image.merge("RGBA", (r, g, b, clipped_a))
    return Image.alpha_composite(base, clipped)


# ═══════════════════════════════════════════════════════════════════
# JERSEY SILHOUETTE
# ═══════════════════════════════════════════════════════════════════
img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

jersey_pts = [
    (296, 118), (250, 130), (190, 144),
    (96, 188), (82, 280), (126, 292), (214, 252),
    (214, 842), (450, 860), (686, 842),
    (686, 252), (774, 292), (818, 280),
    (710, 188), (650, 144), (604, 130), (604, 118),
]
draw.polygon(jersey_pts, fill=BLUE)

# Sleeve cuffs
draw.polygon([(82,280),(126,292),(122,316),(78,304)],  fill=BLUE_CUFF)
draw.polygon([(818,280),(774,292),(778,316),(822,304)], fill=BLUE_CUFF)

# Collar — subtle back-neckline arc
draw.arc([320, 100, 580, 210], start=205, end=335, fill=BLUE_DARK, width=18)
draw.arc([332, 108, 568, 200], start=205, end=335, fill=(40,70,200), width=4)

# (center seam removed — cleaner look)

# ── Stars ──────────────────────────────────────────────────────────
star_arc = [
    (222,110),(256,92),(292,80),(332,72),(370,67),
    (450,64),
    (530,67),(568,72),(608,80),(644,92),(678,110),
]
for i,(sx,sy) in enumerate(star_arc):
    r = 14 if i == 5 else 10
    draw_star(draw, sx, sy, r, r*0.42, GOLD)

# ── Flag patches ───────────────────────────────────────────────────
flag_patch(draw, 94, 210)
flag_patch(draw, 748, 210)


# ═══════════════════════════════════════════════════════════════════
# HFS — COLLEGIATE TRIPLE-OUTLINE (mask dilation)
# ═══════════════════════════════════════════════════════════════════
font_path = "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf"
font = ImageFont.truetype(font_path, 330)
cx, cy = 450, 510

# 1. Render glyph mask
glyph_img = Image.new("L", (W, H), 0)
ImageDraw.Draw(glyph_img).text((cx,cy), "HFS", font=font, fill=255, anchor="mm")
glyph = np.array(glyph_img)

# 2. Dilate rings
R_BLK, R_GOLD, R_DARK = 24, 14, 7
print("Dilating rings…")
d_blk  = dilate_mask(glyph, R_BLK)
d_gold = dilate_mask(glyph, R_GOLD)
d_dark = dilate_mask(glyph, R_DARK)

# 3. Isolated bands
band_blk  = np.clip(d_blk.astype(int)  - d_gold.astype(int), 0, 255).astype(np.uint8)
band_gold = np.clip(d_gold.astype(int) - d_dark.astype(int), 0, 255).astype(np.uint8)
band_dark = np.clip(d_dark.astype(int) - glyph.astype(int),  0, 255).astype(np.uint8)

# 4. Paint bands (back → front)
paste_solid(img, BLACK,       band_blk)
paste_solid(img, GOLD,        band_gold)
paste_solid(img, DARK_INNER,  band_dark)
paste_solid(img, GREEN_BRA,   glyph)        # green fill on actual glyph


# ═══════════════════════════════════════════════════════════════════
# BRAZILIAN FLAG DESIGN INSIDE THE LETTERS
# (like the inner design of the "0" in the white jersey reference)
# Elements: Yellow losango outline → Blue circle → white equator line
# → small stars around band — all clipped to the green glyph area
# ═══════════════════════════════════════════════════════════════════
bbox = ImageDraw.Draw(glyph_img).textbbox((cx,cy), "HFS", font=font, anchor="mm")
tx0, ty0, tx1, ty1 = bbox
tw, th = tx1-tx0, ty1-ty0

flag_layer = Image.new("RGBA", (W, H), (0,0,0,0))
fd = ImageDraw.Draw(flag_layer)

# ── Outer rectangular badge border (like the frame in the "0") ──
pad = 18
fd.rectangle([tx0+pad, ty0+pad, tx1-pad, ty1-pad],
             outline=(255,215,0,200), width=4)
fd.rectangle([tx0+pad+7, ty0+pad+7, tx1-pad-7, ty1-pad-7],
             outline=(255,215,0,120), width=2)

# ── Yellow LOSANGO (flag diamond) ──────────────────────────────
lw = tw * 0.46   # half-width
lh = th * 0.51   # half-height
lcx, lcy = cx, cy
los = [(lcx, lcy-lh), (lcx+lw, lcy), (lcx, lcy+lh), (lcx-lw, lcy)]

# Gold fill (semi-transparent) + thick gold border
fd.polygon(los, fill=(255,215,0,55), outline=(255,215,0,220))
fd.polygon(los, outline=(255,215,0,220), width=5)

# Inner losango contour
lw2, lh2 = lw*0.84, lh*0.84
los2 = [(lcx, lcy-lh2), (lcx+lw2, lcy), (lcx, lcy+lh2), (lcx-lw2, lcy)]
fd.polygon(los2, outline=(255,215,0,110), width=2)

# ── Blue circle (globo) ────────────────────────────────────────
cr = int(th * 0.31)   # circle radius
fd.ellipse([lcx-cr, lcy-cr, lcx+cr, lcy+cr],
           fill=(26, 63, 180, 220), outline=(255,255,255,180), width=3)

# White horizontal band through globe (like the flag equator line)
band_h = max(4, int(cr * 0.22))
fd.rectangle([lcx-cr+4, lcy-band_h, lcx+cr-4, lcy+band_h],
             fill=(255,255,255,200))

# "ORDEM E PROGRESSO" approximation — three tiny stars on the band
for sx_off in [-cr//3, 0, cr//3]:
    draw_star(fd, lcx+sx_off, lcy, 5, 2, (0, 60, 20))

# Stars outside circle but inside losango — 4 corners
for px, py in [
    (lcx, lcy-lh*0.62),
    (lcx+lw*0.62, lcy),
    (lcx, lcy+lh*0.62),
    (lcx-lw*0.62, lcy),
]:
    draw_star(fd, int(px), int(py), 7, 3, (255,215,0))

# ── Circuit tech traces from losango corners ────────────────────
def ctrace(drw, px, py, dx, dy):
    drw.line([(int(px), int(py)), (int(px+dx), int(py+dy))],
             fill=(255,215,0,140), width=2)
    drw.ellipse([int(px+dx)-4, int(py+dy)-4,
                 int(px+dx)+4, int(py+dy)+4], fill=(255,215,0,165))

ctrace(fd, lcx, lcy-lh, -28, -28)
ctrace(fd, lcx, lcy-lh,  28, -28)
ctrace(fd, lcx+lw, lcy,  28, -22)
ctrace(fd, lcx+lw, lcy,  28,  22)
ctrace(fd, lcx, lcy+lh, -28,  28)
ctrace(fd, lcx, lcy+lh,  28,  28)
ctrace(fd, lcx-lw, lcy, -28, -22)
ctrace(fd, lcx-lw, lcy, -28,  22)

# ── Clip flag layer to glyph (multiply alphas — no black bleed) ──
img = clip_composite(img, flag_layer, glyph)
draw = ImageDraw.Draw(img)


# ═══════════════════════════════════════════════════════════════════
# DISTRESS DIAGONAL STRIPES (subtle, clipped to glyph)
# ═══════════════════════════════════════════════════════════════════
stripe_layer = Image.new("RGBA", (W, H), (0,0,0,0))
sl = ImageDraw.Draw(stripe_layer)
for yy in range(ty0-80, ty1+80, 12):
    sl.line([(tx0-80+(yy-ty0), ty0-80), (tx1+80+(yy-ty0), ty1+80)],
            fill=(0,0,0,20), width=5)

img = clip_composite(img, stripe_layer, glyph)
draw = ImageDraw.Draw(img)


# ═══════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════
out = "/home/user/hiarly-scripter/assets/logo/jersey-mockup-blue.png"
img.convert("RGB").save(out, quality=97)
print(f"✓  {out}  ({W}×{H}px)")
