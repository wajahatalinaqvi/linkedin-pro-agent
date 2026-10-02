# Shopify → LinkedIn Agent

A lightweight, reusable agent that separates **Shopify research/content generation** from **LinkedIn publishing**.

```text
Research producer → queue/latest.json → Python publisher → LinkedIn
```

The publisher itself uses no AI model, so the publishing step consumes no AI tokens.

## Features

- Text-only or single-image LinkedIn posts
- LinkedIn official Posts + Images APIs
- Duplicate protection by post ID and source URL
- Safe dry-run mode by default
- Publication history
- Windows PowerShell runner
- GitHub Actions scheduling
- No secrets committed to Git

## LinkedIn requirements

Create a LinkedIn Developer application and obtain:

- an OAuth access token with `w_member_social`
- your member author URN, for example `urn:li:person:abc123`

LinkedIn tokens expire, so keep the token in environment variables or GitHub Secrets, never in the repository.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill `.env`:

```env
LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_AUTHOR_URN=urn:li:person:...
LINKEDIN_VERSION=202607
AUTO_PUBLISH=false
```

## Queue format

A research agent writes one ready post into `queue/latest.json`:

```json
{
  "id": "shopify-example-2026-10-02",
  "status": "ready",
  "topic": "Shopify example",
  "caption": "Final LinkedIn caption here",
  "source_url": "https://changelog.shopify.com/...",
  "image_url": "https://cdn.shopify.com/...",
  "image_alt": "Short description of the image",
  "created_at": "2026-10-02T11:00:00+05:00"
}
```

Leave `image_url` empty for a text-only post.

## Dry run

```powershell
python src\publish.py
```

With `AUTO_PUBLISH=false`, the script validates the queue and duplicate history but does not publish.

## One-time real test

```powershell
python src\publish.py --force
```

`--force` bypasses only the AUTO_PUBLISH safety switch. It does **not** bypass queue validation or duplicate checks.

## Full automation

After the first successful test, set:

```env
AUTO_PUBLISH=true
```

For local Windows use, schedule `scripts/run-publisher.ps1`.

For GitHub-hosted automation, the included workflow runs Monday–Friday at **11:15 PKT**.

Add GitHub Actions secrets:

- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_AUTHOR_URN`

Optional repository variable:

- `LINKEDIN_VERSION` (defaults to `202607`)

## Research producer

`AGENT_PROMPT.md` defines the strict output contract for the research side. It should research one useful fresh Shopify development and update only `queue/latest.json`.

This design means Codex/OpenAI does **not** need to run during publishing.

## Security

Never commit:

- `.env`
- LinkedIn access tokens
- LinkedIn client secrets
- OAuth authorization codes

Use local environment variables or GitHub Actions Secrets.

## Notes

- LinkedIn requires a supported date-version header for its REST APIs. Update `LINKEDIN_VERSION` when LinkedIn retires an older version.
- The access token may periodically require reauthorization.
- Prefer official Shopify visuals only when appropriate to reuse; otherwise use an original visual or a text-only post.

## License

MIT.
