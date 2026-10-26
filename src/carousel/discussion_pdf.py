"""Six-page, vector-based discussion carousel with six deliberately different layouts.

Opt-in via carousel.design_version == 'discussion-v1'. Uses original fact-checked
slide text only and never generates or infers claims. Review before publishing.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

W, H = 1080, 1350
INK, PALE, SIGNAL = "#101D22", "#F6F4ED", "#F06B4E"
MUTED, GRID, SOFT = "#56656A", "#D7DCD5", "#C8DDCC"


def _fonts():
    paths = {
        "Editorial": ["/usr/share/fonts/truetype/lato/Lato-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
        "EditorialBold": ["/usr/share/fonts/truetype/lato/Lato-Black.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "EditorialMedium": ["/usr/share/fonts/truetype/lato/Lato-Semibold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    }
    names = {}
    for label, options in paths.items():
        if label in pdfmetrics.getRegisteredFontNames():
            names[label] = label
            continue
        matched = next((path for path in options if Path(path).exists()), None)
        if matched:
            pdfmetrics.registerFont(TTFont(label, matched))
            names[label] = label
        else:
            names[label] = {"Editorial": "Helvetica", "EditorialBold": "Helvetica-Bold", "EditorialMedium": "Helvetica"}[label]
    return names


def _rect(c, color, x, y, w, h, radius=0):
    c.setFillColor(HexColor(color))
    if radius:
        c.roundRect(x, y, w, h, radius, fill=1, stroke=0)
    else:
        c.rect(x, y, w, h, fill=1, stroke=0)


def _line(c, color, x, y, xx, yy, width=1):
    c.setLineWidth(width)
    c.setStrokeColor(HexColor(color))
    c.line(x, y, xx, yy)


def _text(c, text, x, top, size=26, color=INK, face="Editorial", limit=None):
    font = _fonts()[face]
    c.setFillColor(HexColor(color))
    c.setFont(font, size)
    if limit:
        while pdfmetrics.stringWidth(str(text), font, size) > limit and size > 12:
            size -= 1
            c.setFont(font, size)
    c.drawString(x, H - top - size, str(text))


def _para(c, text, x, top, width, font_size=28, leading=None, color=INK,
          weight="Editorial", max_height=350):
    leading = leading or font_size * 1.35
    style = ParagraphStyle("p", fontName=_fonts()[weight], fontSize=font_size,
                           leading=leading, textColor=HexColor(color), spaceAfter=0,
                           splitLongWords=True, allowWidows=0)
    p = Paragraph(escape(str(text)).replace("\n", "<br/>"), style)
    _, height = p.wrap(width, max_height)
    if height > max_height + 0.01:
        raise ValueError("Text exceeds the available discussion slide height.")
    p.drawOn(c, x, H - top - height)
    return height


def _footer(c, n, dark=False):
    primary = "#DCEBE7" if dark else INK
    _line(c, "#577276" if dark else GRID, 66, 103, W-66, 103, 1)
    _text(c, "WAJAHAT NAQVI", 66, 1264, 18, primary, "EditorialBold")
    _text(c, "AI  /  SOFTWARE ENGINEERING", 265, 1267, 15,
          "#96AAAA" if dark else MUTED)
    _text(c, f"{n:02d} / 06", 910, 1266, 17, primary, "EditorialMedium")


def _header(c, title, n, dark=False):
    _text(c, title.upper(), 66, 59, 19, SIGNAL if dark else "#B85139",
          "EditorialBold")
    _text(c, "FIELD NOTES    /    OCT 2026", 750, 59, 15,
          "#9DB1B1" if dark else MUTED, "EditorialMedium")
    _footer(c, n, dark)


def _cover(c, s):
    _rect(c, INK, 0, 0, W, H)
    _rect(c, SIGNAL, 67, 597, 947, 18)
    c.setStrokeColor(HexColor("#6E9190"))
    c.setLineWidth(5)
    for index in range(4):
        c.roundRect(700 + index*55, 480 - index*53, 380, 500, 38, fill=0, stroke=1)
    _text(c, "01    /    THE AGENT SECURITY QUESTION", 67, 63, 22, SOFT, "EditorialBold")
    for word, y, size, color in (
        ("AI AGENTS", 195, 110, "#F8FAF6"),
        ("ESCAPED", 325, 123, SIGNAL),
        ("TEST", 462, 114, "#F8FAF6"),
        ("SANDBOXES.", 582, 92, "#F8FAF6"),
    ):
        _text(c, word, 63, y, size, color, "EditorialBold")
    _text(c, "IN CONTROLLED RED-TEAM EXERCISES", 74, 763, 23, SOFT, "EditorialBold")
    _para(c, s["subtitle"], 73, 824, 690, font_size=33, leading=44,
          color="#F5F3E8", max_height=190)
    _text(c, "WHAT ACCESS SHOULD WE GIVE CODING AGENTS?",
          74, 1137, 22, SIGNAL, "EditorialBold")
    _footer(c, 1, True)
    c.showPage()


def _reality(c, s):
    _rect(c, PALE, 0, 0, W, H)
    _header(c, "What the report actually says", 2)
    _text(c, "RESEARCH", 66, 176, 100, INK, "EditorialBold")
    _text(c, "NOT PRODUCTION.", 66, 286, 90, SIGNAL, "EditorialBold")
    _line(c, INK, 66, H-475, 1010, H-475, 5)
    _para(c, s["description"], 70, 515, 790, 35, 49, INK, max_height=270)
    _rect(c, "#D7E7DB", 66, 190, 948, 410, radius=10)
    _text(c, "THE DISTINCTION", 97, 760, 21, "#43675D", "EditorialBold")
    _para(c, s["caveat"], 97, 827, 850, 32, 45, INK, max_height=245)
    c.showPage()


def _boundaries(c, s):
    _rect(c, INK, 0, 0, W, H)
    _header(c, "Security architecture", 3, True)
    _text(c, "ONE AGENT.", 67, 149, 94, "#F5F7F4", "EditorialBold")
    _text(c, "SEVERAL BOUNDARIES.", 67, 244, 78, SIGNAL, "EditorialBold")
    _para(c, s["subtitle"], 71, 372, 830, 28, 39, "#D8E7E3", max_height=120)
    nodes = s["nodes"]
    if len(nodes) != 4:
        raise ValueError("Boundary map requires exactly four nodes.")
    # Fixed top-aligned grid: 62 pt below the two-line introduction;
    # 128 pt high rows with identical 42 pt connector gaps. Last row leaves
    # 99 pt to the footer rule at ~1247 pt. Preserve baseline rhythm.
    card_tops = (510, 680, 850, 1020)
    card_height = 128
    for index, (node, top) in enumerate(zip(nodes, card_tops)):
        y = H - top - card_height
        _rect(c, "#26424A" if index % 2 == 0 else "#20363D",
              66, y, 944, card_height, radius=14)
        _rect(c, SIGNAL if index == 3 else SOFT, 66, y, 11, card_height)
        _text(c, f"{index+1:02d}", 98, top+34, 28,
              SIGNAL if index == 3 else SOFT, "EditorialBold")
        _text(c, node["title"].upper(), 182, top+24, 37,
              "#F5F7F4", "EditorialBold", limit=740)
        _text(c, node["note"], 184, top+77, 21,
              "#AEC8C5", limit=760)
        if index < 3:
            _text(c, "↓", 528, top+136, 28, SIGNAL, "EditorialBold")
    c.showPage()


def _response(c, s):
    _rect(c, "#F1EFE6", 0, 0, W, H)
    _header(c, "What changed after the tests", 4)
    _text(c, "THE RESPONSE", 66, 158, 96, INK, "EditorialBold")
    _text(c, "IS LAYERED.", 66, 269, 94, SIGNAL, "EditorialBold")
    items = s["items"]
    if len(items) != 3:
        raise ValueError("Response slide requires exactly three items.")
    for index, item in enumerate(items):
        top = [447, 672, 897][index]
        _rect(c, ["#DAE4DE", "#D7E4DF", "#E8D8CD"][index],
              66, H-top-205, 948, 205, radius=12)
        _text(c, f"0{index+1}", 96, top+23, 66, SIGNAL, "EditorialBold")
        _text(c, item["title"], 219, top+35, 47, INK, "EditorialBold", limit=745)
        _para(c, item["detail"], 221, top+107, 731, 25, 33,
              INK, max_height=78)
    c.showPage()


def _tradeoff(c, s):
    _rect(c, PALE, 0, 0, W, H)
    _header(c, "The engineering tradeoff", 5)
    _text(c, "SPEED", 66, 149, 107, "#1A3D3F", "EditorialBold")
    _text(c, "VS CONTROL", 66, 265, 105, SIGNAL, "EditorialBold")
    _para(c, s["intro"], 69, 410, 850, 26, 38,
          MUTED, max_height=110)
    left, right = 66, 555
    _rect(c, "#DAE7DE", left, 250, 459, 544, radius=12)
    _rect(c, "#1B3D46", right, 250, 459, 544, radius=12)
    _text(c, "MORE AUTONOMY", left+29, 592, 26,
          "#2E6459", "EditorialBold")
    _para(c, s["left"], left+30, 675, 385, 36, 48,
          INK, max_height=320)
    _text(c, "TIGHTER BOUNDARIES", right+28, 592, 25,
          SOFT, "EditorialBold")
    _para(c, s["right"], right+28, 675, 385, 36, 48,
          "#F7F5ED", max_height=320)
    _para(c, s["footnote"], 73, 1142, 910, 23, 32,
          MUTED, max_height=68)
    c.showPage()


def _question(c, s):
    _rect(c, SIGNAL, 0, 0, W, H)
    _header(c, "Your opinion", 6)
    _rect(c, "#F9E1D8", 60, 398, 960, 14)
    for value, top, size, color in (
        ("WHERE", 161, 128, INK),
        ("DO YOU", 292, 121, INK),
        ("DRAW THE", 434, 112, INK),
        ("LINE?", 560, 153, "#F8F6F0"),
    ):
        _text(c, value, 60, top, size, color, "EditorialBold")
    _para(c, s["question"], 70, 812, 900, 42, 58,
          INK, max_height=205)
    _rect(c, INK, 66, 109, 947, 4)
    _text(c, "MY TAKE: DEFAULT TO LEAST PRIVILEGE. EARN BROADER ACCESS.",
          70, 1132, 23, INK, "EditorialBold", limit=935)
    _footer(c, 6)
    c.showPage()


def render_discussion_pdf(data: dict, output_path: str | Path) -> Path:
    if data.get("design_version") != "discussion-v1":
        raise ValueError("Discussion renderer requires design_version=discussion-v1.")
    slides = data.get("slides") or []
    expected = ["debate_cover", "reality_check", "boundary_map",
                "response_layers", "tradeoff", "open_question"]
    if [slide.get("type") for slide in slides] != expected:
        raise ValueError("Discussion deck requires six distinct editorial slide types.")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _fonts()
    c = canvas.Canvas(str(destination), pagesize=(W, H), pageCompression=1)
    c.setTitle("AI agents, sandboxes and developer access | Security debate")
    for draw, slide in zip(
        (_cover, _reality, _boundaries, _response, _tradeoff, _question),
        slides,
    ):
        draw(c, slide)
    c.save()
    return destination
