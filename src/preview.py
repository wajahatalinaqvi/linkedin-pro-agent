from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from post_store import load_post

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "queue" / "latest.json"
GENERATED_DIR = ROOT / "generated"


def load_queue() -> dict:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def source_urls(post: dict) -> list[str]:
    values = []
    for source in [post.get("source_url"), *(post.get("sources") or [])]:
        if isinstance(source, str):
            url = source.strip()
        elif isinstance(source, dict):
            url = str(source.get("url", "")).strip()
        else:
            url = ""
        if url and url not in values:
            values.append(url)
    return values


def document_path(post: dict) -> Path:
    document = post.get("document") or {}
    configured = str(document.get("path", "")).strip()
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else ROOT / path
    return GENERATED_DIR / f"{post['id']}.pdf"


def write_summary(post: dict, output_path: Path) -> Path:
    sources = source_urls(post)
    lines = [
        "LinkedIn post preview",
        "=====================",
        "",
        f"Topic: {post.get('topic', '')}",
        f"Category: {post.get('category', '')}",
        f"Priority score: {post.get('priority_score', '')}",
        f"Format: {post.get('format', 'text')}",
        "",
        "Caption:",
        str(post.get("caption", "")),
        "",
        f"Source URL: {post.get('source_url', '')}",
        "",
        "All sources:",
        *[f"- {url}" for url in sources],
        "",
        "Review only. This artifact cannot publish to LinkedIn.",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def write_github_outputs(values: dict[str, str], output_file: str) -> None:
    if not output_file:
        return
    with Path(output_file).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare metadata for a read-only LinkedIn preview artifact.")
    parser.add_argument("--post-id", default="", help="Optional saved draft ID; any status can be previewed.")
    parser.add_argument("--summary", default="generated/preview-summary.txt")
    parser.add_argument("--github-output", default=os.getenv("GITHUB_OUTPUT", ""))
    args = parser.parse_args()

    post, _ = load_post(args.post_id)
    status = str(post.get("status", "idle")).strip().lower()
    post_format = str(post.get("format", "text")).strip().lower()
    outputs = {"ready": "false", "format": post_format, "document_path": ""}

    if status not in {"ready", "published", "skipped"} or not post.get("id"):
        write_github_outputs(outputs, args.github_output)
        print(f"PREVIEW SKIPPED: no complete saved post is selected (status={status!r}).")
        return 0

    summary = Path(args.summary)
    if not summary.is_absolute():
        summary = ROOT / summary
    write_summary(post, summary)
    outputs["ready"] = "true"

    if post_format == "document":
        path = document_path(post).resolve()
        try:
            outputs["document_path"] = path.relative_to(ROOT.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError("Preview documents must stay inside the repository workspace.") from exc

    write_github_outputs(outputs, args.github_output)
    print(f"PREVIEW READY: {post.get('topic', '')}")
    print(f"SUMMARY: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
