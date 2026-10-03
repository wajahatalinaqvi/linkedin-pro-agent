from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Iterable

import requests
from PIL import Image, ImageOps
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

PAGE_W = 1080
PAGE_H = 1350
MARGIN = 86
DEFAULT_ACCENT = "#665CF6"
DARK = "#101116"
TEXT = "#14151B"
MUTED = "#676B78"
LIGHT = "#F4F3EF"


class SlideRenderError(RuntimeError):
    pass


def _clean_hex(value: str, fallback: str = DEFAULT_ACCENT) -> str:
    value = (value or "").strip()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return value
    return fallback


def _wrap(text: str, max_chars: int) -> list[str]:
    words = str(text or "").split()
    if not words:
        return []
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if current and len(candidate) > max_chars:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def _draw_lines(c, lines: Iterable[str], x, y, font, size, color, leading=None, max_lines=None):
    leading = leading or size * 1.2
    c.setFont(font, size)
    c.setFillColor(HexColor(color))
    for index, line in enumerate(lines):
        if max_lines is not None and index >= max_lines:
            break
        c.drawString(x, y, line)
        y -= leading
    return y


def _image_reader(url: str, width: int, height: int):
    if not url:
        return None
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    image = Image.open(BytesIO(response.content)).convert("RGB")
    fitted = ImageOps.fit(image, (max(1, width), max(1, height)), method=Image.Resampling.LANCZOS)
    buf = BytesIO()
    fitted.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return ImageReader(buf)


def _footer(c, slide_no: int, source: str = ""):
    c.setFillColor(HexColor("#A6A8B1"))
    c.setFont("Helvetica", 16)
    c.drawString(MARGIN, 48, "WAJAHAT TECH")
    c.drawRightString(PAGE_W - MARGIN, 48, f"{slide_no:02d}")
    if source:
        source_line = source.replace("https://", "").replace("http://", "")
        if len(source_line) > 72:
            source_line = source_line[:69] + "..."
        c.setFont("Helvetica", 13)
        c.drawCentredString(PAGE_W / 2, 48, source_line)


def _draw_cover(c, slide, accent, category, source):
    c.setFillColor(HexColor(DARK))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(HexColor(accent))
    c.roundRect(MARGIN, PAGE_H - 180, 260, 52, 20, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 19)
    c.drawCentredString(MARGIN + 130, PAGE_H - 162, (category or "TECH UPDATE").upper()[:24])

    y = PAGE_H - 300
    y = _draw_lines(c, _wrap(slide.get("title", ""), 23), MARGIN, y, "Helvetica-Bold", 76, "#FFFFFF", 88, 5)
    subtitle = slide.get("body") or slide.get("subtitle") or ""
    if subtitle:
        y -= 24
        _draw_lines(c, _wrap(subtitle, 52), MARGIN, y, "Helvetica", 31, "#D6D7DF", 42, 5)

    c.setFillColor(HexColor(accent))
    c.rect(MARGIN, 188, 150, 12, fill=1, stroke=0)
    c.setFillColor(HexColor("#D6D7DF"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN, 145, "WHAT CHANGED - WHY IT MATTERS - WHAT TO WATCH")
    _footer(c, 1, source)


def _draw_standard(c, slide, accent, slide_no, source):
    c.setFillColor(HexColor(LIGHT))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    kicker = (slide.get("kicker") or slide.get("eyebrow") or "").upper()
    if kicker:
        c.setFillColor(HexColor(accent))
        c.setFont("Helvetica-Bold", 18)
        c.drawString(MARGIN, PAGE_H - 110, kicker[:40])

    y = PAGE_H - 175
    y = _draw_lines(c, _wrap(slide.get("title", ""), 28), MARGIN, y, "Helvetica-Bold", 55, TEXT, 64, 4)
    has_image = bool(slide.get("image_url", ""))

    body = slide.get("body", "")
    if body:
        y -= 18
        y = _draw_lines(c, _wrap(body, 58 if not has_image else 42), MARGIN, y, "Helvetica", 27, MUTED, 38, 8)

    bullets = slide.get("bullets") or []
    if bullets:
        y -= 22
        for bullet in bullets[:5]:
            c.setFillColor(HexColor(accent))
            c.circle(MARGIN + 8, y + 10, 7, fill=1, stroke=0)
            lines = _wrap(str(bullet), 47 if not has_image else 34)
            y = _draw_lines(c, lines, MARGIN + 32, y, "Helvetica", 25, TEXT, 34, 3)
            y -= 22

    if has_image:
        x, image_y, image_w, image_h = 630, 180, 365, 660
        c.setFillColor(HexColor("#E6E4DE"))
        c.roundRect(x - 12, image_y - 12, image_w + 24, image_h + 24, 28, fill=1, stroke=0)
        try:
            reader = _image_reader(slide.get("image_url", ""), image_w, image_h)
            if reader:
                c.drawImage(reader, x, image_y, image_w, image_h, mask="auto")
        except Exception:
            c.setFillColor(HexColor("#D8D6D0"))
            c.roundRect(x, image_y, image_w, image_h, 22, fill=1, stroke=0)
            c.setFillColor(HexColor(MUTED))
            c.setFont("Helvetica-Bold", 22)
            c.drawCentredString(x + image_w / 2, image_y + image_h / 2, "Visual unavailable")

    _footer(c, slide_no, source)


def _draw_quote(c, slide, accent, slide_no, source):
    c.setFillColor(HexColor(DARK))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(HexColor(accent))
    c.setFont("Helvetica-Bold", 160)
    c.drawString(MARGIN, PAGE_H - 300, '"')
    y = PAGE_H - 390
    y = _draw_lines(c, _wrap(slide.get("title") or slide.get("body") or "", 30), MARGIN, y, "Helvetica-Bold", 55, "#FFFFFF", 68, 7)
    if slide.get("title") and slide.get("body"):
        y -= 24
        _draw_lines(c, _wrap(slide.get("body", ""), 48), MARGIN, y, "Helvetica", 28, "#C8CAD2", 40, 5)
    _footer(c, slide_no, source)


def _draw_closing(c, slide, accent, slide_no, source):
    c.setFillColor(HexColor(LIGHT))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(HexColor(accent))
    c.roundRect(MARGIN, PAGE_H - 188, 180, 14, 7, fill=1, stroke=0)
    y = PAGE_H - 280
    y = _draw_lines(c, _wrap(slide.get("title") or "The takeaway", 26), MARGIN, y, "Helvetica-Bold", 64, TEXT, 74, 4)
    if slide.get("body"):
        y -= 28
        y = _draw_lines(c, _wrap(slide.get("body", ""), 48), MARGIN, y, "Helvetica", 31, MUTED, 43, 7)
    for bullet in (slide.get("bullets") or [])[:4]:
        y -= 22
        c.setFillColor(HexColor(accent))
        c.roundRect(MARGIN, y - 2, 12, 36, 6, fill=1, stroke=0)
        y = _draw_lines(c, _wrap(str(bullet), 46), MARGIN + 34, y, "Helvetica-Bold", 26, TEXT, 36, 3)
    c.setFillColor(HexColor(DARK))
    c.roundRect(MARGIN, 145, PAGE_W - 2 * MARGIN, 145, 26, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 27)
    c.drawString(MARGIN + 34, 232, "Follow for practical AI, Shopify & developer updates")
    c.setFont("Helvetica", 20)
    c.setFillColor(HexColor("#C8CAD2"))
    c.drawString(MARGIN + 34, 190, "Primary sources first. No filler. One useful story at a time.")
    _footer(c, slide_no, source)


def render_document(post: dict, output_path: Path) -> Path:
    document = post.get("document") or {}
    slides = document.get("slides") or []
    if not slides:
        raise SlideRenderError("Document format requires document.slides.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    accent = _clean_hex(document.get("accent", DEFAULT_ACCENT))
    category = post.get("category", "Tech update")
    sources = post.get("sources") or [post.get("source_url", "")]
    source = sources[0] if sources else ""

    c = canvas.Canvas(str(output_path), pagesize=(PAGE_W, PAGE_H))
    c.setTitle(document.get("title") or post.get("topic") or "LinkedIn document")

    for index, slide in enumerate(slides, start=1):
        layout = (slide.get("layout") or ("cover" if index == 1 else "standard")).lower()
        if layout == "cover":
            _draw_cover(c, slide, accent, category, source)
        elif layout in {"quote", "highlight"}:
            _draw_quote(c, slide, accent, index, source)
        elif layout in {"closing", "cta"}:
            _draw_closing(c, slide, accent, index, source)
        else:
            _draw_standard(c, slide, accent, index, source)
        c.showPage()

    c.save()
    return output_path
