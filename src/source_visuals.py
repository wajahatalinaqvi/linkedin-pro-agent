"""Capture real, attributable screenshots from a verified source webpage.

Screenshots are source material for editorial commentary, not simulated UIs.
No synthetic claim or fake image is substituted if the capture fails.
For source-led posts, outputs remain stable across preview and publish because
the preparing workflow commits the image assets next to the saved draft.
"""
from __future__ import annotations

import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "queue" / "assets"


def _safe_source(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Source screenshots require an HTTPS publisher URL.")
    host = parsed.hostname.lower().rstrip(".")
    try:
        address = ipaddress.ip_address(host)
        raise ValueError("An IP address cannot be a source screenshot host.")
    except ValueError as exc:
        if "cannot be a source" in str(exc):
            raise
    config = json.loads((ROOT / "config/official_sources.json").read_text(encoding="utf-8"))
    approved = [urlparse(s["url"]).hostname for s in config.get("sources", [])]
    if not any(host == h or host.endswith("." + h) for h in approved if h):
        raise ValueError("Screenshot host is not on the verified source list.")


def build_visual_config(post_id: str, url: str, *, required: bool = False) -> dict:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,128}", post_id):
        raise ValueError("Invalid draft ID for source asset storage.")
    _safe_source(url)
    folder = f"queue/assets/{post_id}"
    return {
        "enabled": True, "required": required, "url": url,
        "attribution": urlparse(url).hostname,
        "images": [f"{folder}/source-{i}.jpg" for i in range(1,4)],
        "design_system": "source-editorial",
        "capture_method": "real_browser_screenshot",
    }


def ensure_source_images(data: dict, *, root: Path = ROOT) -> list[str]:
    config = data.get("source_visuals") or {}
    if not config.get("enabled"):
        return []
    url = str(config.get("url") or "").strip()
    _safe_source(url)
    images = config.get("images") or []
    if len(images) != 3:
        raise ValueError("Source-led design requires three screenshot paths.")
    targets = [(root / str(img)).resolve() for img in images]
    allowed = (root / "queue" / "assets").resolve()
    if not all(t.is_relative_to(allowed) and t.suffix.lower() == ".jpg" for t in targets):
        raise ValueError("Source image paths must stay inside queue/assets.")
    if all(t.exists() and t.stat().st_size > 10000 for t in targets):
        return [str(t) for t in targets]
    from playwright.sync_api import sync_playwright
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900},
                                        device_scale_factor=1, reduced_motion="reduce")
                page.goto(url, wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(1900)
                # Original site screenshot, not generated art. Intentional overlap
                # between scroll positions retains actual source context.
                for index, target in enumerate(targets):
                    page.evaluate("(offset) => window.scrollTo(0, offset)", index * 850)
                    page.wait_for_timeout(600)
                    page.screenshot(path=str(target), type="jpeg", quality=83,
                                    animations="disabled", full_page=False)
            finally:
                browser.close()
    except Exception as exc:
        if config.get("required"):
            raise ValueError(f"Required official screenshots could not be captured: {type(exc).__name__}") from exc
        print(f"SOURCE VISUALS UNAVAILABLE: {type(exc).__name__}; using editorial slides.")
        for target in targets:
            if target.exists() and target.stat().st_size < 10000:
                target.unlink()
        return []
    valid = all(p.exists() and p.stat().st_size > 10000 for p in targets)
    if not valid and config.get("required"):
        raise ValueError("Source capture created incomplete images.")
    return [str(t) for t in targets] if valid else []
