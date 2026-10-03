from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

try:
    from .renderer import render_html
except ImportError:
    from renderer import render_html


ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIR = ROOT / "generated"


def render_carousel_pdf(data: dict, output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html = render_html(data)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1080, "height": 1350})
            page.emulate_media(media="print")
            page.set_content(html, wait_until="load")
            try:
                page.wait_for_function(
                    "Array.from(document.images).every(image => image.complete)",
                    timeout=8_000,
                )
            except Exception:
                page.evaluate(
                    """Array.from(document.images)
                    .filter(image => !image.complete)
                    .forEach(image => {
                      image.style.display = 'none';
                      image.parentElement.classList.add('image-missing');
                    })"""
                )
            page.pdf(
                path=str(output_path),
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    parser.add_argument("--output", default=None)

    args = parser.parse_args()

    json_path = Path(args.json_file)

    if not json_path.is_absolute():
        json_path = ROOT / json_path

    data = json.loads(
        json_path.read_text(encoding="utf-8")
    )

    if args.output:
        output = Path(args.output)

        if not output.is_absolute():
            output = ROOT / output
    else:
        output = GENERATED_DIR / f"{json_path.stem}.pdf"

    rendered = render_carousel_pdf(
        data,
        output,
    )

    print(f"RENDERED: {rendered}")


if __name__ == "__main__":
    main()
