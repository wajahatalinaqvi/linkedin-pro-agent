"""Offline draft management. Does not publish or contact LinkedIn."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from post_store import ROOT, create_draft, list_drafts, select_draft


def main() -> None:
    parser = argparse.ArgumentParser(description="Import, list and select LinkedIn drafts.")
    sub = parser.add_subparsers(dest="action", required=True)
    add = sub.add_parser("import", help="Import a source-verified ready-post JSON file.")
    add.add_argument("file")
    add.add_argument("--select", action="store_true")
    choose = sub.add_parser("select", help="Select saved draft for legacy queue/latest.json.")
    choose.add_argument("post_id")
    sub.add_parser("list")
    args = parser.parse_args()
    if args.action == "import":
        path = Path(args.file)
        if not path.is_absolute():
            path = ROOT / path
        post = json.loads(path.read_text(encoding="utf-8"))
        dest = create_draft(post, select=args.select)
        print(f"SAVED: {dest.relative_to(ROOT)}")
    elif args.action == "select":
        select_draft(args.post_id)
        print(f"SELECTED: {args.post_id}")
    elif args.action == "list":
        for item in list_drafts():
            print(f"{item['id']} | {item['status']} | {item['topic']}")


if __name__ == "__main__":
    main()
