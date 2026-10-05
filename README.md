# LinkedIn Pro Agent

A priority-driven LinkedIn content agent that researches strong technology stories, prepares professional LinkedIn posts, generates previews, and keeps final publication under explicit human control.

Built and maintained by **[Wajahat Naqvi](https://github.com/wajahatalinaqvi)** — a Shopify-focused full-stack developer working across React, Laravel, ecommerce automation, and practical AI workflows.

[Portfolio](https://wajahatalinaqvi.github.io/) · [GitHub Profile](https://github.com/wajahatalinaqvi) · [LinkedIn](https://www.linkedin.com/in/wajahatnaqvi-developer/)

## How it works

```text
Official primary sources
        ↓
Research + candidate scoring
        ↓
Strongest eligible story
        ↓
Prepare LinkedIn content
        ↓
queue/latest.json = ready
        ↓
GitHub preview
        ↓
Human review
   ├── PUBLISH → LinkedIn
   └── SKIP    → record decision
```

The repository intentionally separates **content preparation**, **preview**, and **publication** so developers can work on each stage safely.

## What the agent does

- Prioritizes major OpenAI, Anthropic / Claude, AI-agent, developer-tool, Shopify, and ecommerce-automation stories.
- Uses a 100-point editorial score:
  - significance: 0–30
  - freshness: 0–20
  - developer/business impact: 0–20
  - novelty: 0–15
  - source quality: 0–10
  - profile relevance: 0–5
- Selects at most one strongest story per preparation run.
- Rejects already-published stories and stories previously skipped.
- Keeps useful secondary candidates in a short-lived backlog.
- Supports LinkedIn **text**, **single-image**, and **PDF carousel/document** posts.
- Stores verified primary-source URLs with every prepared story.
- Uses the official LinkedIn API only after explicit approval.
- Never automates likes, comments, DMs, connection requests, reposts, or other engagement.

## Editorial priority

The agent does not rely on a fixed weekday topic rotation. It evaluates current candidates and selects the strongest eligible story.

Priority order is used as a tie-breaker:

1. Major OpenAI releases
2. Major Anthropic / Claude releases
3. Important AI-agent developments
4. Important AI and developer-tool releases
5. Shopify platform and developer updates
6. Ecommerce automation
7. Evergreen developer insight only when no fresh story qualifies

Primary sources are preferred, including official changelogs, documentation, release notes, and product announcements.

## LinkedIn format selection

The story determines the post format.

### Text

Use for concise updates, observations, or developer takeaways that do not require a visual.

### Single image

Use when one branded visual communicates the story clearly.

Example queue fields:

```json
{
  "format": "image",
  "image_url": "https://...",
  "image_alt": "Accessible description"
}
```

### PDF carousel / document

Use when a story benefits from explanation, architecture, comparisons, workflows, timelines, or multiple takeaways.

New document posts use the V3 HTML/CSS renderer:

```json
{
  "format": "document",
  "document": {
    "renderer": "v3",
    "carousel": {
      "theme": "shopify",
      "brand": {
        "name": "WAJAHAT NAQVI",
        "subtitle": "Shopify · Full-stack · AI"
      },
      "slides": []
    }
  }
}
```

Supported V3 layouts:

`cover`, `browser`, `code`, `network`, `architecture`, `cards`, `feature_grid`, `comparison`, `before_after`, `timeline`, `metrics`, `quote`, `screenshot`, `annotated_screenshot`, `workflow`, `ecommerce`, `model_comparison`, and `closing`.

Carousels normally contain 5–8 slides.

The renderer also normalizes escaped line breaks so literal `\n` sequences do not appear in published carousel titles.

## Repository structure

```text
.github/workflows/
  preview.yml       Preview the currently queued LinkedIn post
  publish.yml       Publish an approved LinkedIn post
  skip.yml          Skip the current queued story

src/
  prepare.py        Candidate validation, scoring, deduplication, queue creation
  preview.py        Preview preparation
  publish.py        LinkedIn publication flow
  skip.py           Skip/rejection flow
  linkedin.py       LinkedIn API client
  carousel/
    renderer.py     V3 HTML renderer
    render_pdf.py   PDF generation
    carousel.css    Carousel presentation styles

queue/
  latest.json       Current handoff item
  example-document.json
  openai-v3.json

data/
  history.json      Successfully published stories
  skipped.json      Rejected stories
  backlog.json      Short-lived secondary candidates

examples/
  carousels/        Example carousel payloads
  assets/           Example visual assets
```

## Queue contract

`queue/latest.json` is the handoff between content preparation and human approval.

Typical states:

- `ready` — prepared and waiting for review
- `published` — successfully published to LinkedIn
- `skipped` — intentionally rejected
- `idle` — no eligible story

A new story must never overwrite an existing `ready` item that still needs a human decision.

A typical prepared item includes:

```json
{
  "id": "unique-story-id",
  "status": "ready",
  "category": "Shopify Developer Platform",
  "priority_score": 90,
  "format": "document",
  "topic": "Story title",
  "caption": "LinkedIn caption",
  "source_url": "https://official-source.example/article",
  "sources": [
    "https://official-source.example/article"
  ],
  "document": {
    "renderer": "v3",
    "carousel": {}
  }
}
```

## Normal operating procedure

### 1. Prepare a story

Research authoritative primary sources, score candidates, exclude duplicate or skipped stories, and select at most one qualifying topic.

If a qualifying story is found:

```text
queue/latest.json → status=ready
```

If nothing is strong enough, do not create filler.

### 2. Preview

The **Preview prepared LinkedIn post** workflow runs automatically when `queue/latest.json` changes on `main`, and it can also be run manually.

For a document post it:

1. reads the ready queue item;
2. renders the carousel;
3. validates the generated document;
4. uploads the document preview artifact;
5. shows a GitHub Actions summary.

For text or image posts, the appropriate preview artifact is generated instead.

A skipped artifact step can be normal when it belongs to a different post format. For example, a document post uploads the document preview and skips the text/image artifact step.

### 3. Review

Before publishing, verify:

- topic and source accuracy;
- caption quality;
- title and slide wrapping;
- no visible escape sequences such as `\n`;
- no clipping or text overflow;
- mobile-safe spacing;
- correct brand and theme;
- correct source references.

### 4. Publish

Run the **Publish approved LinkedIn post** workflow manually from GitHub Actions and enter:

```text
PUBLISH
```

The workflow uses the official LinkedIn API.

On success it:

1. receives a LinkedIn post URN;
2. appends the story to `data/history.json`;
3. changes `queue/latest.json` to `status=published`;
4. stores `linkedin_post_id` and `published_at`;
5. commits the publication state back to the repository.

There is intentionally no scheduled LinkedIn publication.

### 5. Skip

If the story should not be published, run the **Skip current LinkedIn post** workflow and enter:

```text
SKIP
```

The story is recorded in `data/skipped.json` so it is not selected again.

## Important GitHub Actions behavior

A green GitHub Actions **Success** means the workflow completed successfully. It does not always mean a new LinkedIn post was created.

For example, if `queue/latest.json` already has:

```json
{
  "status": "published"
}
```

the publish script intentionally exits as a no-op.

Developers should inspect the workflow log for either:

```text
SUCCESS: urn:li:...
```

or:

```text
NOOP: queue status is 'published'.
```

before concluding that a new LinkedIn post was created.

## Mobile-safe carousel design

LinkedIn's mobile document viewer overlays controls on part of the PDF.

V3 keeps important readable content inside reusable safe areas:

- top: 170px
- bottom: 110px
- left/right: 80px

Decorative shapes can extend outside these areas, but essential text should stay inside them.

## Local setup

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

If PowerShell blocks virtual-environment activation:

```powershell
.venv\Scripts\python.exe
```

## LinkedIn credentials

Keep credentials in local environment variables or GitHub Secrets. Never commit them.

Required GitHub Secrets:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN`

Optional repository variable:

- `LINKEDIN_VERSION` — defaults to `202609`

The access token and author URN must belong to the intended LinkedIn publishing identity.

## Manual candidate preparation

Create `queue/candidates.json`, then run:

```powershell
.venv\Scripts\python.exe src\prepare.py --candidates queue\candidates.json
```

The preparation command:

1. validates scoring ranges and source requirements;
2. excludes published and skipped stories;
3. combines fresh candidates with valid backlog items;
4. selects at most one strongest story;
5. chooses text, image, or document format;
6. renders a local V3 preview for document posts;
7. writes `queue/latest.json` with `status=ready`;
8. stops without publishing.

## Render a carousel locally

Render the queued document:

```powershell
.venv\Scripts\python.exe src\publish.py --render-only
```

Render an example:

```powershell
.venv\Scripts\python.exe src\carousel\render_pdf.py examples\carousels\shopify.json --output generated\examples\shopify.pdf
```

## Developer workflow

For contributors working on the repository:

1. pull the latest `main`;
2. create a feature branch;
3. keep queue/history changes separate from renderer or publisher code when possible;
4. make the smallest targeted change;
5. run local validation;
6. render a sample document when changing carousel code;
7. inspect the generated PDF visually;
8. open a pull request;
9. do not expose LinkedIn credentials in commits, logs, screenshots, or test fixtures.

When changing publication logic, test the no-op and dry-run paths before using real LinkedIn credentials.

When changing carousel rendering, test both normal titles and titles containing escaped line breaks such as `\\n`.

## Validation

Run:

```powershell
.venv\Scripts\python.exe -m py_compile src\linkedin.py src\publish.py src\carousel\renderer.py src\carousel\render_pdf.py src\prepare.py src\skip.py
.venv\Scripts\python.exe src\publish.py
git diff --check
```

The default publisher run remains a dry run unless the explicit manual publishing controls are satisfied.

## Safety boundaries

This project intentionally separates preparation from publication.

It does **not** automate:

- LinkedIn browser interaction
- likes
- comments
- DMs
- connection requests
- reposts
- engagement automation

LinkedIn publication requires explicit human approval.

## Repository

`wajahatalinaqvi/linkedin-pro-agent`

## License

MIT
