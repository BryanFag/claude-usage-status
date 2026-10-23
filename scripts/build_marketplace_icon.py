from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = ROOT / "media" / "icon.png"
SYMBOL_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
CLAUDE_MARK = "✻"
ICON_SIZE = 128
SUPERSAMPLE = 4
CANVAS = ICON_SIZE * SUPERSAMPLE
BACKGROUND = "#1E1E1E"
ORANGE = "#D97757"
CORNER_RADIUS = 96
MARK_SIZE = 210
MARK_CENTER_Y = 190
BAR_LEFT = 72
BAR_WIDTH = CANVAS - 2 * BAR_LEFT
BAR_HEIGHT = 96
BAR_CENTER_Y = 352
BAR_STROKE = 16
BAR_GAP = 16
BAR_FILL_PERCENT = 65


def draw_pill(draw, left, top, size, **style):
    pill_width, pill_height = size
    draw.rounded_rectangle([left, top, left + pill_width, top + pill_height], radius=pill_height / 2, **style)


def build_icon():
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([0, 0, CANVAS - 1, CANVAS - 1], radius=CORNER_RADIUS, fill=BACKGROUND)
    mark_font = ImageFont.truetype(SYMBOL_FONT_PATH, MARK_SIZE)
    draw.text((CANVAS / 2, MARK_CENTER_Y), CLAUDE_MARK, font=mark_font, fill=ORANGE, anchor="mm")
    bar_top = BAR_CENTER_Y - BAR_HEIGHT / 2
    draw_pill(draw, BAR_LEFT, bar_top, (BAR_WIDTH, BAR_HEIGHT), outline=ORANGE, width=BAR_STROKE)
    fill_inset = BAR_STROKE + BAR_GAP
    fill_height = BAR_HEIGHT - 2 * fill_inset
    fill_width = (BAR_WIDTH - 2 * fill_inset) * BAR_FILL_PERCENT / 100
    draw_pill(draw, BAR_LEFT + fill_inset, bar_top + fill_inset, (fill_width, fill_height), fill=ORANGE)
    ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS).save(ICON_PATH)


if __name__ == "__main__":
    build_icon()
