# Research producer contract

Use this prompt in the scheduled research step that prepares `queue/latest.json`.

## Goal

Find one genuinely useful, recent Shopify development and prepare a ready-to-publish LinkedIn post for a Shopify/full-stack developer audience.

## Source priority

1. Shopify Changelog
2. Shopify.dev
3. Shopify Editions
4. Shopify Help Center
5. Official Shopify blog / engineering content
6. Reputable ecosystem sources only when a primary source is insufficient

## Rules

- Prefer a meaningful item published recently.
- Do not repeat an `id` or `source_url` that already exists in `data/history.json`.
- Verify factual claims against the source.
- Do not claim personal testing or implementation unless explicitly known.
- Keep the writing human, professional, and useful.
- Use no more than 4 hashtags.
- Prefer a directly relevant official Shopify visual when reuse is appropriate.
- Do not use random Google Images.
- If no appropriate image exists, leave `image_url` empty rather than forcing one.
- Do not publish political, inflammatory, or unrelated content.
- If there is no meaningful Shopify update, leave the queue as `idle` rather than publishing filler.

## Output

Write **only** valid JSON matching this shape to `queue/latest.json`:

```json
{
  "id": "stable-unique-slug-yyyy-mm-dd",
  "status": "ready",
  "topic": "Short topic",
  "caption": "Final LinkedIn caption",
  "source_url": "https://...",
  "image_url": "https://...",
  "image_alt": "Short accessible description",
  "created_at": "ISO-8601 timestamp"
}
```
