"""Flatten the Photoshop templates into cached frame art."""

from pathlib import Path

from PIL import Image

from cardmaker.layout import BUILD_JOBS, ICON_SOURCES, TYPES

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "Custom Content" / "Custom Content"
CACHE = ROOT / "cache"
VERSION = "2"

FONTS = {
    "display": CONTENT / "Fonts" / "HYWenHei.ttf",
    "body": CONTENT / "Fonts" / "supermarket.ttf",
    "number": CONTENT / "Fonts" / "LaOriental-Bold.otf",
    "jp": CONTENT / "Fonts" / "Default_JP.ttf",
}

RARITY_OF = {
    "common": "Common",
    "r": "R",
    "sr": "SR",
    "ssr": "SSR",
    "ur": "UR",
    "ex": "EX",
    "legen": "EX",
}

STYLE_GROUP = {
    "character": "character back",
    "enemies": "enemies back",
}


def norm_name(name):
    return " ".join(str(name).replace("\x00", " ").split()).lower()


def norm_type(name):
    text = norm_name(name)
    if " old" in text:
        return None
    text = text.replace("posion", "poison")
    if text in TYPES:
        return text
    return None


def type_slug(key):
    return key.replace(" ", "-")


def _walk(layers):
    for layer in layers:
        yield layer
        if layer.is_group():
            yield from _walk(layer)


def _apply(psd, job, rarity, style):
    hide = set(job.get("hide") or [])
    keep_only = job.get("keep_only")
    wanted_style = STYLE_GROUP.get(style) if style else None

    def visit(layer):
        name = norm_name(layer.name)
        visible = layer.visible
        rarity_name = RARITY_OF.get(name)
        if rarity and rarity_name:
            visible = rarity_name == rarity
        if wanted_style and name in STYLE_GROUP.values():
            visible = name == wanted_style
        if layer.kind in ("type", "smartobject") or norm_type(layer.name) or name in hide:
            visible = False
        if keep_only and not layer.is_group() and name not in keep_only:
            visible = False
        layer.visible = visible
        if layer.is_group():
            for child in layer:
                visit(child)

    for layer in psd:
        visit(layer)


def _composite(psd):
    image = psd.composite(force=True).convert("RGBA")
    if image.size != (psd.width, psd.height):
        canvas = Image.new("RGBA", (psd.width, psd.height), (0, 0, 0, 0))
        canvas.alpha_composite(image, (0, 0))
        image = canvas
    return image


def _save(image, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=False, compress_level=1)


def build_icons():
    from psd_tools import PSDImage

    best = {}
    documents = []
    for relative in ICON_SOURCES:
        psd = PSDImage.open(CONTENT / relative)
        documents.append(psd)
        for layer in _walk(psd):
            key = norm_type(layer.name)
            if not key or layer.kind not in ("pixel", "smartobject"):
                continue
            try:
                image = layer.topil()
            except Exception:
                image = None
            if image is None:
                continue
            image = image.convert("RGBA")
            opaque = sum(image.getchannel("A").histogram()[16:])
            if opaque < 20:
                continue
            current = best.get(key)
            if current is None or opaque > current[0]:
                best[key] = (opaque, image)

    icon_dir = CACHE / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)
    for key, (_score, image) in best.items():
        path = icon_dir / f"{type_slug(key)}.png"
        if path.exists():
            continue
        _save(image, path)
        print(f"  icon {key}", flush=True)

    missing = [key for key in TYPES if not (icon_dir / f"{type_slug(key)}.png").exists()]
    if missing:
        print("  no artwork for:", ", ".join(missing), flush=True)
    documents.clear()


def build_frames():
    from psd_tools import PSDImage

    opened = {}
    for job in BUILD_JOBS:
        styles = job.get("styles") or [None]
        for style in styles:
            for rarity in job["rarities"]:
                relative = job["out"].format(rarity=rarity or "", style=style or "")
                path = CACHE / relative
                if path.exists():
                    continue
                source = job["file"]
                if source not in opened:
                    print(f"Opening {source}", flush=True)
                    opened[source] = PSDImage.open(CONTENT / source)
                psd = opened[source]
                label = relative
                print(f"  frame {label}", flush=True)
                _apply(psd, job, rarity, style)
                _save(_composite(psd), path)
        opened.clear()


def build_drop_icons():
    """The item drop sits in the enemy file, hidden, in the same slot as the event icon."""
    path = CACHE / "drops" / "item.png"
    if path.exists():
        return
    try:
        from psd_tools import PSDImage
    except ImportError:
        return

    psd = PSDImage.open(CONTENT / "Cards/Enemies Template.psd")
    for layer in _walk(psd):
        if norm_name(layer.name) != "items" or not layer.is_group():
            continue
        for child in layer:
            if child.kind != "pixel":
                continue
            image = child.topil()
            if image is None:
                continue
            _save(image.convert("RGBA"), path)
            return


def _find_layer(layers, name):
    for layer in layers:
        if norm_name(layer.name) == name:
            return layer
        if layer.is_group():
            found = _find_layer(layer, name)
            if found:
                return found
    return None


def build_skill_panels():
    """The gray skill panel is its own shape, so the editor can fade it."""
    from psd_tools import PSDImage

    sources = (
        ("Cards/Character Template.psd", "character"),
        ("Cards/Enemies Template.psd", "enemy"),
    )
    for relative, name in sources:
        path = CACHE / "panels" / f"{name}.png"
        if path.exists():
            continue
        psd = PSDImage.open(CONTENT / relative)
        layer = _find_layer(psd, "ability box")
        if layer is None:
            continue
        piece = layer.composite().convert("RGBA")
        canvas = Image.new("RGBA", (psd.width, psd.height), (0, 0, 0, 0))
        canvas.alpha_composite(piece, (layer.left, layer.top))
        _save(canvas, path)
        print(f"  skill panel {name}", flush=True)


def ensure_cache():
    version_path = CACHE / "version.txt"
    if version_path.exists() and version_path.read_text().strip() != VERSION:
        import shutil

        shutil.rmtree(CACHE)
    CACHE.mkdir(parents=True, exist_ok=True)
    print("Preparing card frames from Custom Content…", flush=True)
    build_icons()
    build_drop_icons()
    build_skill_panels()
    build_frames()
    version_path.write_text(VERSION)
    print("Frames ready.", flush=True)


if __name__ == "__main__":
    ensure_cache()
