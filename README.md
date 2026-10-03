# Priority-driven LinkedIn Content Agent

A reusable agent that keeps research and preparation separate from manual LinkedIn publishing.

```text
Official sources → candidates → scoring → preview → queue/latest.json → manual approval → LinkedIn API
```

## Capabilities

- Text, image, and PDF document posts
- V3 HTML/CSS carousel renderer with 18 story-driven layouts
- 1080×1350 pages with OpenAI, Claude, Shopify, and developer-tool art direction
- Remote and local image support with graceful visual fallback
- Exact 100-point editorial scoring, history deduplication, and expiring backlog
- LinkedIn official Posts, Images, and Documents APIs only
- Safe dry-run behavior and manual-only GitHub publishing
- Legacy `src/slides.py` renderer retained as a fallback

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

Keep LinkedIn credentials in local environment variables or GitHub Secrets. Never commit them.

## Research and preparation

`AGENT_PROMPT.md` defines the source, narrative, scoring, and visual contract. Place researched candidates in the ignored `queue/candidates.json` file, then run:

```powershell
.venv\Scripts\python.exe src\prepare.py --candidates queue\candidates.json
```

The preparation command:

1. validates the candidate scores and official-source claims;
2. removes stories already represented in `data/history.json`;
3. combines fresh candidates with the non-stale backlog;
4. selects at most one strongest story;
5. chooses text, image, or V3 document format;
6. renders a document preview before writing `status=ready`;
7. updates `queue/latest.json` and stops.

It does not import the LinkedIn client, read publishing secrets, or publish anything.

## V3 carousel rendering

New document posts use:

```json
{
  "format": "document",
  "document": {
    "renderer": "v3",
    "carousel": {
      "theme": "openai",
      "brand": {
        "name": "WAJAHAT NAQVI",
        "subtitle": "Shopify · Full-stack · AI"
      },
      "slides": []
    }
  }
}
```

V3 supports `cover`, `browser`, `code`, `network`, `architecture`, `cards`, `feature_grid`, `comparison`, `before_after`, `timeline`, `metrics`, `quote`, `screenshot`, `annotated_screenshot`, `workflow`, `ecommerce`, `model_comparison`, and `closing`. Each carousel must contain 5–8 slides.

Render the current queued document without publishing:

```powershell
.venv\Scripts\python.exe src\publish.py --render-only
```

Render an individual example:

```powershell
.venv\Scripts\python.exe src\carousel\render_pdf.py examples\carousels\openai.json --output generated\examples\openai.pdf
```

## Manual publishing only

The GitHub workflow uses `workflow_dispatch` only and requires `confirm=PUBLISH`. It has no schedule or cron. Publishing uses the official LinkedIn API in `src/linkedin.py`.

Never automate LinkedIn browser interaction, likes, comments, DMs, connections, or reposts.

Required GitHub Secrets:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN`

Optional repository variable:

- `LINKEDIN_VERSION` (defaults to `202609`)

## Mobile review workflow

LinkedIn's mobile document viewer adds its own title and page-count controls over the top of a PDF. V3 therefore keeps readable content inside reusable mobile-safe tokens: 170px at the top, 110px at the bottom, and 80px on each side. Decorative glows and shapes may still extend to the page edges.

Use this review sequence:

```text
Research/preparation
→ queue/latest.json = ready
→ Preview prepared LinkedIn post workflow
→ download/open linkedin-post-preview
→ review preview-summary.txt and the PDF
→ if approved
→ manually run Publish approved LinkedIn post
→ type PUBLISH
→ LinkedIn official API publishes
```

The preview workflow can run manually, and also runs when `queue/latest.json` changes on `main`. It has read-only repository permissions, receives no LinkedIn secrets, never calls LinkedIn, and cannot change queue status or publication history. Its `linkedin-post-preview` artifact is retained for seven days and is downloadable from the GitHub Actions run on desktop or phone.

The publish workflow is separate. It runs only through `workflow_dispatch` and only after the operator types `PUBLISH`.

## Safety checks

```powershell
.venv\Scripts\python.exe -m py_compile src\linkedin.py src\publish.py src\carousel\renderer.py src\carousel\render_pdf.py src\prepare.py
.venv\Scripts\python.exe src\publish.py
git diff --check
```

The default publisher run validates the queue and remains a dry run unless the explicit manual publishing controls are satisfied.

## License

MIT
