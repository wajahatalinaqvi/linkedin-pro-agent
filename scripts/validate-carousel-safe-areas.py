from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from carousel.renderer import SUPPORTED_LAYOUTS, render_html  # noqa: E402

SAFE_TOP = 170
SAFE_BOTTOM = 110
SAFE_X = 80
PAGE_WIDTH = 1080
PAGE_HEIGHT = 1350

CRITICAL_SELECTOR = ",".join(
    [
        ".eyebrow", ".title", ".display", ".lead", ".bullet-list",
        ".browser-shell", ".code-window", ".network-map", ".arch-stack",
        ".card-grid", ".feature-grid", ".comparison-grid", ".timeline-track",
        ".metric-grid", "blockquote", ".screenshot-stage", ".workflow-rail",
        ".product-grid", ".model-table", ".cover-footer", ".source-line",
        ".brand-lockup", ".page-number",
    ]
)


def load_example(name: str) -> dict:
    path = ROOT / "examples" / "carousels" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def supplemental_layouts() -> dict:
    return {
        "theme": "developer",
        "topic": "Safe-area validation",
        "slides": [
            {"type": "cover", "eyebrow": "VALIDATION", "title": "Safe-area layout check", "subtitle": "Synthetic content used only for local rendering QA."},
            {"type": "code", "eyebrow": "CODE", "title": "Readable implementation detail", "code": "const safe = true;\nawait render(safe);", "bullets": ["Example note", "Example check"]},
            {"type": "cards", "eyebrow": "CARDS", "title": "Three concise decisions", "cards": [["01", "First", "Example detail"], ["02", "Second", "Example detail"], ["03", "Third", "Example detail"]]},
            {"type": "screenshot", "eyebrow": "SCREENSHOT", "title": "Interface evidence stays visible", "image": "examples/assets/agent-console.svg", "image_alt": "Synthetic agent console"},
            {"type": "closing", "eyebrow": "COMPLETE", "title": "Safe by design", "subtitle": "Synthetic validation content.", "source": "Local layout validation"},
        ],
    }


def validate_page(page, data: dict, label: str, screenshot_dir: Path | None) -> list[str]:
    page.set_content(render_html(data), wait_until="load")
    page.evaluate("document.fonts.ready")
    errors = []
    slides = page.locator("section.slide")
    for index in range(slides.count()):
        slide = slides.nth(index)
        slide_box = slide.bounding_box()
        layout = slide.get_attribute("class") or "unknown"
        if not slide_box:
            errors.append(f"{label} slide {index + 1}: no bounding box")
            continue
        elements = slide.locator(CRITICAL_SELECTOR)
        for element_index in range(elements.count()):
            element = elements.nth(element_index)
            box = element.bounding_box()
            if not box or box["width"] == 0 or box["height"] == 0:
                continue
            left = box["x"] - slide_box["x"]
            top = box["y"] - slide_box["y"]
            right = left + box["width"]
            bottom = top + box["height"]
            name = element.get_attribute("class") or element.evaluate("node => node.tagName.toLowerCase()")
            if left < SAFE_X - 1 or right > PAGE_WIDTH - SAFE_X + 1:
                errors.append(f"{label} slide {index + 1} ({layout}) {name}: horizontal bounds {left:.1f}–{right:.1f}")
            if top < SAFE_TOP - 1 or bottom > PAGE_HEIGHT - SAFE_BOTTOM + 1:
                errors.append(f"{label} slide {index + 1} ({layout}) {name}: vertical bounds {top:.1f}–{bottom:.1f}")
        if screenshot_dir:
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            slide.screenshot(path=str(screenshot_dir / f"{label}-{index + 1:02d}.png"))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate readable V3 content against LinkedIn mobile safe areas.")
    parser.add_argument("--screenshots", help="Optional directory for per-slide QA screenshots.")
    args = parser.parse_args()
    screenshot_dir = Path(args.screenshots) if args.screenshots else None

    datasets = [(name, load_example(name)) for name in ("openai", "claude", "shopify")]
    datasets.append(("supplemental", supplemental_layouts()))
    queue = json.loads((ROOT / "queue" / "latest.json").read_text(encoding="utf-8"))
    carousel = (queue.get("document") or {}).get("carousel")
    if carousel:
        datasets.append(("current-queue", carousel))
    errors = []
    covered = {
        str(slide.get("type") or slide.get("layout") or "cards").strip().lower()
        for _, data in datasets
        for slide in data.get("slides", [])
    }
    covered.discard("split")
    missing = SUPPORTED_LAYOUTS - covered
    if missing:
        errors.append(f"Missing layout coverage: {', '.join(sorted(missing))}")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": PAGE_WIDTH, "height": PAGE_HEIGHT})
            for label, data in datasets:
                errors.extend(validate_page(page, data, label, screenshot_dir))
        finally:
            browser.close()

    if errors:
        print("SAFE-AREA VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SAFE-AREA VALIDATION PASSED: all 18 layouts remain inside 170/110/80 readable bounds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
