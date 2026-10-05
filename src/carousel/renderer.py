from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CSS = (HERE / "carousel.css").read_text(encoding="utf-8")

SUPPORTED_LAYOUTS = {
    "cover", "browser", "code", "network", "architecture", "cards",
    "feature_grid", "comparison", "before_after", "timeline", "metrics",
    "quote", "screenshot", "annotated_screenshot", "workflow", "ecommerce",
    "model_comparison", "closing",
}


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def _lines(value: Any) -> str:
    """Normalize real and literal escaped newlines before rendering."""
    text = str(value or "")
    text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    return esc(text).replace("\n", "<br>")

def _items(values: Iterable[Any], class_name: str = "bullet-list") -> str:
    return f'<ul class="{class_name}">' + "".join(f"<li>{esc(value)}</li>" for value in values) + "</ul>"


def _theme(data: dict) -> str:
    requested = str(data.get("theme", "")).strip().lower()
    if requested in {"openai", "claude", "shopify", "developer"}:
        return requested
    topic = str(data.get("topic", "")).lower()
    if "claude" in topic or "anthropic" in topic:
        return "claude"
    if "shopify" in topic or "ecommerce" in topic:
        return "shopify"
    return "openai"


def _brand(data: dict, number: int) -> str:
    brand = data.get("brand") or {}
    name = brand.get("name") or "WAJAHAT NAQVI"
    subtitle = brand.get("subtitle") or "Shopify · Full-stack · AI"
    return (
        f'<div class="brand-lockup"><b>{esc(name)}</b><span>{esc(subtitle)}</span></div>'
        f'<div class="page-number">{number:02d}</div>'
    )


def _heading(slide: dict, *, large: bool = False) -> str:
    eyebrow = slide.get("eyebrow") or slide.get("kicker") or "FIELD NOTE"
    title_class = "display" if large else "title"
    subtitle = slide.get("subtitle") or slide.get("body") or ""
    return (
        f'<div class="eyebrow">{esc(eyebrow)}</div>'
        f'<h1 class="{title_class}">{_lines(slide.get("title"))}</h1>'
        + (f'<p class="lead">{esc(subtitle)}</p>' if subtitle else "")
    )


def _image_source(value: Any) -> str:
    source = str(value or "").strip()
    if not source:
        return ""
    if source.startswith(("https://", "http://", "data:", "file:")):
        return source
    path = Path(source)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        return ""
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _visual(slide: dict, class_name: str = "media-frame") -> str:
    source = _image_source(slide.get("image") or slide.get("image_url") or slide.get("path"))
    label = slide.get("fallback") or slide.get("image_alt") or "Visual preview"
    fallback = f'<div class="media-fallback"><span></span><b>{esc(label)}</b><small>IMAGE PREVIEW</small></div>'
    if not source:
        return f'<div class="{class_name} image-missing">{fallback}</div>'
    return (
        f'<div class="{class_name}">{fallback}'
        f'<img src="{esc(source)}" alt="{esc(label)}" '
        'onerror="this.style.display=\'none\';this.parentElement.classList.add(\'image-missing\')"></div>'
    )


def _card_data(value: Any, index: int) -> tuple[str, str, str]:
    if isinstance(value, dict):
        return (
            str(value.get("number") or value.get("icon") or f"{index:02d}"),
            str(value.get("title") or value.get("label") or ""),
            str(value.get("body") or value.get("text") or value.get("value") or ""),
        )
    if isinstance(value, (list, tuple)):
        padded = list(value) + ["", "", ""]
        return str(padded[0]), str(padded[1]), str(padded[2])
    return f"{index:02d}", str(value), ""


def _cards(values: Iterable[Any], class_name: str = "card-grid") -> str:
    output = []
    for index, value in enumerate(values, start=1):
        marker, title, body = _card_data(value, index)
        output.append(
            f'<article class="info-card"><span class="card-marker">{esc(marker)}</span>'
            f'<h3>{esc(title)}</h3><p>{esc(body)}</p></article>'
        )
    return f'<div class="{class_name}">' + "".join(output) + "</div>"


def _code_block(slide: dict) -> str:
    raw = slide.get("code") or slide.get("snippet") or "// Example\nconst result = await agent.run(task);"
    if isinstance(raw, list):
        raw = "\n".join(str(line) for line in raw)
    language = slide.get("language") or "CODE"
    return (
        '<div class="code-window"><div class="window-bar"><i></i><i></i><i></i>'
        f'<span>{esc(language)}</span></div><pre>{esc(raw)}</pre></div>'
    )


def _cover(slide: dict) -> str:
    footer = slide.get("footer") or "Swipe for the practical breakdown →"
    return (
        '<div class="cover-grid"></div><div class="cover-orbit orbit-one"></div>'
        '<div class="cover-orbit orbit-two"></div><div class="cover-mark"><i></i><i></i><i></i></div>'
        f'<div class="cover-copy">{_heading(slide, large=True)}</div>'
        f'<div class="cover-footer"><span></span>{esc(footer)}</div>'
    )


def _browser(slide: dict) -> str:
    bullets = slide.get("bullets") or []
    address = slide.get("address") or "agent.workspace / task"
    browser_body = _visual(slide, "browser-canvas") if slide.get("image") or slide.get("image_url") else _code_block(slide)
    return (
        f'<div class="two-column browser-layout"><div>{_heading(slide)}{_items(bullets)}</div>'
        '<div class="browser-shell"><div class="browser-chrome"><i></i><i></i><i></i>'
        f'<span>{esc(address)}</span></div>{browser_body}</div></div>'
    )


def _code(slide: dict) -> str:
    notes = slide.get("bullets") or slide.get("notes") or []
    return f'<div class="code-layout"><div>{_heading(slide)}{_items(notes)}</div>{_code_block(slide)}</div>'


def _network(slide: dict) -> str:
    values = slide.get("nodes") or []
    nodes = "".join(
        f'<div class="satellite sat-{index}"><span></span><b>{esc(value.get("title") if isinstance(value, dict) else value)}</b>'
        f'<small>{esc(value.get("label", "SPECIALIST") if isinstance(value, dict) else "SPECIALIST")}</small></div>'
        for index, value in enumerate(values[:5], start=1)
    )
    center = slide.get("center") or "ORCHESTRATOR"
    return (
        f'<div class="network-layout"><div class="network-copy">{_heading(slide)}</div>'
        f'<div class="network-map"><div class="network-lines"></div><div class="hub"><span></span><b>{esc(center)}</b></div>{nodes}</div></div>'
    )


def _architecture(slide: dict) -> str:
    layers = slide.get("layers") or slide.get("components") or []
    rendered = []
    for index, layer in enumerate(layers[:5], start=1):
        if isinstance(layer, dict):
            title, body = layer.get("title"), layer.get("body") or layer.get("items") or ""
            if isinstance(body, list):
                body = " · ".join(map(str, body))
        else:
            title, body = layer, ""
        rendered.append(f'<div class="arch-layer"><span>{index:02d}</span><b>{esc(title)}</b><p>{esc(body)}</p></div>')
    return f'<div class="architecture-layout">{_heading(slide)}<div class="arch-stack">{"".join(rendered)}</div></div>'


def _feature_grid(slide: dict) -> str:
    return f'<div class="feature-layout">{_heading(slide)}{_cards(slide.get("features") or slide.get("cards") or [], "feature-grid")}</div>'


def _comparison(slide: dict, before_after: bool = False) -> str:
    left = slide.get("left") or slide.get("before") or {}
    right = slide.get("right") or slide.get("after") or {}
    if before_after:
        left = {"label": "BEFORE", **left}
        right = {"label": "AFTER", **right}

    def panel(value: dict, positive: bool) -> str:
        return (
            f'<article class="compare-panel {"positive" if positive else ""}">'
            f'<span>{esc(value.get("label") or ("OPTION B" if positive else "OPTION A"))}</span>'
            f'<h3>{esc(value.get("title"))}</h3>{_items(value.get("items") or [])}</article>'
        )

    return f'<div class="comparison-layout">{_heading(slide)}<div class="comparison-grid">{panel(left, False)}{panel(right, True)}</div></div>'


def _timeline(slide: dict) -> str:
    events = slide.get("events") or slide.get("steps") or []
    rendered = []
    for index, event in enumerate(events[:6], start=1):
        marker, title, body = _card_data(event, index)
        rendered.append(f'<div class="timeline-event"><span>{esc(marker)}</span><div><h3>{esc(title)}</h3><p>{esc(body)}</p></div></div>')
    return f'<div class="timeline-layout">{_heading(slide)}<div class="timeline-track">{"".join(rendered)}</div></div>'


def _metrics(slide: dict) -> str:
    rendered = []
    for index, metric in enumerate((slide.get("metrics") or [])[:4], start=1):
        marker, title, body = _card_data(metric, index)
        rendered.append(f'<article class="metric"><span>{esc(marker)}</span><b>{esc(title)}</b><p>{esc(body)}</p></article>')
    return f'<div class="metrics-layout">{_heading(slide)}<div class="metric-grid">{"".join(rendered)}</div></div>'


def _quote(slide: dict) -> str:
    quote = slide.get("quote") or slide.get("title") or slide.get("body")
    attribution = slide.get("attribution") or slide.get("source") or "Example perspective"
    return (
        '<div class="quote-layout"><div class="quote-glyph">“</div>'
        f'<blockquote>{esc(quote)}</blockquote><div class="quote-rule"></div><p>{esc(attribution)}</p></div>'
    )


def _screenshot(slide: dict, annotated: bool = False) -> str:
    callouts = slide.get("callouts") or []
    annotations = ""
    if annotated:
        annotations = "".join(
            f'<div class="annotation annotation-{index}"><span>{index}</span>{esc(value.get("label") if isinstance(value, dict) else value)}</div>'
            for index, value in enumerate(callouts[:4], start=1)
        )
    return f'<div class="screenshot-layout">{_heading(slide)}<div class="screenshot-stage">{_visual(slide, "screenshot-frame")}{annotations}</div></div>'


def _workflow(slide: dict) -> str:
    rendered = []
    for index, step in enumerate((slide.get("steps") or [])[:6], start=1):
        marker, title, body = _card_data(step, index)
        rendered.append(f'<article class="workflow-step"><span>{index:02d}</span><div><b>{esc(title or marker)}</b><p>{esc(body)}</p></div></article>')
    return f'<div class="workflow-layout">{_heading(slide)}<div class="workflow-rail">{"".join(rendered)}</div></div>'


def _ecommerce(slide: dict) -> str:
    rendered = []
    for product in (slide.get("products") or slide.get("cards") or [])[:3]:
        product = product if isinstance(product, dict) else {"title": str(product)}
        rendered.append(
            '<article class="product-card">'
            f'{_visual(product, "product-image")}<small>{esc(product.get("tag") or "PRODUCT")}</small>'
            f'<h3>{esc(product.get("title"))}</h3><div><b>{esc(product.get("value") or product.get("price") or "")}</b>'
            f'<span>{esc(product.get("meta") or "")}</span></div></article>'
        )
    return f'<div class="commerce-layout">{_heading(slide)}<div class="product-grid">{"".join(rendered)}</div></div>'


def _model_comparison(slide: dict) -> str:
    models = slide.get("models") or slide.get("columns") or []
    rows = slide.get("rows") or []
    headers = "".join(f'<b>{esc(model.get("name") if isinstance(model, dict) else model)}</b>' for model in models[:3])
    body = []
    for row in rows[:5]:
        if isinstance(row, dict):
            values = row.get("values") or []
            body.append(f'<div class="model-row"><span>{esc(row.get("label"))}</span>' + "".join(f'<b>{esc(value)}</b>' for value in values[:3]) + "</div>")
    return f'<div class="model-layout">{_heading(slide)}<div class="model-table"><div class="model-head"><span>BEST FIT</span>{headers}</div>{"".join(body)}</div></div>'


def _closing(slide: dict) -> str:
    source = slide.get("source") or "Example content · replace with a verified primary source"
    return (
        '<div class="closing-glow"></div><div class="closing-copy">'
        f'{_heading(slide, large=True)}<div class="closing-chip">SAVE · SHARE · BUILD</div></div>'
        f'<div class="source-line">{esc(source)}</div>'
    )


def render_slide(slide: dict, data: dict, number: int) -> str:
    layout = str(slide.get("type") or slide.get("layout") or "cards").strip().lower()
    if layout == "split":
        layout = "comparison"
    if layout not in SUPPORTED_LAYOUTS:
        raise ValueError(f"Unsupported V3 carousel layout: {layout}")

    renderers = {
        "cover": _cover,
        "browser": _browser,
        "code": _code,
        "network": _network,
        "architecture": _architecture,
        "cards": lambda item: f'<div class="cards-layout">{_heading(item)}{_cards(item.get("cards") or [])}</div>',
        "feature_grid": _feature_grid,
        "comparison": _comparison,
        "before_after": lambda item: _comparison(item, True),
        "timeline": _timeline,
        "metrics": _metrics,
        "quote": _quote,
        "screenshot": _screenshot,
        "annotated_screenshot": lambda item: _screenshot(item, True),
        "workflow": _workflow,
        "ecommerce": _ecommerce,
        "model_comparison": _model_comparison,
        "closing": _closing,
    }
    content = renderers[layout](slide)
    theme = _theme(data)
    tone = "dark" if layout in {"cover", "code", "network", "architecture", "quote", "closing"} else "light"
    return f'<section class="slide theme-{theme} layout-{layout} {tone}"><div class="slide-inner">{content}</div>{_brand(data, number)}</section>'


def render_html(data: dict) -> str:
    slides = data.get("slides") or []
    if not slides:
        raise ValueError("V3 carousel requires at least one slide.")
    if not 5 <= len(slides) <= 8:
        raise ValueError("V3 carousel requires 5-8 slides.")
    content = "".join(render_slide(slide, data, index) for index, slide in enumerate(slides, start=1))
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=1080, initial-scale=1">'
        f'<style>{CSS}</style></head><body>{content}</body></html>'
    )
