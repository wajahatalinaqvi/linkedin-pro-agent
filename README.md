# LinkedIn Pro Agent

A priority-driven LinkedIn content agent that researches strong technology stories, prepares professional LinkedIn posts, generates previews, and keeps final publication under explicit human control.

Built and maintained by **[Wajahat Naqvi](https://github.com/wajahatalinaqvi)** — a Shopify-focused full-stack developer working across React, Laravel, ecommerce automation, and practical AI workflows.

[Portfolio](https://wajahatalinaqvi.github.io/) · [GitHub Profile](https://github.com/wajahatalinaqvi) · [LinkedIn](https://www.linkedin.com/in/wajahatnaqvi-developer/)

## Free automatic preparation (Gemini API free tier)

The **Request priority LinkedIn topic** action now attempts to prepare a saved LinkedIn draft automatically with Google's free-tier Gemini API (subject to model availability and quotas). No paid OpenAI API key is required.

**One-time setup:** Create an API key at https://aistudio.google.com/apikey in a **free-tier project without paid billing**. Save it under GitHub → Settings → Secrets and variables → Actions → New repository secret as `GEMINI_API_KEY`. Never paste your key into a topic field, a commit, or a public issue.

Then run **Actions → Request priority LinkedIn topic** with a **verified official source URL** and the topic/angle. The workflow:
1. saves your request under `queue/topic_requests/`;
2. reads the supplied official webpage with URL context;
3. prepares a LinkedIn caption and six-slide V3 carousel;
4. renders the PDF and saves `queue/drafts/<request-id>.json`;
5. uploads a `linkedin-post-preview` artifact and selects the new draft as latest only if another `ready` post isn't already selected.

No LinkedIn publication is attempted. **You must inspect the sources, caption and all six slides before manually publishing.** A generated draft is not a guarantee that every claim is correct.

If the source is missing, the domain is not in `config/official_sources.json`, the Gemini key/quota is unavailable, or webpage retrieval fails, the workflow records a request status such as `needs_source`, `needs_configuration` or `needs_review` instead of inventing content. Free-tier availability and quotas can change. Do not enable billing if you want to ensure there are no API charges.

For a topic you already requested, run **Actions → Prepare existing topic request (free tier)** and enter the request's filename (including `.json`). A request filename is **not** a draft ID until preparation succeeds. Refer to the resulting `draft_id` inside the updated request JSON.

---

## Flexible manual workflow (new)

**There is no daily publishing limit or posting schedule.** Prepare, preview, skip, or publish whenever you choose. Keep more than one draft without overwriting an existing ready post.

### 1. Request your own topic (highest editorial priority)

Open **Actions → Request priority LinkedIn topic → Run workflow**. Enter a topic, optional primary-source URL, and the angle you want. For example: "OpenAI DOTS: developer implications."

This saves a request under `queue/topic_requests/`. It **does not** invent facts, produce a researched post, or publish by itself. A researcher/developer must verify official sources and prepare a complete draft. Explicit user requests take priority for editorial consideration; fact-checking still applies.

### 2. Import a prepared draft

When a complete source-verified JSON post is ready, save it as `queue/drafts/<post-id>.json` on `main` or run the following locally:

```powershell
.venv\Scripts\python.exe src\drafts.py import path\to\post.json
.venv\Scripts\python.exe src\drafts.py list
```

Each saved draft has its own stable `id`. It must have `status: "ready"`, `caption`, `source_url`, and a supported format. Editing `queue/drafts/<post-id>.json` lets you revise the caption/slides and preview the updated draft. The research preparation script also archives new selected candidates into this directory, protecting an existing ready post.

To select a saved draft as the legacy current queue item, run **Actions → Select LinkedIn draft** and enter its `post_id`. This preserves any displaced ready draft. Alternatively run:

```powershell
.venv\Scripts\python.exe src\drafts.py select <post-id>
```

### 3. Preview any post whenever you want

Open **Actions → Preview prepared LinkedIn post → Run workflow**. Enter `post_id` to preview any saved draft, including an already-published or skipped item. Leave it blank to preview `queue/latest.json`.

The workflow generates `linkedin-post-preview` (for document posts, a rendered PDF plus summary; for text/image, a summary). Published posts are **previewable without becoming publishable again**.

### 4. Publish only the post you select

Open **Actions → Publish approved LinkedIn post → Run workflow**. Enter the saved `post_id`, then type **exactly** `PUBLISH`. Leave `post_id` blank to use `queue/latest.json`. The publish action refuses previously published/skipped posts, checks `data/history.json` for duplicates, and updates the selected draft and matching latest queue state after successful API publication.

You may publish more than one **different, reviewed** post per day. There is no automated engagement or auto-publishing. Keep your GitHub Actions credentials private.

### 5. Skip selected drafts

Run **Actions → Skip current LinkedIn post**, optionally enter `post_id`, and confirm `SKIP`. It records the decision without affecting other drafts.

**Safety:** never edit a published post's status back to `ready` to force a repost. Use a genuinely new, independently verified story and unique ID. Actions run sequentially to avoid overlapping publish/skip/select operations.

---

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

The **Preview prepared LinkedIn post** workflow runs automatically when `queue/latest.json` changes on `main`, and it can also be run manually with an optional saved `post_id`.

For a document post it:

1. reads the selected saved post (including previously published items);
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
