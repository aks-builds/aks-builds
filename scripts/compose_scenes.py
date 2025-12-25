import math
from PIL import Image, ImageDraw, ImageFont, ImageSequence

FONT_HEAD = "C:/Windows/Fonts/impact.ttf"
FONT_BODY = "C:/Windows/Fonts/arialbd.ttf"
FONT_BODY_REG = "C:/Windows/Fonts/arial.ttf"

def make_halftone_tile(size=10, dot=2, opacity=18):
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.ellipse([size/2-dot/2, size/2-dot/2, size/2+dot/2, size/2+dot/2], fill=(255, 255, 255, opacity))
    return tile

def tile_over(im, tile):
    w, h = im.size
    tw, th = tile.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(0, h, th):
        for x in range(0, w, tw):
            overlay.paste(tile, (x, y), tile)
    return Image.alpha_composite(im.convert("RGBA"), overlay)

def outlined(draw, pos, text, font, fill=(250, 250, 250, 255), stroke_fill=(0, 0, 0, 255), stroke_width=3,
             shadow_offset=None, shadow_fill=None):
    x, y = pos
    if shadow_offset and shadow_fill:
        draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill=shadow_fill)
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)

def rounded_pill(frame, pos, text, font, fg, bg):
    x, y = pos
    tmp = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 28
    h = bbox[3] - bbox[1] + 16
    pill = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=bg, outline=(255, 255, 255, 255), width=2)
    pd.text((14, 8), text, font=font, fill=fg)
    frame.alpha_composite(pill, (int(x), int(y)))
    return w, h

def card(frame, pos, text, font, fg, bg, angle=0):
    tmp = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 20
    h = bbox[3] - bbox[1] + 14
    c = Image.new("RGBA", (w, h), bg)
    cd = ImageDraw.Draw(c)
    cd.rectangle([0, 0, w - 1, h - 1], outline=(0, 0, 0, 255), width=2)
    cd.text((10, 7 - bbox[1]), text, font=font, fill=fg)
    if angle:
        c = c.rotate(angle, expand=True, resample=Image.BICUBIC)
    frame.alpha_composite(c, (int(pos[0]), int(pos[1])))
    return c.size

def add_kanji(frame, kx, ky, kchar, kfont, kopacity):
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    kd = ImageDraw.Draw(overlay)
    kd.text((kx, ky), kchar, font=kfont, fill=(255, 255, 255, kopacity))
    return Image.alpha_composite(frame, overlay)


# ---------- Layout 1: cinematic title card (Gojo / hero) ----------
def layout_titlecard(frame, cfg):
    W, H = frame.size
    head_font = ImageFont.truetype(FONT_HEAD, cfg.get("head_size", 58))
    sub_font = ImageFont.truetype(FONT_BODY, 15)
    small_font = ImageFont.truetype(FONT_BODY, 13)
    badge_font = ImageFont.truetype(FONT_BODY, 12)

    kfont = ImageFont.truetype(FONT_HEAD, 220)
    frame = add_kanji(frame, W - 260, H - 260, cfg.get("kanji_char", "六眼"), kfont, 15)
    draw = ImageDraw.Draw(frame)
    draw.rectangle([0, 0, W - 1, H - 1], outline=(255, 255, 255, 255), width=3)

    hx, hy = cfg["headline_pos"]
    line_h = cfg.get("head_size", 58)
    for i, line in enumerate(cfg["headline"]):
        outlined(draw, (hx, hy + i * line_h), line, head_font,
                 shadow_offset=(5, 5), shadow_fill=cfg["accent"] + (255,))
    rule_y = hy + len(cfg["headline"]) * line_h + 6
    draw.line([hx, rule_y, hx + 340, rule_y], fill=(255, 255, 255, 255), width=3)
    draw.text((hx, rule_y + 10), cfg["subtitle"], font=sub_font, fill=(255, 255, 255, 255),
               stroke_width=1, stroke_fill=(0, 0, 0, 255))

    # corner rating-style stamp, top right
    num, label = cfg["stat"]
    stamp = Image.new("RGBA", (150, 62), (10, 10, 10, 220))
    sd = ImageDraw.Draw(stamp)
    sd.rectangle([0, 0, 149, 61], outline=(255, 255, 255, 255), width=2)
    sd.text((10, 4), num, font=ImageFont.truetype(FONT_HEAD, 26), fill=(255, 255, 255, 255))
    sd.text((10, 38), label, font=ImageFont.truetype(FONT_BODY, 9), fill=cfg["accent"] + (255,))
    stamp = stamp.rotate(4, expand=True, resample=Image.BICUBIC)
    frame.alpha_composite(stamp, (W - 170, 18))

    # understated bottom-left link line
    ly = H - 34
    draw.text((hx, ly), cfg["links_line"], font=small_font, fill=(255, 255, 255, 255),
               stroke_width=1, stroke_fill=(0, 0, 0, 255))
    return frame


# ---------- Layout 2: evidence board / pinned cards (Choso / catalogue) ----------
def layout_evidenceboard(frame, cfg):
    W, H = frame.size
    stamp_font = ImageFont.truetype(FONT_HEAD, 34)
    card_font = ImageFont.truetype(FONT_BODY, 14)
    tiny_font = ImageFont.truetype(FONT_BODY, 13)

    # big faded kanji watermark, centered
    kfont = ImageFont.truetype(FONT_HEAD, 260)
    frame = add_kanji(frame, W // 2 - 100, H // 2 - 160, cfg["kanji_char"], kfont, 14)
    draw = ImageDraw.Draw(frame)

    # case-file stamp, top-left, rotated
    stamp = Image.new("RGBA", (292, 82), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sd.rectangle([0, 0, 291, 81], outline=cfg["accent"] + (255,), width=4)
    outlined(sd, (10, 6), cfg["headline"][0], stamp_font, fill=(250, 250, 250, 255),
             shadow_offset=(3, 3), shadow_fill=cfg["accent"] + (255,))
    stamp = stamp.rotate(-6, expand=True, resample=Image.BICUBIC)
    frame.alpha_composite(stamp, (24, 20))

    # scattered pinned index cards around the edges
    positions = cfg["scatter_positions"]
    for (px, py, angle), text in zip(positions, cfg["badges"]):
        card(frame, (px, py), text, card_font, (10, 10, 10, 255), (250, 250, 250, 235), angle=angle)
        pin = Image.new("RGBA", (15, 15), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pin)
        pd.ellipse([0, 0, 14, 14], fill=cfg["accent"] + (255,), outline=(0, 0, 0, 255), width=1)
        frame.alpha_composite(pin, (int(px) - 6, int(py) - 6))

    # push-pin stat circle, tucked into a corner (never the center)
    num, label = cfg["stat"]
    sx, sy = cfg["stat_pos"]
    d = 120
    circle = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    cd = ImageDraw.Draw(circle)
    cd.ellipse([0, 0, d - 1, d - 1], fill=(10, 10, 10, 225), outline=cfg["accent"] + (255,), width=5)
    numfont = ImageFont.truetype(FONT_HEAD, 40)
    labelfont = ImageFont.truetype(FONT_BODY, 12)
    bbox = cd.textbbox((0, 0), num, font=numfont)
    cd.text(((d - (bbox[2]-bbox[0]))//2, 30), num, font=numfont, fill=(255, 255, 255, 255))
    lbbox = cd.textbbox((0, 0), label, font=labelfont)
    cd.text(((d - (lbbox[2]-lbbox[0]))//2, 84), label, font=labelfont, fill=cfg["accent"] + (255,))
    frame.alpha_composite(circle, (int(sx), int(sy)))

    # bottom torn strip subtitle
    draw = ImageDraw.Draw(frame)
    strip = Image.new("RGBA", (min(560, W - 48), 32), (250, 250, 250, 230))
    strd = ImageDraw.Draw(strip)
    strd.text((10, 7), cfg["subtitle"], font=tiny_font, fill=(10, 10, 10, 255))
    frame.alpha_composite(strip, (24, H - 34))
    return frame


# ---------- Layout 3: RPG inventory sheet (Sukuna / skill arsenal) ----------
def layout_rpgsheet(frame, cfg):
    W, H = frame.size
    panel_w = int(W * 0.34)
    panel = Image.new("RGBA", (panel_w, H), (8, 8, 8, 205))
    pdraw = ImageDraw.Draw(panel)
    pdraw.line([0, 0, 0, H], fill=cfg["accent"] + (255,), width=4)

    head_font = ImageFont.truetype(FONT_HEAD, 28)
    slot_font = ImageFont.truetype(FONT_BODY, 12)
    label_font = ImageFont.truetype(FONT_BODY, 10)

    kfont_small = ImageFont.truetype(FONT_HEAD, 70)
    khost = Image.new("RGBA", panel.size, (0, 0, 0, 0))
    khd = ImageDraw.Draw(khost)
    khd.text((panel_w - 90, H - 110), cfg.get("kanji_char", "領域"), font=kfont_small, fill=(255, 255, 255, 16))
    panel = Image.alpha_composite(panel, khost)
    pdraw = ImageDraw.Draw(panel)

    y = 24
    for line in cfg["headline"]:
        outlined(pdraw, (18, y), line, head_font,
                 shadow_offset=(3, 3), shadow_fill=cfg["accent"] + (255,))
        y += 32
    y += 6
    pdraw.line([18, y, panel_w - 18, y], fill=cfg["accent"] + (255,), width=2)
    y += 14

    # 2-column inventory grid
    slot_w, slot_h, gap = (panel_w - 44) // 2, 46, 8
    for i, item in enumerate(cfg["badges"]):
        col = i % 2
        row = i // 2
        sx = 18 + col * (slot_w + gap)
        sy = y + row * (slot_h + gap)
        slot = Image.new("RGBA", (slot_w, slot_h), (30, 30, 30, 220))
        sld = ImageDraw.Draw(slot)
        sld.rectangle([0, 0, slot_w - 1, slot_h - 1], outline=cfg["accent"] + (255,), width=2)
        sld.text((8, 8), item, font=slot_font, fill=(255, 255, 255, 255))
        slot = slot.rotate(-1.5 if i % 2 == 0 else 1.5, expand=True, resample=Image.BICUBIC)
        panel.alpha_composite(slot, (sx, sy))
    pdraw = ImageDraw.Draw(panel)
    grid_rows = math.ceil(len(cfg["badges"]) / 2)
    y = y + grid_rows * (slot_h + gap) + 16

    # circular power gauge
    num, label = cfg["stat"]
    d = panel_w - 60
    gauge = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gauge)
    gd.arc([4, 4, d - 4, d - 4], start=-90, end=270, fill=(60, 60, 60, 255), width=10)
    gd.arc([4, 4, d - 4, d - 4], start=-90, end=180, fill=cfg["accent"] + (255,), width=10)
    bbox = gd.textbbox((0, 0), num, font=ImageFont.truetype(FONT_HEAD, 36))
    gd.text(((d-(bbox[2]-bbox[0]))//2, d//2 - 24), num, font=ImageFont.truetype(FONT_HEAD, 36), fill=(255, 255, 255, 255))
    panel.alpha_composite(gauge, (30, y))
    pdraw.text((18, y + d + 6), label, font=label_font, fill=cfg["accent"] + (255,))

    pdraw.text((18, H - 30), cfg["links_line"], font=label_font, fill=(255, 255, 255, 255))

    frame.alpha_composite(panel, (W - panel_w, 0))
    return frame


# ---------- Layout 4: outro / credits (Itadori / contact) ----------
def layout_outro(frame, cfg):
    W, H = frame.size
    kfont = ImageFont.truetype(FONT_HEAD, 200)
    frame = add_kanji(frame, 40, H - 260, cfg.get("kanji_char", "黒閃"), kfont, 14)
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for i in range(int(H * 0.55), H):
        alpha = int(210 * (i - H * 0.55) / (H * 0.45))
        sd.line([0, i, W, i], fill=(0, 0, 0, min(max(alpha, 0), 210)))
    frame = Image.alpha_composite(frame, scrim)
    draw = ImageDraw.Draw(frame)

    head_font = ImageFont.truetype(FONT_HEAD, cfg.get("head_size", 44))
    sub_font = ImageFont.truetype(FONT_BODY, 15)
    stamp_font = ImageFont.truetype(FONT_BODY, 11)

    lines = cfg["headline"]
    total_h = len(lines) * (cfg.get("head_size", 44) + 4)
    y = H - total_h - 74
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=head_font)
        lw = bbox[2] - bbox[0]
        outlined(draw, ((W - lw) // 2, y), line, head_font,
                 shadow_offset=(4, 4), shadow_fill=cfg["accent"] + (255,))
        y += cfg.get("head_size", 44) + 4

    bbox = draw.textbbox((0, 0), cfg["subtitle"], font=sub_font)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2, y + 6), cfg["subtitle"], font=sub_font, fill=(255, 255, 255, 255),
               stroke_width=1, stroke_fill=(0, 0, 0, 255))

    # flanking cert stamps
    left_badge, right_badge = cfg["badges"][0], cfg["badges"][1]
    for text, side in [(left_badge, "L"), (right_badge, "R")]:
        bbox = draw.textbbox((0, 0), text, font=stamp_font)
        bw = bbox[2] - bbox[0] + 20
        bh = bbox[3] - bbox[1] + 12
        stamp = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        std = ImageDraw.Draw(stamp)
        std.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=bh // 2, outline=(255, 255, 255, 255), width=2,
                                fill=cfg["accent"] + (200,))
        std.text((10, 6), text, font=stamp_font, fill=(255, 255, 255, 255))
        xpos = 40 if side == "L" else W - bw - 40
        frame.alpha_composite(stamp, (xpos, H - 130))

    # centered signature line
    draw = ImageDraw.Draw(frame)
    bbox = draw.textbbox((0, 0), cfg["links_line"], font=stamp_font)
    lw = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, H - 32), cfg["links_line"], font=stamp_font, fill=(255, 255, 255, 255),
               stroke_width=1, stroke_fill=(0, 0, 0, 255))
    return frame


LAYOUTS = {
    "titlecard": layout_titlecard,
    "evidenceboard": layout_evidenceboard,
    "rpgsheet": layout_rpgsheet,
    "outro": layout_outro,
}

def compose_frame(frame, cfg):
    frame = frame.convert("RGBA")
    frame = tile_over(frame, cfg["halftone_tile"])
    frame = LAYOUTS[cfg["layout"]](frame, cfg)
    return frame.convert("RGB")

def process(src_path, out_path, cfg):
    im = Image.open(src_path)
    frames = []
    durations = []
    cfg["halftone_tile"] = make_halftone_tile()
    n = 0
    for frame in ImageSequence.Iterator(im):
        composed = compose_frame(frame.copy(), cfg)
        frames.append(composed)
        durations.append(frame.info.get("duration", 40))
        n += 1
    frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=durations, loop=0, quality=80, method=4)
    print(f"{out_path}: {n} frames composed")
