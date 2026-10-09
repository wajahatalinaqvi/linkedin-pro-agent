# Saved LinkedIn posts

Each JSON file in this directory is an independently addressable post.

- Copy the filename **without** `.json` to use as the **post_id** in GitHub Actions.
- **Preview prepared LinkedIn post** accepts any saved post ID, including already-published posts.
- **Publish approved LinkedIn post** requires exact `PUBLISH` and only publishes a new `ready` post that is not in publication history.
- **Select LinkedIn draft** lets you make a saved post the currently selected `queue/latest.json` item.
- New researched posts can be added by the preparation pipeline or imported with `python src/drafts.py import path/to/post.json`.

The archived Claude Sonnet 5.5 JSON here is marked **published**, preserving its actual publication ID. It is a real example, **not a new ready post**, and must not be republished.

To request a new topic, use **Actions → Request priority LinkedIn topic**. Topic requests are stored separately under `queue/topic_requests/` and require source verification and post preparation before a draft appears here.
