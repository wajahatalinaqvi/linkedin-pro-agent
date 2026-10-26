"""Human-readable GitHub Actions results. Does not invoke LinkedIn or mutate drafts."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
from post_store import load_post


def format_summary(action: str, post_id: str, outcome: str) -> str:
    if outcome != "success":
        return (f"### {action.title()}: needs attention\n"
                "The job did not complete successfully. Review the failed step and "
                "check LinkedIn before retrying a publish operation.\n")
    if action == "daily" and not post_id:
        return ("### Daily research: no new draft\n"
                "The run completed without selecting a new story. "
                "Check the research logs for the reason (including topic priority, "
                "duplicates, insufficiently strong news, or API limits).\n")
    try:
        post, _ = load_post(post_id)
    except (ValueError, OSError):
        return ("### No matching draft\n"
                "Check the requested draft ID and workflow logs.\n")
    if not post:
        return "### No selected draft\nCheck the workflow logs.\n"
    title = str(post.get("topic", "Untitled")).replace("|", " ").replace("\n", " ")[:160]
    saved_id = str(post.get("id", "unknown"))
    status = str(post.get("status", "unknown"))
    if action == "publish":
        urn = post.get("linkedin_post_id")
        if status == "published" and urn:
            return (f"### LinkedIn publication recorded\n"
                    f"- Story: {title}\n"
                    f"- Draft ID: \`{saved_id}\`\n"
                    f"- LinkedIn post ID: \`{urn}\`\n"
                    "Verify it appears under LinkedIn > Activity > Posts.\n")
        return (f"### Publish status needs checking\n"
                f"- Draft: \`{saved_id}\` (state: {status})\n"
                "The publishing step completed but no confirmed publication ID "
                "was recorded; check LinkedIn and logs before retrying.\n")
    return (f"### New draft prepared, not published\n"
            f"- Story: {title}\n"
            f"- Draft ID: \`{saved_id}\`\n"
            f"- Status: \`{status}\`\n"
            "Download the **linkedin-post-preview** artifact and review it before publishing.\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("daily", "publish"))
    parser.add_argument("--post-id", default="")
    parser.add_argument("--outcome", default="")
    args = parser.parse_args()
    text = format_summary(args.action, args.post_id, args.outcome)
    print(text)
    dest = os.environ.get("GITHUB_STEP_SUMMARY")
    if dest:
        with Path(dest).open("a", encoding="utf-8") as out:
            out.write("\n" + text + "\n")


if __name__ == "__main__":
    main()
