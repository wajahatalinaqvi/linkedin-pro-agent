"""Editorial, source-led carousel compositions.

Six intentionally distinct page treatments, driven by authentic original-source
screenshots and already-authored text. No generated screen mockups or fake stats.
Missing screenshots MUST NOT produce a purported source-led slide.
"""
from __future__ import annotations

from typing import Any


def _entries(slide: dict, card_data, key: str) -> list[tuple[str, str, str]]:
    return [card_data(item, i) for i, item in enumerate(slide.get(key) or [], 1)][:3]


def _heading(esc, slide: dict, tag: str = "h2") -> str:
    label = esc(slide.get("eyebrow") or "DEVELOPER NOTES")
    title = esc(slide.get("title") or "")
    return f'<div class="se-kicker">{label}</div><{tag} class="se-title">{title}</{tag}>'


def _credit(esc, config: dict) -> str:
    return '<span class="se-credit">ORIGINAL SOURCE · ' + esc(config.get("attribution") or "Publisher") + '</span>'


def _shot(esc, img: str, alt: str, extra: str = "") -> str:
    return (f'<img class="se-shot {extra}" src="{esc(img)}" '
            f'alt="{esc(alt)}">')


def render_source_page(slide: dict, carousel: dict, number: int, image_source,
                       esc, card_data) -> str | None:
    """Return screenshot-led HTML; use None to preserve legacy fallback."""
    if carousel.get("design_version") != "studio-v2":
        return None
    settings = carousel.get("source_visuals") or {}
    if not settings.get("enabled"):
        return None
    paths = settings.get("images") or []
    if len(paths) < 3:
        return None
    images = [image_source(path) for path in paths[:3]]
    # Never substitute a fake UI; if source imagery is unavailable, legacy
    # slides remain intact and do not claim to show the original website.
    if not all(images):
        if settings.get("required"):
            raise ValueError("Source-led layout requires three authentic screenshots.")
        return None
    img_a, img_b, img_c = images
    source = _credit(esc, settings)
    if number == 1:
        subtitle = esc(slide.get("subtitle") or "")
        return (
            '<div class="se-page se-hero">'
            '<div class="se-hero-screenshot">'+_shot(esc,img_a,"Shopify Editions source website")+'</div>'
            '<div class="se-hero-shade"></div>'
            '<div class="se-hero-type"><div class="se-edition">01 / FALL EDITION</div>'
            + _heading(esc,slide,"h1") +
            '<p class="se-intro">'+subtitle+'</p><div class="se-bottom-accent"></div>'
            +source+'</div></div>'
        )
    if number == 2:
        entries = _entries(slide,card_data,"cards")
        details = ''.join(
            '<article class="se-fact"><span>'+esc(marker)+'</span><div><h3>'+
            esc(title)+'</h3><p>'+esc(body)+'</p></div></article>'
            for marker,title,body in entries
        )
        return (
            '<div class="se-page se-impact">'
            '<div class="se-page-heading">'+_heading(esc,slide)+'</div>'
            '<div class="se-impact-body"><figure class="se-impact-photo">'+
            _shot(esc,img_b,"Shopify Editions original feature webpage")+
            '<figcaption>ORIGINAL RELEASE VISUAL</figcaption></figure>'
            '<div class="se-impact-facts">'+details+'</div></div>'
            +'<div class="se-page-foot">'+source+'</div></div>'
        )
    if number == 3:
        left=slide.get("left") or slide.get("before") or {}
        right=slide.get("right") or slide.get("after") or {}
        def side(panel, label, klass):
            points=''.join('<li>'+esc(p)+'</li>' for p in (panel.get("items") or [])[:3])
            return (f'<div class="se-compare-panel {klass}"><span>{esc(label)}</span>'
                    f'<h3>{esc(panel.get("title") or "")}</h3><ul>{points}</ul></div>')
        return (
            '<div class="se-page se-compare">'
            '<div class="se-page-heading">'+_heading(esc,slide)+'</div>'
            '<div class="se-compare-body">'+side(left,left.get("label") or "BEFORE","se-before")+
            '<div class="se-vs">VS</div>'+side(right,right.get("label") or "AFTER","se-after")+
            '</div><div class="se-page-foot">'+source+'</div></div>'
        )
    if number == 4:
        entries = _entries(slide,card_data,"cards")
        labels = ''.join(
            '<article class="se-tool"><span>'+esc(marker)+'</span><strong>'+
            esc(title)+'</strong><p>'+esc(body)+'</p></article>'
            for marker,title,body in entries
        )
        return (
            '<div class="se-page se-mosaic">'
            '<div class="se-page-heading">'+_heading(esc,slide)+'</div>'
            '<div class="se-photo-mosaic"><figure class="se-mosaic-main">'+
            _shot(esc,img_c,"Shopify Editions developer feature website")+
            '</figure><figure class="se-mosaic-side">'+
            _shot(esc,img_a,"Shopify Editions original website overview")+
            '</figure></div><div class="se-tools">'+labels+'</div>'
            '<div class="se-page-foot">'+source+'</div></div>'
        )
    if number == 5:
        entries = _entries(slide,card_data,"events")
        if not entries: entries = _entries(slide,card_data,"steps")
        rows=''.join(
            '<div class="se-signal"><span class="se-index">'+esc(marker)+'</span>'
            '<h3>'+esc(title)+'</h3><p>'+esc(body)+'</p></div>'
            for marker,title,body in entries
        )
        return ('<div class="se-page se-checklist">'
                '<div class="se-page-heading">'+_heading(esc,slide)+'</div>'
                '<div class="se-signals">'+rows+'</div>'
                '<div class="se-page-foot">'+source+'</div></div>')
    if number == 6:
        question = esc(slide.get("discussion_question") or
                       "When AI agents start shopping, who owns the checkout experience?")
        subtitle = esc(slide.get("subtitle") or "")
        return (
            '<div class="se-page se-debate"><div class="se-debate-top">'
            'FIELD NOTES / THE DEVELOPER QUESTION</div>'
            '<div class="se-debate-copy"><div class="se-debate-mark">?</div>'
            '<h1>'+question+'</h1><p>'+subtitle+'</p></div>'
            '<div class="se-debate-bottom"><span>WHAT WOULD YOU BUILD DIFFERENTLY?</span>'
            +source+'</div></div>'
        )
    return None
