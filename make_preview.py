from PIL import Image, ImageDraw, ImageFont
import os

width, height = 1200, 630
# Background: bright yellow matching user request #FED700
img = Image.new("RGB", (width, height), "#FED700")
draw = ImageDraw.Draw(img)

# Subtle decorative grid pattern (very faint, opacity 10)
for x in range(30, width, 45):
    for y in range(30, height, 45):
        # Avoid drawing dots behind main text zone
        if 40 <= x <= 530 and 100 <= y <= 380:
            continue
        draw.ellipse([x, y, x+3, y+3], fill=(0, 0, 0, 18))

# Heavy outer border (Neobrutalism signature)
draw.rectangle([14, 14, width-14, height-14], outline="#000000", width=8)

# Load fonts
try:
    font_badge = ImageFont.truetype("arialbd.ttf", 20)
    font_h1 = ImageFont.truetype("arialbd.ttf", 46)
    font_h2 = ImageFont.truetype("arialbd.ttf", 38)
    font_desc = ImageFont.truetype("arial.ttf", 22)
    font_tag_lbl = ImageFont.truetype("arialbd.ttf", 15)
    font_tag_val = ImageFont.truetype("arialbd.ttf", 36)
    
    font_card_head = ImageFont.truetype("arialbd.ttf", 34)
    font_card_sub = ImageFont.truetype("arialbd.ttf", 18)
    font_day = ImageFont.truetype("arialbd.ttf", 18)
    font_prod = ImageFont.truetype("arialbd.ttf", 17)
    font_badge_sm = ImageFont.truetype("arialbd.ttf", 15)
except Exception:
    font_badge = font_h1 = font_h2 = font_desc = font_tag_lbl = font_tag_val = ImageFont.load_default()
    font_card_head = font_card_sub = font_day = font_prod = font_badge_sm = ImageFont.load_default()


# -------------------------------------------------------------
# LEFT COLUMN: Text Content (x from 55 to 530)
# -------------------------------------------------------------

# 1. Top Badge: "PROYECTO PF ROSA • FUMIGACIÓN"
b_x, b_y, b_w, b_h = 55, 48, 440, 46
draw.rectangle([b_x+5, b_y+5, b_x+b_w+5, b_y+b_h+5], fill="#000000") # shadow
draw.rectangle([b_x, b_y, b_x+b_w, b_y+b_h], fill="#15803D", outline="#000000", width=4)
draw.text((b_x + 20, b_y + 11), "PROYECTO PF ROSA • FUMIGACIÓN", fill="#FFFFFF", font=font_badge)

# 2. Main Title (3 lines, compact & crisp, bounded to 510px width)
draw.text((55, 118), "PROGRAMA", fill="#000000", font=font_h1)
draw.text((55, 174), "SEMANAL", fill="#000000", font=font_h1)
draw.text((55, 230), "DE APLICACIONES", fill="#3247C5", font=font_h2)

# 3. Description text (wrapped nicely within 470px)
desc_lines = [
    "Consulta en tiempo real por bloque,",
    "días programados, agroquímicos,",
    "dosis y categoría toxicológica."
]
curr_y = 300
for line in desc_lines:
    draw.text((55, curr_y), line, fill="#1E293B", font=font_desc)
    curr_y += 30

# 4. Status Box: "SEMANA ACTUAL"
st_x, st_y, st_w, st_h = 55, 425, 450, 120
draw.rectangle([st_x+6, st_y+6, st_x+st_w+6, st_y+st_h+6], fill="#000000")
draw.rectangle([st_x, st_y, st_x+st_w, st_y+st_h], fill="#FFFFFF", outline="#000000", width=5)
draw.text((st_x + 22, st_y + 16), "CALENDARIO ACTIVO", fill="#64748B", font=font_tag_lbl)
draw.text((st_x + 22, st_y + 42), "SEMANA ACTUAL", fill="#15803D", font=font_tag_val)
draw.text((st_x + 22, st_y + 88), "Sincronizado con base de datos", fill="#0284C7", font=font_tag_lbl)


# -------------------------------------------------------------
# RIGHT COLUMN: Floating Popup Card (x from 575 to 1135, width 560)
# -------------------------------------------------------------
cx, cy, cw, ch = 575, 48, 560, 525

# Card outer shadow
draw.rectangle([cx+8, cy+8, cx+cw+8, cy+ch+8], fill="#000000")
# Card base
draw.rectangle([cx, cy, cx+cw, cy+ch], fill="#F8FAFC", outline="#000000", width=5)

# Header (Blue #3247C5)
head_h = 70
draw.rectangle([cx, cy, cx+cw, cy+head_h], fill="#3247C5", outline="#000000", width=5)
draw.text((cx + 25, cy + 16), "BLOQUE 1A", fill="#FED700", font=font_card_head)
draw.text((cx + cw - 165, cy + 24), "Semana Actual", fill="#FFFFFF", font=font_card_sub)

# Inner content area
pad = 18
ix = cx + pad
iy = cy + head_h + 16
iw = cw - (pad * 2)

# --- DAY 1: LUNES ---
d1_h = 185
draw.rectangle([ix, iy, ix+iw, iy+d1_h], fill="#F0F9FF", outline="#0284C7", width=3)
# Day header strip
draw.rectangle([ix, iy, ix+iw, iy+36], fill="#E0F2FE", outline="#0284C7", width=2)
draw.text((ix + 14, iy + 8), "LUNES", fill="#0369A1", font=font_day)
# Pill: 2 PRODUCTOS
pw, ph = 125, 24
px_pill = ix + iw - pw - 8
py_pill = iy + 6
draw.rectangle([px_pill, py_pill, px_pill+pw, py_pill+ph], fill="#0284C7")
draw.text((px_pill + 10, py_pill + 4), "2 PRODUCTOS", fill="#FFFFFF", font=font_badge_sm)

# Product 1
p1_y = iy + 46
draw.rectangle([ix+10, p1_y, ix+iw-10, p1_y+58], fill="#FFFFFF", outline="#000000", width=2)
draw.text((ix + 22, p1_y + 18), "INFINITO SC", fill="#000000", font=font_prod)
# Tox badge: I (Red)
draw.rectangle([ix+iw-205, p1_y+14, ix+iw-125, p1_y+44], fill="#DC2626", outline="#991B1B", width=2)
draw.text((ix+iw-193, p1_y+20), "TOX: I", fill="#FFFFFF", font=font_badge_sm)
# Dosis badge
draw.rectangle([ix+iw-115, p1_y+14, ix+iw-20, p1_y+44], fill="#F1F5F9", outline="#000000", width=2)
draw.text((ix+iw-105, p1_y+20), "Dosis: 1.6", fill="#0F172A", font=font_badge_sm)

# Product 2
p2_y = iy + 114
draw.rectangle([ix+10, p2_y, ix+iw-10, p2_y+58], fill="#FFFFFF", outline="#000000", width=2)
draw.text((ix + 22, p2_y + 18), "RUTASTAR", fill="#000000", font=font_prod)
# Tox badge: IV (Green)
draw.rectangle([ix+iw-205, p2_y+14, ix+iw-125, p2_y+44], fill="#16A34A", outline="#166534", width=2)
draw.text((ix+iw-197, p2_y+20), "TOX: IV", fill="#FFFFFF", font=font_badge_sm)
# Dosis badge
draw.rectangle([ix+iw-115, p2_y+14, ix+iw-20, p2_y+44], fill="#F1F5F9", outline="#000000", width=2)
draw.text((ix+iw-105, p2_y+20), "Dosis: 1.5", fill="#0F172A", font=font_badge_sm)

# --- DAY 2: MIÉRCOLES ---
iy2 = iy + d1_h + 14
d2_h = 185
draw.rectangle([ix, iy2, ix+iw, iy2+d2_h], fill="#F0FDF4", outline="#16A34A", width=3)
# Day header strip
draw.rectangle([ix, iy2, ix+iw, iy2+36], fill="#DCFCE7", outline="#16A34A", width=2)
draw.text((ix + 14, iy2 + 8), "MIÉRCOLES", fill="#15803D", font=font_day)
# Pill: 2 PRODUCTOS
draw.rectangle([px_pill, iy2+6, px_pill+pw, iy2+30], fill="#16A34A")
draw.text((px_pill + 10, iy2 + 10), "2 PRODUCTOS", fill="#FFFFFF", font=font_badge_sm)

# Product 1
m1_y = iy2 + 46
draw.rectangle([ix+10, m1_y, ix+iw-10, m1_y+58], fill="#FFFFFF", outline="#000000", width=2)
draw.text((ix + 22, m1_y + 18), "OBERON SC 240", fill="#000000", font=font_prod)
# Tox badge: III (Blue)
draw.rectangle([ix+iw-205, m1_y+14, ix+iw-125, m1_y+44], fill="#2563EB", outline="#1E40AF", width=2)
draw.text((ix+iw-199, m1_y+20), "TOX: III", fill="#FFFFFF", font=font_badge_sm)
# Dosis badge
draw.rectangle([ix+iw-115, m1_y+14, ix+iw-20, m1_y+44], fill="#F1F5F9", outline="#000000", width=2)
draw.text((ix+iw-105, m1_y+20), "Dosis: 0.3", fill="#0F172A", font=font_badge_sm)

# Product 2 (6 AM Alert Demonstration!)
m2_y = iy2 + 114
draw.rectangle([ix+10, m2_y, ix+iw-10, m2_y+58], fill="#FFFBEB", outline="#D97706", width=2)
draw.text((ix + 22, m2_y + 18), "PRECISION MD", fill="#92400E", font=font_prod)
# Tox badge: N/A
draw.rectangle([ix+iw-205, m2_y+14, ix+iw-125, m2_y+44], fill="#64748B", outline="#334155", width=2)
draw.text((ix+iw-198, m2_y+20), "TOX: N/A", fill="#FFFFFF", font=font_badge_sm)
# Dosis badge
draw.rectangle([ix+iw-115, m2_y+14, ix+iw-20, m2_y+44], fill="#FEF3C7", outline="#D97706", width=2)
draw.text((ix+iw-105, m2_y+20), "Dosis: 0.5", fill="#92400E", font=font_badge_sm)

# Save
target_path = "preview.png"
img.save(target_path, "PNG")
print("Generated clean preview at preview.png")

