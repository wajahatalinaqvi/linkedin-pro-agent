# LinkedIn Pro Agent — GitHub Actions quick guide

These workflows prepare and publish content for the repository owner. They are
**not a multi-user SaaS dashboard**. GitHub Actions' own sidebar cannot be
fully customized, but the workflows are grouped by their ordered names.

## Everyday workflow

1. **01 | Daily research (draft only)** runs on a GitHub UTC cron daily.
   It collects source-verified news, chooses one strong story when available,
   saves a ready draft and uploads a PDF preview. GitHub scheduled start times
   can be delayed. The job never publishes automatically.
2. **02 | Request priority topic** is optional. Submit a verified official
   source URL and your topic. The requested draft takes priority over the
   automatic one. The automatic draft stays saved.
3. **03 | Preview a saved draft** manually renders the currently selected
   ready draft, or a specified saved draft. This is useful after editing one.
   Automatic research and requested-topic jobs already upload PDFs, so
   preview is not automatically triggered by every queue update.
4. **04 | Publish approved post** requires an explicit \`PUBLISH\` confirmation.
   Post ID may be blank to use the current selected ready draft. Look for
   the publication status and LinkedIn ID in the run summary/logs.

## Advanced utilities

- **81 | Retry existing topic** for a request that needs a corrected source.
- **82 | Select saved draft** when you want a different saved ready draft.
- **83 | Skip saved draft** (requires \`SKIP\`) if you reject an unsuitable post.
- **90 | Agent tests** runs automatically when code/workflows change.
- SaaS foundation tests are kept in the \`saas-development\` branch.

## Who can run this?

Only members with **write access** to the repository can run a manual
\`workflow_dispatch\` job in this repository. Forks don't inherit the private
LinkedIn and Gemini Actions secrets.

**Warning for public repositories:** Source code, saved drafts, publishing
history, workflow logs, and available artifacts may be visible publicly.
A public repository is not private content storage. Consider changing the
repository visibility to private (Settings > General > Danger Zone > Change
repository visibility), and review access for any collaborators.

Make sure \`Settings > Actions > General\` uses conservative permissions and
fork-PR approvals. **Never approve untrusted workflow changes**, and don't
give write access to people who shouldn't be able to publish.

New workflow names and triggers improve *future* runs only. Previously
recorded runs remain visible until their retention period expires.
