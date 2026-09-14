---
name: gh-upload-media
description: Upload images or video to a GitHub issue or PR (before/after screenshots, proof media). Use when a PR or issue needs an embedded picture or video.
---

# Upload media to a GitHub issue or PR

## Preconditions

- Never use computer control or a browser for the upload.
- Upload only with GitHub-write authorization and approved content plus destination.
- Sanitize first: no secrets, personal or private data, internal-only identifiers, or other sensitive content. If a capture cannot be made safe, state the blocker and do not upload.

## Command

Keep the token out of process arguments:

```sh
{ printf 'Authorization: Bearer '; gh auth token; } | curl -sS "https://uploads.github.com/user-attachments/assets?name=<file>&content_type=<mime>&repository_id=$(gh api repos/<owner>/<repo> --jq .id)" -X POST -H @- -H "Accept: application/json" --data-binary @<file>
```

Use the response `.url`:

- Images: embed as `![alt](url)`.
- Video: put the URL on its own line so GitHub renders a player.

Same CDN as drag-and-drop. Uploads inherit repository visibility and are permanent.

## Failure modes

- Images and video only. `422` means bad content type. `404` means bad repository id or no push access.
- For other artifacts, or when the endpoint fails, use a prerelease asset or the repo-approved artifact store.

## Alternatives, and one to avoid

- `gh --attach` (repeatable, on `gh issue|pr create|edit|comment`) supersedes the curl once shipped. Unmerged as of gh 2.98.0 (`cli/cli#14186`): feature-detect, never assume.
- `gh attach` is an unrelated extension (`enthus-appdev/gh-attach`). It pushes repo blobs to `refs/uploads/` and returns 400 at roughly 60KB and above. Never use it for proof media.
