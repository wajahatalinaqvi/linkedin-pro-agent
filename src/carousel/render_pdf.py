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




def _audit_studio_layout(page) -> None:
    """Reject unsafe card geometry in newly generated Studio V2 PDFs.

    Browser geometry checks catch collisions and clipped card text that Python
    unit tests cannot see. Legacy and discussion designs remain unchanged.
    """
    issues = page.evaluate("""() => {
      const problems = [];
      const rect = el => el.getBoundingClientRect();
      const overlaps = (a, b) => Math.min(a.right,b.right) > Math.max(a.left,b.left) + 2
                            && Math.min(a.bottom,b.bottom) > Math.max(a.top,b.top) + 2;
      document.querySelectorAll('section.slide.design-v2').forEach((slide, pageIndex) => {
        const frame = rect(slide);
        slide.querySelectorAll('.feature-grid').forEach(grid => {
          const cards = [...grid.querySelectorAll(':scope > .info-card')];
          const found = (grid.className.match(/card-count-(\\d+)/) || [])[1];
          if (Number(found) !== cards.length) {
            problems.push('Slide '+(pageIndex+1)+': card count does not match grid');
          }
          const boxes = cards.map(rect);
          boxes.forEach((box, index) => {
            if (box.left < frame.left + 45 || box.right > frame.right - 45) {
              problems.push('Slide '+(pageIndex+1)+': card '+(index+1)+' breaches side margins');
            }
            if (box.bottom > frame.bottom - 110) {
              problems.push('Slide '+(pageIndex+1)+': card '+(index+1)+' intersects footer space');
            }
            const children = [...cards[index].querySelectorAll('h3,p')];
            children.forEach(node => {
              const r = rect(node);
              if (r.left < box.left + 12 || r.right > box.right - 12 ||
                  r.bottom > box.bottom - 10 || r.top < box.top + 8) {
                problems.push('Slide '+(pageIndex+1)+': text extends beyond card '+(index+1));
              }
              if (node.scrollWidth > node.clientWidth + 4 ||
                  node.scrollHeight > node.clientHeight + 4) {
                problems.push('Slide '+(pageIndex+1)+': card text is clipped');
              }
            });
          });
          for (let a=0;a<boxes.length;a++) {
            for (let b=a+1;b<boxes.length;b++) {
              if(overlaps(boxes[a],boxes[b])) {
                problems.push('Slide '+(pageIndex+1)+': cards '+(a+1)+' and '+(b+1)+' overlap');
              }
            }
          }
        });
      });
      return problems;
    }""")
    if issues:
        raise ValueError("Studio V2 layout rejected before PDF export: " + "; ".join(issues[:6]))

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
            if data.get("design_version") == "studio-v2":
                _audit_studio_layout(page)
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
