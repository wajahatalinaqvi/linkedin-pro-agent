# LinkedIn Pro Agent

A priority-driven content agent for preparing high-quality **LinkedIn + X** posts from the same verified technology story while keeping final publishing under human control.

```text
Official primary sources
        ↓
Research + candidate scoring
        ↓
Strongest eligible story
        ↓
LinkedIn version + X version
        ↓
queue/latest.json = ready
        ↓
GitHub preview
        ↓
Human decision
   ├── PUBLISH → LinkedIn
   └── SKIP    → record decision

X → review x_post → copy/paste manually
```

## What it does

- Prioritizes major OpenAI, Anthropic / Claude, AI-agent, developer-tool, Shopify, and ecommerce-automation stories.
- Uses a 100-point editorial score:
  - significance: 0–30
  - freshness: 0–20
  - developer/business impact: 0–20
  - novelty: 0–15
  - source quality: 0–10
  - profile relevance: 0–5
- Selects at most one strongest story per preparation run.
- Rejects duplicate published stories and stories previously skipped.
- Keeps strong secondary candidates in a short-lived backlog.
- Supports **text**, **single-image**, and **PDF carousel/document** LinkedIn posts.
- Produces a separate platform-appropriate **X post** for the same story.
- Stores primary source URLs in the queue and preview so claims can be checked before publishing.
- Uses the official LinkedIn API only for approved LinkedIn publication.
- Keeps X completely manual: no Metricool, no X API, no automated browser posting.

## Editorial priority

The agent does not use a fixed weekday topic rotation. It evaluates all current candidates and picks the strongest eligible story.

Priority order is used as a tie-breaker:

1. Major OpenAI releases
2. Major Anthropic / Claude releases
3. Important AI-agent developments
4. Important AI and developer-tool releases
5. Shopify platform and developer updates
6. Ecommerce automation
7. Evergreen developer insight only when no fresh story qualifies

Primary sources are preferred. Examples include official OpenAI, Anthropic, Shopify, and GitHub changelogs, documentation, release notes, and product announcements.

## LinkedIn format selection

The post format is chosen from the story rather than forcing everything into a carousel.

### Text

Best for a concise update, observation, or developer takeaway that does not need a visual.

### Single image

Best when one branded visual can communicate the story clearly.

The queue can include:

```json
{
  "format": "image",
  "image_url": "https://...",
  "image_alt": "Accessible description"
}
```

### PDF carousel

Best for stories that benefit from explanation, architecture, comparisons, workflows, timelines, or several distinct takeaways.

New document posts use the V3 HTML/CSS renderer:

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

V3 supports these story-driven layouts:

`cover`, `browser`, `code`, `network`, `architecture`, `cards`, `feature_grid`, `comparison`, `before_after`, `timeline`, `metrics`, `quote`, `screenshot`, `annotated_screenshot`, `workflow`, `ecommerce`, `model_comparison`, and `closing`.

Carousels normally contain 5–8 slides depending on story complexity.

## LinkedIn + X from one story

A prepared queue item is designed to carry both platform versions.

LinkedIn gets the fuller professional explanation and, when useful, a visual asset.

X gets a separate concise version such as:

```json
{
  "x_post": "A short platform-specific version of the same story.",
  "x_thread": []
}
```

The X copy should be written for X rather than being a truncated LinkedIn caption.

**X publishing is manual-only.** Review `x_post`, then copy and paste it into X yourself. This avoids Metricool fees and X API costs.

## Sources and links

Every prepared story should keep its source data in the queue:

```json
{
  "source_url": "https://official-source.example/article",
  "sources": [
    "https://official-source.example/article"
  ]
}
```

The LinkedIn caption can include a short source line such as:

```text
Source: OpenAI API Changelog
```

The full URLs remain available in `queue/latest.json` and the GitHub preview summary for verification before publication.

Do not invent dates, benchmarks, capabilities, quotes, availability, or metrics.

## Daily workflow

A companion scheduled ChatGPT task can prepare the same LinkedIn + X story **Monday–Friday at 11:00 AM Asia/Karachi**.

Normal flow:

```text
11:00 AM
↓
Research strongest fresh story
↓
If an existing queue item is still ready, do not overwrite it
↓
Prepare LinkedIn content + X copy
↓
Write queue/latest.json with status=ready
↓
Preview workflow runs automatically
↓
Review
↓
PUBLISH or SKIP
```

When a post is ready, the notification should begin with:

```text
NEW POST READY — <topic>
```

If no story is strong enough, the agent should create no filler post.

## Queue states

`queue/latest.json` is the handoff between preparation and approval.

Typical states:

- `ready` — waiting for review
- `published` — successfully published to LinkedIn
- `skipped` — intentionally rejected
- `idle` — no eligible story

A new story should never overwrite an existing `ready` item that still needs a human decision.

## GitHub review and approval

### Preview

**Preview prepared LinkedIn post**

Runs automatically when `queue/latest.json` changes on `main`, and can also be run manually.

For a ready post it creates the `linkedin-post-preview` artifact. The preview summary includes:

- topic
- category
- priority score
- post format
- LinkedIn caption
- source URL
- full source list

For document posts the rendered PDF is included in the artifact.

The preview workflow has read-only repository permission and does not receive LinkedIn publishing secrets.

### Publish

**Publish approved LinkedIn post**

Manual only.

Run it from GitHub Actions and type:

```text
PUBLISH
```

The workflow then uses the official LinkedIn API and records the result in `data/history.json` and `queue/latest.json`.

There is intentionally no scheduled LinkedIn publishing.

### Skip

**Skip current LinkedIn post**

If you do not want to publish the current story, run the workflow and type:

```text
SKIP
```

The decision is recorded in `data/skipped.json`, the queue becomes skipped, and the preparation system excludes the same story/source from future selection.

## Mobile-safe carousel design

LinkedIn's mobile document viewer places its own controls over part of the PDF.

V3 therefore keeps important readable content inside reusable safe areas:

- top: 170px
- bottom: 110px
- left/right: 80px

Decorative shapes may bleed outside these boundaries, but essential text should remain inside them.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

If PowerShell blocks virtual-environment activation, invoke the interpreter directly:

```powershell
.venv\Scripts\python.exe
```

## Manual research/preparation

The repository also supports local preparation from candidate JSON.

Create `queue/candidates.json`, then run:

```powershell
.venv\Scripts\python.exe src\prepare.py --candidates queue\candidates.json
```

The preparation command:

1. validates score ranges and official-source claims;
2. excludes published and skipped stories;
3. combines fresh candidates with the non-stale backlog;
4. selects at most one strongest story;
5. chooses text, image, or document format;
6. renders a local V3 preview for document posts;
7. writes `queue/latest.json` with `status=ready`;
8. stops without publishing.

## Render a queued carousel locally

```powershell
.venv\Scripts\python.exe src\publish.py --render-only
```

Render an example directly:

```powershell
.venv\Scripts\python.exe src\carousel\render_pdf.py examples\carousels\openai.json --output generated\examples\openai.pdf
```

## LinkedIn credentials

Keep credentials in local environment variables or GitHub Secrets. Never commit them.

Required GitHub Secrets:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN`

Optional repository variable:

- `LINKEDIN_VERSION` — defaults to `202609`

## Safety boundaries

This project intentionally separates preparation from publication.

It does **not** automate:

- LinkedIn browser interaction
- likes
- comments
- DMs
- connection requests
- reposts
- X posting
- X engagement

LinkedIn publication requires explicit human approval. X remains manual copy/paste.

## Validation

```powershell
.venv\Scripts\python.exe -m py_compile src\linkedin.py src\publish.py src\carousel\renderer.py src\carousel\render_pdf.py src\prepare.py src\skip.py
.venv\Scripts\python.exe src\publish.py
git diff --check
```

The default publisher run remains a dry run unless the explicit manual publishing controls are satisfied.

## Repository

`wajahatalinaqvi/linkedin-pro-agent`

## License

MIT
