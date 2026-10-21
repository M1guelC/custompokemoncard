"""Paint a card from cached frames, type icons, and the user's text."""

from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageOps

from cardmaker.assets import CACHE, CONTENT, FONTS, type_slug
from cardmaker.layout import BACK_FILES, CARDS, RARITIES, TYPE_COLORS

MOVE_VALUE_STYLE = {
    "font": "number",
    "size": 40,
    "fill": (255, 226, 120),
    "stroke": (40, 28, 16),
    "stroke_width": 2,
    "align": "center",
}

MOVE_NAME_STYLE = {
    "font": "display",
    "size": 40,
    "fill": (90, 83, 102),
    "stroke": (255, 255, 255),
    "stroke_width": 2,
    "align": "left",
    "auto_contrast": True,
}

MOVE_TEXT_STYLE = {
    "font": "body",
    "size": 30,
    "fill": (255, 255, 255),
    "stroke": (16, 12, 20),
    "stroke_width": 2,
    "align": "left",
    "valign": "top",
    "auto_contrast": True,
    "stroke_mode": "dark-only",
}


def render_png(card_id, data, photo, side="front", preview=False):
    image = render(card_id, data, photo, side)
    buffer = BytesIO()
    if preview:
        # The window only shows the card at screen size. A small JPEG is
        # what makes typing feel immediate; Download still asks for the PNG.
        image = image.copy()
        image.thumbnail((1000, 1400), Image.Resampling.LANCZOS)
        image.convert("RGB").save(buffer, "JPEG", quality=84)
        return buffer.getvalue(), "image/jpeg"
    image.convert("RGBA").save(buffer, "PNG", optimize=False, compress_level=1)
    return buffer.getvalue(), "image/png"


def render(card_id, data, photo, side="front"):
    if side == "back" and card_id == "round":
        kind = data.get("back_kind") or "Round"
        if kind not in BACK_FILES:
            kind = "Round"
        image = Image.open(CONTENT / BACK_FILES[kind]).convert("RGBA")
        return image
    if side == "back" and card_id in ("character", "enemy"):
        title = (data.get("name") or "").strip() or ("ENEMIES" if card_id == "enemy" else "CHARACTER")
        back_data = {
            "style": "enemies" if card_id == "enemy" else "character",
            "rarity": data.get("rarity") or "EX",
            "title": title,
            "move1_type": "",
            "move1_name": "",
            "move1_value": "",
            "move1_text": "",
        }
        return render("cardback", back_data, None, "front")

    spec = CARDS[card_id]
    if card_id == "booster":
        design = data.get("design") or "pack"
        spec = {**spec, **spec["designs"].get(design, spec["designs"]["pack"])}

    rarity = data.get("rarity") or "EX"
    if rarity not in RARITIES:
        rarity = "EX"
    style = data.get("style") or "enemies"
    if style not in ("enemies", "character"):
        style = "enemies"

    width, height = spec["size"]
    canvas = Image.new("RGBA", (width, height), (28, 26, 32, 255))
    if spec.get("back"):
        canvas.alpha_composite(_load(CACHE / spec["back"]))

    art_box = spec.get("art")
    if photo is not None and art_box and not spec.get("art_above"):
        _place_photo(canvas, photo, art_box, data, spec.get("art_radius", 0))

    # The type badge sits under the rarity ring, which is part of the frame.
    if spec.get("main_icon"):
        _paste_icon(canvas, data.get("type"), spec["main_icon"], spec.get("main_inset", 0))

    if spec.get("frame"):
        frame_path = CACHE / spec["frame"].format(rarity=rarity, style=style)
        frame = _load(frame_path)
        if frame.size != (width, height):
            frame = frame.crop((0, 0, width, height))
        canvas.alpha_composite(frame)

    _apply_skill_panel(canvas, spec, data)

    for icon in spec.get("drop_icons") or []:
        _paste_drop(canvas, icon)

    if photo is not None and art_box and spec.get("art_above"):
        _place_photo(canvas, photo, art_box, data, spec.get("art_radius", 0))

    for index, box in enumerate(spec.get("learn_icons") or [], start=1):
        _paste_icon(canvas, data.get(f"learn{index}"), box, 1)
    for index, move in enumerate(spec.get("moves") or [], start=1):
        _paste_icon(canvas, data.get(f"move{index}_type"), move["icon"], 0)

    draw = ImageDraw.Draw(canvas)
    ascension = _ascension_label(data)
    mark = spec.get("ascension_mark") if ascension else None
    for item in spec.get("texts") or []:
        style = dict(item)
        if mark and item.get("id") == "name":
            left, top, right, bottom = style["box"]
            style["box"] = (left, top, mark["box"][0] - 12, bottom)
        _draw_block(draw, data.get(item["id"], ""), _contrast(canvas, style))
    if mark:
        _draw_block(draw, ascension, _contrast(canvas, mark))
    for index, move in enumerate(spec.get("moves") or [], start=1):
        _draw_block(draw, data.get(f"move{index}_name", ""), _contrast(canvas, {**MOVE_NAME_STYLE, "box": move["name"]}))
        if move.get("value"):
            _draw_block(draw, data.get(f"move{index}_value", ""), {**MOVE_VALUE_STYLE, "box": move["value"]})
        _draw_block(draw, data.get(f"move{index}_text", ""), _contrast(canvas, {**MOVE_TEXT_STYLE, "box": move["text"]}))

    if photo is None and spec.get("empty_label"):
        _draw_block(
            draw,
            spec["empty_label"],
            {
                "box": spec["empty_box"],
                "font": "display",
                "size": 48,
                "fill": (255, 255, 255, 210),
                "stroke": (20, 16, 24),
                "stroke_width": 2,
                "align": "center",
            },
        )
    return canvas


def _place_photo(canvas, photo, box, data, radius=0):
    left, top, right, bottom = box
    box_w = right - left
    box_h = bottom - top
    zoom = _number(data.get("zoom"), 100, 100, 220) / 100
    focus = _number(data.get("focus"), 35, 0, 100) / 100
    scale = max(box_w / photo.width, box_h / photo.height) * zoom
    resized = photo.resize(
        (max(1, int(photo.width * scale)), max(1, int(photo.height * scale))),
        Image.Resampling.LANCZOS,
    )
    crop_left = max(0, (resized.width - box_w) // 2)
    crop_top = max(0, int((resized.height - box_h) * focus))
    crop_left = min(crop_left, max(0, resized.width - box_w))
    crop_top = min(crop_top, max(0, resized.height - box_h))
    cropped = resized.crop((crop_left, crop_top, crop_left + box_w, crop_top + box_h))
    if cropped.size != (box_w, box_h):
        fitted = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        fitted.paste(cropped, (0, 0))
        cropped = fitted
    if radius:
        mask = Image.new("L", cropped.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, box_w - 1, box_h - 1), radius=radius, fill=255)
        cropped.putalpha(mask)
    canvas.alpha_composite(cropped, (left, top))


def _apply_skill_panel(canvas, spec, data):
    relative = spec.get("skill_panel")
    if not relative:
        return
    path = CACHE / relative
    if not path.exists():
        from cardmaker.assets import build_skill_panels

        build_skill_panels()
    if not path.exists():
        return
    amount = _number(data.get("skill_opacity"), 40, 0, 100)
    if amount <= 0:
        return
    panel = _load(path)
    native = panel.getchannel("A").getextrema()[1] or 1
    scale = (amount / 100) * (255 / native)
    if abs(scale - 1) > 0.02:
        panel = panel.copy()
        panel.putalpha(panel.getchannel("A").point(lambda value: max(0, min(255, int(value * scale)))))
    canvas.alpha_composite(panel)


def _paste_drop(canvas, spec):
    icon = _equipment_badge() if spec["file"] == "equipment" else _drop_art(spec["file"])
    if icon is None:
        return
    left, top, right, bottom = spec["box"]
    width = max(1, right - left)
    height = max(1, bottom - top)
    scale = min(width / icon.width, height / icon.height)
    sized = icon.resize(
        (max(1, int(icon.width * scale)), max(1, int(icon.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas.alpha_composite(
        sized,
        (left + (width - sized.width) // 2, top + (height - sized.height) // 2),
    )


def _drop_art(name):
    path = CACHE / "drops" / f"{name}.png"
    if not path.exists():
        from cardmaker.assets import build_drop_icons

        build_drop_icons()
    if not path.exists():
        return None
    return _load(path)


@lru_cache(maxsize=1)
def _equipment_badge():
    size = 160
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pen.ellipse((4, 4, size - 5, size - 5), fill=(92, 64, 24, 245), outline=(236, 196, 92, 255), width=8)
    pen.ellipse((16, 16, size - 17, size - 17), outline=(236, 210, 140, 255), width=3)
    pen.line((42, 132, 128, 36), fill=(236, 242, 246, 255), width=10)
    pen.polygon([(128, 36), (116, 34), (124, 50)], fill=(236, 242, 246, 255))
    pen.line((58, 92, 96, 118), fill=(232, 186, 74, 255), width=8)
    pen.line((46, 138, 62, 122), fill=(196, 140, 48, 255), width=8)
    return image.resize((80, 80), Image.Resampling.LANCZOS)


def _paste_icon(canvas, key, box, inset):
    key = (key or "").strip()
    if not key or key == "none":
        return
    left, top, right, bottom = box
    left += inset
    top += inset
    right -= inset
    bottom -= inset
    width = max(1, right - left)
    height = max(1, bottom - top)
    icon = _icon(key)
    if icon is None:
        color = TYPE_COLORS.get(key, (140, 140, 140))
        badge = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        pen = ImageDraw.Draw(badge)
        pen.ellipse((1, 1, width - 2, height - 2), fill=color + (255,))
        canvas.alpha_composite(badge, (left, top))
        return
    scale = min(width / icon.width, height / icon.height)
    sized = icon.resize(
        (max(1, int(icon.width * scale)), max(1, int(icon.height * scale))),
        Image.Resampling.LANCZOS,
    )
    origin_x = left + (width - sized.width) // 2
    origin_y = top + (height - sized.height) // 2
    canvas.alpha_composite(sized, (origin_x, origin_y))


def _ascension_label(data):
    return {"1": "I", "2": "II", "3": "III"}.get(str(data.get("ascension_level") or "").strip(), "")


def _contrast(canvas, style):
    if not style.get("auto_contrast"):
        return style
    style = dict(style)
    fill, stroke = _contrast_colors(canvas, style["box"])
    style["fill"] = fill
    if style.get("stroke_mode") == "dark-only" and fill != (255, 255, 255):
        style["stroke"] = None
        style["stroke_width"] = 0
    else:
        style["stroke"] = stroke
        style["stroke_width"] = max(style.get("stroke_width", 0), 2)
    return style


def _contrast_colors(canvas, box):
    left, top, right, bottom = [int(value) for value in box]
    y = max(0, min(canvas.height - 1, (top + bottom) // 2))
    samples = []
    step = max(1, (right - left) // 6)
    for x in range(left + 8, right - 8, step):
        if x < 0 or x >= canvas.width:
            continue
        red, green, blue, alpha = canvas.getpixel((x, y))
        if alpha < 160:
            continue
        samples.append((red + green + blue) / 3)
    average = sum(samples) / len(samples) if samples else 180
    if average < 150:
        return (255, 255, 255), (20, 16, 24)
    return (28, 24, 32), (255, 255, 255)


def _draw_block(draw, text, style):
    text = "" if text is None else str(text).strip()
    if not text and not style.get("cover"):
        return
    if style.get("cover"):
        draw.rectangle(style["box"], fill=style["cover"])
    if not text:
        return
    left, top, right, bottom = style["box"]
    max_w = max(8, right - left)
    max_h = max(8, bottom - top)
    font_file = _font_file(style.get("font", "body"), text)
    size = style.get("size", 32)
    font = _fit_font(draw, text, font_file, size, max_w, max_h)
    lines = _wrap(draw, text, font, max_w)
    line_h = font.size + max(2, font.size // 8)
    block_h = line_h * len(lines)
    if style.get("valign") == "top":
        y = top
    else:
        y = top + max(0, (max_h - block_h) // 2)
    fill = style.get("fill", (255, 255, 255))
    stroke = style.get("stroke")
    stroke_width = style.get("stroke_width", 0) if stroke else 0
    align = style.get("align", "left")
    for line in lines:
        line_w = draw.textlength(line, font=font)
        if align == "center":
            x = left + (max_w - line_w) / 2
        elif align == "right":
            x = right - line_w
        else:
            x = left
        draw.text(
            (x, y),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke,
        )
        y += line_h
        if y > bottom:
            break


def _fit_font(draw, text, font_file, size, max_w, max_h):
    size = int(size)
    while size > 12:
        font = _truetype(font_file, size)
        lines = _wrap(draw, text, font, max_w)
        line_h = size + max(2, size // 8)
        widest = max((draw.textlength(line, font=font) for line in lines), default=0)
        if widest <= max_w and line_h * len(lines) <= max_h:
            return font
        size -= 2
    return _truetype(font_file, 12)


def _wrap(draw, text, font, max_w):
    lines = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split(" ")
        if not words or words == [""]:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if draw.textlength(trial, font=font) <= max_w:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines or [""]


def _font_file(role, text):
    if any(ord(char) > 127 for char in text):
        return str(FONTS["jp"])
    return str(FONTS.get(role, FONTS["body"]))


@lru_cache(maxsize=64)
def _truetype(path, size):
    return ImageFont.truetype(path, size)


@lru_cache(maxsize=48)
def _load(path):
    return Image.open(path).convert("RGBA")


@lru_cache(maxsize=32)
def _icon(key):
    path = CACHE / "icons" / f"{type_slug(key)}.png"
    if not path.exists():
        return None
    image = Image.open(path).convert("RGBA")
    if image.getchannel("A").getextrema()[1] == 0:
        return None
    return image


def _number(value, default, low, high):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(low, min(high, number))


def open_photo(raw):
    photo = Image.open(BytesIO(raw))
    photo.seek(0)
    photo = ImageOps.exif_transpose(photo)
    if photo.width * photo.height > 40_000_000:
        photo.thumbnail((4000, 4000))
    return photo.convert("RGBA")
