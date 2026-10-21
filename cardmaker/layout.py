"""Card fields and where they sit on each template."""

RARITIES = ["Common", "R", "SR", "SSR", "UR", "EX"]

TYPES = [
    "normal",
    "fire",
    "water",
    "grass",
    "electro",
    "ice",
    "fight",
    "poison",
    "ground",
    "fly",
    "psychic",
    "bug",
    "rock",
    "ghost",
    "dragon",
    "dark",
    "steel",
    "fairy",
    "electro genshin",
    "type less",
]

TYPE_LABELS = {
    "electro genshin": "Electro (Genshin)",
    "type less": "Typeless",
}

TYPE_COLORS = {
    "normal": (168, 168, 120),
    "fire": (240, 128, 48),
    "water": (104, 144, 240),
    "grass": (120, 200, 80),
    "electro": (248, 208, 48),
    "ice": (152, 216, 216),
    "fight": (192, 48, 40),
    "poison": (160, 64, 160),
    "ground": (224, 192, 104),
    "fly": (168, 144, 240),
    "psychic": (248, 88, 136),
    "bug": (168, 184, 32),
    "rock": (184, 160, 56),
    "ghost": (112, 88, 152),
    "dragon": (112, 56, 248),
    "dark": (112, 88, 72),
    "steel": (184, 184, 208),
    "fairy": (238, 153, 172),
    "electro genshin": (138, 92, 246),
    "type less": (150, 150, 150),
}


def type_label(key):
    return TYPE_LABELS.get(key, key.title())


def _type_select(field_id, label, optional=False):
    field = {"id": field_id, "label": label, "type": "type"}
    if optional:
        field["optional"] = True
    return field


def _text(field_id, label, multiline=False):
    kind = "textarea" if multiline else "text"
    return {"id": field_id, "label": label, "type": kind}


def _picture():
    return {
        "title": "Picture",
        "fields": [
            {"id": "image", "label": "Artwork", "type": "image"},
            {"id": "zoom", "label": "Zoom", "type": "range", "min": 100, "max": 220},
            {"id": "focus", "label": "Vertical focus", "type": "range", "min": 0, "max": 100},
        ],
    }


def _identity(extra=None):
    fields = [
        _text("name", "Name"),
        {"id": "rarity", "label": "Rarity", "type": "rarity"},
        _type_select("type", "Type"),
        _text("category", "Category"),
        _text("tag", "Tag"),
    ]
    if extra:
        fields.extend(extra)
    return {"title": "Card", "fields": fields}


def _stats():
    return {
        "title": "Stats",
        "fields": [_text("hp", "HP"), _text("speed", "Speed")],
    }


def _learn():
    return {
        "title": "Can learn",
        "fields": [
            _type_select("learn1", "Slot 1", optional=True),
            _type_select("learn2", "Slot 2", optional=True),
            _type_select("learn3", "Slot 3", optional=True),
            _type_select("learn4", "Slot 4", optional=True),
        ],
    }


def _move(prefix, title, power_label):
    fields = [
        _type_select(f"{prefix}_type", "Type", optional=True),
        _text(f"{prefix}_name", "Name"),
    ]
    if power_label:
        fields.append(_text(f"{prefix}_value", power_label))
    fields.append(_text(f"{prefix}_text", "Text", multiline=True))
    return {"title": title, "fields": fields}


# Text and icon boxes are (left, top, right, bottom) on the template pixel grid.
CHARACTER = {
    "id": "character",
    "label": "Character",
    "description": "Fighter card with a portrait, stats, two moves, and a passive.",
    "flip": True,
    "size": (1280, 1792),
    "frame": "character/{rarity}.png",
    "art": (0, 0, 1280, 1792),
    "empty_box": (260, 460, 1020, 700),
    "empty_label": "Add a picture",
    "main_icon": (70, 69, 202, 201),
    "main_inset": 18,
    "learn_icons": [
        (76, 969, 120, 1013),
        (130, 969, 174, 1013),
        (184, 969, 228, 1013),
        (238, 969, 282, 1013),
    ],
    "moves": [
        {
            "icon": (92, 1170, 136, 1214),
            "name": (158, 1166, 980, 1224),
            "value": (990, 1166, 1168, 1224),
            "text": (158, 1228, 1148, 1312),
        },
        {
            "icon": (92, 1318, 136, 1362),
            "name": (158, 1314, 980, 1372),
            "value": (990, 1314, 1168, 1372),
            "text": (158, 1376, 1148, 1462),
        },
        {
            "icon": (92, 1473, 136, 1517),
            "name": (158, 1469, 1148, 1526),
            "value": None,
            "text": (158, 1530, 1148, 1660),
        },
    ],
    "texts": [
        {"id": "name", "box": (300, 58, 1130, 176), "font": "display", "size": 78, "fill": (20, 16, 24), "stroke": (255, 255, 255), "stroke_width": 3, "align": "center", "auto_contrast": True},
        {"id": "category", "box": (86, 198, 186, 238), "font": "body", "size": 30, "fill": (255, 255, 255), "align": "center"},
        {"id": "hp", "box": (1090, 238, 1170, 292), "font": "number", "size": 42, "fill": (255, 255, 255), "align": "center"},
        {"id": "speed", "box": (1090, 332, 1170, 386), "font": "number", "size": 42, "fill": (255, 255, 255), "align": "center"},
        {"id": "tag", "box": (1068, 982, 1212, 1012), "font": "display", "size": 22, "fill": (255, 255, 255), "align": "center"},
    ],
    "sections": [
        _picture(),
        _identity(),
        _stats(),
        _learn(),
        _move("move1", "Move 1", "Power"),
        _move("move2", "Move 2", "Power"),
        _move("move3", "Passive", None),
    ],
    "defaults": {
        "zoom": "100",
        "focus": "35",
        "name": "Shura",
        "rarity": "EX",
        "type": "fight",
        "category": "C",
        "tag": "AmanoHa",
        "hp": "14",
        "speed": "14",
        "learn1": "fight",
        "learn2": "dark",
        "learn3": "steel",
        "learn4": "psychic",
        "move1_type": "fight",
        "move1_name": "Triple Armor Shock",
        "move1_value": "3",
        "move1_text": "When the user next attack, add a critical hit to the roll.\nShura Mode: this attack ignores negative type effectiveness.",
        "move2_type": "fight",
        "move2_name": "The Cycle of Life and Death",
        "move2_value": "5",
        "move2_text": "Remove all status effects from the user and enter Shura Mode for 3 turns.\n[Once per battle]",
        "move3_type": "dark",
        "move3_name": "Heaven Crusher",
        "move3_value": "",
        "move3_text": "If the user has lower current health than the target: Attack strength +1.\nShura Mode: the attack ignores defense.",
    },
}

ENEMY = {
    "id": "enemy",
    "label": "Enemy",
    "description": "Opponent card with a portrait, one ability, a passive, and drops.",
    "flip": True,
    "size": (1280, 1792),
    "frame": "enemy/{rarity}.png",
    "art": (0, 0, 1280, 1792),
    "empty_box": (260, 430, 1020, 760),
    "empty_label": "Add a picture",
    "main_icon": (70, 69, 202, 201),
    "main_inset": 18,
    "learn_icons": [
        (76, 1008, 120, 1052),
        (130, 1008, 174, 1052),
        (184, 1008, 228, 1052),
        (238, 1008, 282, 1052),
    ],
    "moves": [
        {
            "icon": (92, 1357, 136, 1401),
            "name": (158, 1352, 980, 1410),
            "value": (990, 1352, 1168, 1410),
            "text": (158, 1414, 1160, 1505),
        },
        {
            "icon": (92, 1516, 136, 1560),
            "name": (158, 1510, 900, 1568),
            "value": (920, 1510, 1168, 1568),
            "text": (158, 1574, 1160, 1670),
        },
    ],
    "texts": [
        {"id": "name", "box": (300, 58, 1130, 176), "font": "display", "size": 72, "fill": (255, 255, 255), "stroke": (20, 16, 24), "stroke_width": 3, "align": "center", "auto_contrast": True},
        {"id": "category", "box": (78, 198, 194, 236), "font": "body", "size": 26, "fill": (255, 255, 255), "align": "center"},
        {"id": "hp", "box": (1090, 238, 1170, 292), "font": "number", "size": 42, "fill": (255, 255, 255), "align": "center"},
        {"id": "speed", "box": (1090, 332, 1170, 386), "font": "number", "size": 42, "fill": (255, 255, 255), "align": "center"},
        {"id": "tag", "box": (1068, 1016, 1212, 1048), "font": "display", "size": 20, "fill": (255, 255, 255), "align": "center"},
        {"id": "drop_event", "box": (588, 1094, 690, 1142), "font": "number", "size": 36, "fill": (255, 255, 255), "stroke": (20, 16, 24), "stroke_width": 2, "align": "center"},
        {"id": "drop_wish", "box": (730, 1094, 840, 1142), "font": "number", "size": 36, "fill": (255, 255, 255), "stroke": (20, 16, 24), "stroke_width": 2, "align": "center"},
    ],
    "sections": [
        _picture(),
        _identity(),
        _stats(),
        _learn(),
        _move("move1", "Ability", "Power"),
        _move("move2", "Passive", "Cost"),
        {
            "title": "Drops",
            "fields": [
                _text("drop_event", "Event cards"),
                _text("drop_wish", "Wish tokens"),
            ],
        },
    ],
    "defaults": {
        "zoom": "100",
        "focus": "30",
        "name": "Alchemist",
        "rarity": "SSR",
        "type": "poison",
        "category": "EN",
        "tag": "Sangvis Ferri",
        "hp": "12",
        "speed": "12",
        "learn1": "poison",
        "learn2": "psychic",
        "learn3": "electro",
        "learn4": "normal",
        "move1_type": "poison",
        "move1_name": "Poison Blade",
        "move1_value": "3",
        "move1_text": "Inflict Poisoned on the target. If the target is already Poisoned, this move deals double damage.",
        "move2_type": "normal",
        "move2_name": "Reassemble",
        "move2_value": "[EN]",
        "move2_text": "When the user's HP is below half, restore the user to full health.\n[1 use per battle]",
        "drop_event": "x1",
        "drop_wish": "x2",
    },
}

ROUND = {
    "id": "round",
    "label": "Round, event, item",
    "description": "Story card. The same frame is used for rounds, events, and items.",
    "flip": True,
    "size": (1024, 1280),
    "back": "round/back.png",
    "frame": "round/{rarity}.png",
    "art": (18, 150, 1006, 830),
    "empty_box": (180, 360, 844, 620),
    "empty_label": "Add a picture",
    "texts": [
        {"id": "name", "box": (150, 40, 874, 160), "font": "display", "size": 64, "fill": (20, 16, 24), "stroke": (255, 255, 255), "stroke_width": 3, "align": "center"},
        {"id": "rules", "box": (80, 860, 944, 1200), "font": "body", "size": 36, "fill": (32, 32, 36), "align": "left", "valign": "top", "auto_contrast": True},
    ],
    "sections": [
        _picture(),
        {
            "title": "Card",
            "fields": [
                _text("name", "Name"),
                {"id": "rarity", "label": "Rarity", "type": "rarity"},
                {
                    "id": "back_kind",
                    "label": "Back",
                    "type": "select",
                    "options": [
                        {"id": "Round", "label": "Round"},
                        {"id": "Event", "label": "Event"},
                        {"id": "Item", "label": "Item"},
                    ],
                },
            ],
        },
        {"title": "Rules", "fields": [_text("rules", "Rules text", multiline=True)]},
    ],
    "defaults": {
        "zoom": "100",
        "focus": "50",
        "name": "Round End",
        "rarity": "SR",
        "back_kind": "Round",
        "rules": "The player with the lowest rarity card in the game gets 3 wish tokens. The other gets 1 wish token.\n[On a tie, both get 2.]",
    },
}

CARDBACK = {
    "id": "cardback",
    "label": "Card back",
    "description": "The patterned back from the card-back template. Flip a character or enemy card to see this too.",
    "flip": False,
    "size": (1280, 1792),
    "frame": "cardback/{style}/{rarity}.png",
    "art": (390, 250, 890, 760),
    "art_above": True,
    "art_radius": 36,
    "moves": [
        {
            "icon": (92, 1357, 136, 1401),
            "name": (158, 1352, 900, 1410),
            "value": (980, 1352, 1160, 1410),
            "text": (158, 1414, 1140, 1560),
        }
    ],
    "texts": [
        {"id": "title", "box": (220, 790, 1060, 910), "font": "display", "size": 72, "fill": (32, 32, 36), "stroke": (255, 255, 255), "stroke_width": 4, "align": "center"},
    ],
    "sections": [
        {
            "title": "Emblem",
            "fields": [
                {"id": "image", "label": "Replace the center emblem", "type": "image"},
                {"id": "zoom", "label": "Zoom", "type": "range", "min": 100, "max": 220},
                {"id": "focus", "label": "Vertical focus", "type": "range", "min": 0, "max": 100},
            ],
        },
        {
            "title": "Back",
            "fields": [
                {
                    "id": "style",
                    "label": "Style",
                    "type": "select",
                    "options": [
                        {"id": "enemies", "label": "Enemies"},
                        {"id": "character", "label": "Character"},
                    ],
                },
                {"id": "rarity", "label": "Rarity", "type": "rarity"},
                _text("title", "Title"),
            ],
        },
        _move("move1", "Skill line", "Power"),
    ],
    "defaults": {
        "zoom": "100",
        "focus": "50",
        "style": "enemies",
        "rarity": "EX",
        "title": "ENEMIES",
        "move1_type": "dark",
        "move1_name": "Colossus: Sharpness",
        "move1_value": "3",
        "move1_text": "Attack strength rises with the target's battle fatigue.",
    },
}

BOOSTER = {
    "id": "booster",
    "label": "Booster",
    "description": "Pack, box, and box art. Your picture replaces the sample characters.",
    "flip": False,
    "size": (1040, 1840),
    "designs": {
        "pack": {
            "size": (1040, 1840),
            "frame": "booster/pack.png",
            "art": (150, 430, 890, 1580),
            "art_above": True,
            "texts": [
                {"id": "title", "box": (60, 230, 980, 360), "font": "display", "size": 64, "fill": (255, 255, 255), "stroke": (20, 16, 28), "stroke_width": 4, "align": "center"},
            ],
        },
        "box": {
            "size": (1024, 520),
            "frame": "booster/box.png",
            "art": (420, 0, 1024, 520),
            "art_above": True,
            "texts": [
                {
                    "id": "title",
                    "box": (28, 12, 520, 78),
                    "font": "display",
                    "size": 36,
                    "fill": (180, 40, 48),
                    "align": "left",
                    "cover": (246, 242, 236, 255),
                },
            ],
        },
        "boxart": {
            "size": (960, 480),
            "frame": "booster/boxart.png",
            "art": (430, 10, 950, 470),
            "art_above": True,
            "texts": [
                {"id": "title", "box": (28, 18, 470, 78), "font": "display", "size": 32, "fill": (255, 255, 255), "stroke": (20, 16, 28), "stroke_width": 2, "align": "left"},
                {"id": "line", "box": (36, 158, 400, 200), "font": "display", "size": 24, "fill": (255, 255, 255), "stroke": (20, 16, 28), "stroke_width": 2, "align": "left"},
                {"id": "blurb", "box": (48, 208, 400, 320), "font": "body", "size": 20, "fill": (255, 255, 255), "align": "left", "valign": "top"},
                {"id": "wish", "box": (48, 390, 280, 450), "font": "body", "size": 20, "fill": (255, 255, 255), "align": "left"},
            ],
        },
    },
    "sections": [
        _picture(),
        {
            "title": "Piece",
            "fields": [
                {
                    "id": "design",
                    "label": "Which piece",
                    "type": "select",
                    "options": [
                        {"id": "pack", "label": "Booster pack"},
                        {"id": "box", "label": "Booster box"},
                        {"id": "boxart", "label": "Box art"},
                    ],
                }
            ],
        },
        {
            "title": "Words",
            "fields": [
                _text("title", "Title"),
                {**_text("line", "Subtitle"), "show_if": {"field": "design", "value": "boxart"}},
                {**_text("blurb", "Description", multiline=True), "show_if": {"field": "design", "value": "boxart"}},
                {**_text("wish", "Wish cost"), "show_if": {"field": "design", "value": "boxart"}},
            ],
        },
    ],
    "defaults": {
        "zoom": "100",
        "focus": "40",
        "design": "pack",
        "title": "Awakening Wishes",
        "line": "Awakening Wishes 2",
        "blurb": "This box contains character cards of R, SR, SSR, UR, and EX rarity.",
        "wish": "Wish cost  ",
    },
}

CARDS = {
    "character": CHARACTER,
    "enemy": ENEMY,
    "round": ROUND,
    "cardback": CARDBACK,
    "booster": BOOSTER,
}

# Photoshop files to flatten into frame art. Rarity layers are switched per export.
BUILD_JOBS = [
    {
        "file": "Cards/Character Template.psd",
        "out": "character/{rarity}.png",
        "rarities": RARITIES,
        "hide": ["artery gear", "character", "arknight", "azur lane", "background copy"],
    },
    {
        "file": "Cards/Enemies Template.psd",
        "out": "enemy/{rarity}.png",
        "rarities": RARITIES,
        "hide": ["arknight", "background copy", "layer 71", "color bg"],
    },
    {
        "file": "Cards/Round ,Event and Items Card Template.psd",
        "out": "round/back.png",
        "rarities": [None],
        "hide": ["image"],
        "keep_only": ["layer 51"],
    },
    {
        "file": "Cards/Round ,Event and Items Card Template.psd",
        "out": "round/{rarity}.png",
        "rarities": RARITIES,
        "hide": ["image", "layer 51"],
    },
    {
        "file": "Cards/Cardback Template.psd",
        "out": "cardback/{style}/{rarity}.png",
        "rarities": RARITIES,
        "styles": ["enemies", "character"],
        "hide": [],
    },
    {
        "file": "Commponent/Booster Packs.psd",
        "out": "booster/pack.png",
        "rarities": [None],
        "hide": ["characters here"],
    },
    {
        "file": "Commponent/Booster Box.psd",
        "out": "booster/box.png",
        "rarities": [None],
        "hide": [],
    },
    {
        "file": "Commponent/Booster Box Art.psd",
        "out": "booster/boxart.png",
        "rarities": [None],
        "hide": ["characters here"],
    },
]

ICON_SOURCES = [
    "Cards/Character Template.psd",
    "Cards/Enemies Template.psd",
]

BACK_FILES = {
    "Round": "Card Backs/Round Card back.png",
    "Event": "Card Backs/Event Card Back.png",
    "Item": "Card Backs/Items Card Back.png",
}
