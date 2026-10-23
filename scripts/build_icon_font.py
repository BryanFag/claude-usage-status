import json
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

ROOT = Path(__file__).resolve().parent.parent
FONT_PATH = ROOT / "media" / "usage-bar.woff"
PACKAGE_JSON_PATH = ROOT / "package.json"
FONT_PATH_IN_PACKAGE = "./media/usage-bar.woff"
ICON_PREFIX = "claude-usage-bar-"
FAMILY_NAME = "ClaudeUsageBar"
FIRST_CODEPOINT = 0xE000
PERCENT_STEP = 5
UNITS_PER_EM = 1024
ASCENT = 1024
DESCENT = 0
WIN_ASCENT = 1116
WIN_DESCENT = 24
SIDE_MARGIN = 128
BAR_WIDTH = 3328
BAR_HEIGHT = 512
STROKE = 64
GAP = 64


def draw_rounded_rect(pen, left, bottom, width, height):
    radius = min(width, height) / 2
    right = left + width
    top = bottom + height
    points = [
        ("line", (right - radius, top)),
        ("curve", (right, top), (right, top - radius)),
        ("line", (right, bottom + radius)),
        ("curve", (right, bottom), (right - radius, bottom)),
        ("line", (left + radius, bottom)),
        ("curve", (left, bottom), (left, bottom + radius)),
        ("line", (left, top - radius)),
        ("curve", (left, top), (left + radius, top)),
    ]
    start = (left + radius, top)
    pen.moveTo(start)
    current = start
    for kind, *coordinates in points:
        target = coordinates[-1]
        if kind == "curve":
            pen.qCurveTo(coordinates[0], target)
        elif target != current:
            pen.lineTo(target)
        current = target
    pen.closePath()


def build_bar_glyph(percent):
    pen = TTGlyphPen(None)
    bar_bottom = (ASCENT - DESCENT - BAR_HEIGHT) / 2
    draw_rounded_rect(pen, SIDE_MARGIN, bar_bottom, BAR_WIDTH, BAR_HEIGHT)
    hole_inset = STROKE
    draw_rounded_rect(
        ReverseContourPen(pen),
        SIDE_MARGIN + hole_inset,
        bar_bottom + hole_inset,
        BAR_WIDTH - 2 * hole_inset,
        BAR_HEIGHT - 2 * hole_inset,
    )
    fill_inset = STROKE + GAP
    fill_height = BAR_HEIGHT - 2 * fill_inset
    fill_max_width = BAR_WIDTH - 2 * fill_inset
    fill_width = fill_max_width * percent / 100
    if percent > 0:
        draw_rounded_rect(
            pen,
            SIDE_MARGIN + fill_inset,
            bar_bottom + fill_inset,
            max(fill_width, fill_height),
            fill_height,
        )
    return pen.glyph()


def build_font(percents):
    names = [f"bar{percent}" for percent in percents]
    builder = FontBuilder(UNITS_PER_EM, isTTF=True)
    builder.setupGlyphOrder([".notdef", *names])
    builder.setupCharacterMap({FIRST_CODEPOINT + index: name for index, name in enumerate(names)})
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    glyphs.update({name: build_bar_glyph(percent) for name, percent in zip(names, percents)})
    builder.setupGlyf(glyphs)
    advance = BAR_WIDTH + 2 * SIDE_MARGIN
    metrics = {".notdef": (advance, 0)}
    metrics.update({name: (advance, SIDE_MARGIN) for name in names})
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=ASCENT, descent=-DESCENT)
    builder.setupNameTable({"familyName": FAMILY_NAME, "styleName": "Regular"})
    builder.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=-DESCENT,
        sTypoLineGap=0,
        usWinAscent=WIN_ASCENT,
        usWinDescent=WIN_DESCENT,
    )
    builder.setupPost()
    builder.font.flavor = "woff"
    FONT_PATH.parent.mkdir(parents=True, exist_ok=True)
    builder.save(str(FONT_PATH))


def update_package_icons(percents):
    package = json.loads(PACKAGE_JSON_PATH.read_text(encoding="utf-8"))
    package.setdefault("contributes", {})["icons"] = {
        f"{ICON_PREFIX}{percent}": {
            "description": f"Usage bar at {percent}%",
            "default": {
                "fontPath": FONT_PATH_IN_PACKAGE,
                "fontCharacter": f"\\{FIRST_CODEPOINT + index:X}",
            },
        }
        for index, percent in enumerate(percents)
    }
    PACKAGE_JSON_PATH.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    percents = list(range(0, 101, PERCENT_STEP))
    build_font(percents)
    update_package_icons(percents)


if __name__ == "__main__":
    main()
