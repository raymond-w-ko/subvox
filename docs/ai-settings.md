# Local AI settings

`bin/apply_my_ai_settings.py` configures Codex, Claude Code, and Pi to use CLIProxyAPI,
in addition to its existing model, MCP server, and plugin settings.

Store the gateway URL and key in `~/.config/ai/proxy.json`, outside this repository:

```json
{
  "base_url": "https://gateway.example.test",
  "api_key": "YOUR_GATEWAY_KEY"
}
```

Replace the placeholder in a local editor. On Unix, use directory permissions
`700` and file permissions `600`. Do not commit this file.

Preview and apply from the repository root:

```sh
./bin/apply_my_ai_settings.py --dry-run
./bin/apply_my_ai_settings.py
```

The gateway step reads `base_url` and `api_key` and applies:

- `~/.codex/config.toml`: selects `cliproxyapi` and replaces its provider table
  with the Responses API endpoint, `experimental_bearer_token` containing the
  local key, and `requires_openai_auth = false`. It removes the old `env_key`
  reference, so no shell export is needed. Codex's config must already exist.
- `~/.claude/settings.json`: merges `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`,
  and an empty `ANTHROPIC_API_KEY` into `env`, preserving other settings and
  environment variables. The file is created if missing. Writes use permissions
  `600` on Unix because this file contains the plaintext key. Codex config writes
  also use `600` on Unix.
- `~/.pi/agent/models.json`: replaces the `openai` and `anthropic` provider
  overrides with the gateway URL and key, preserving other providers. Builtin
  model lists and capabilities remain available. OpenAI uses `/v1`; Anthropic
  uses the root URL with bearer authentication and an empty `x-api-key` header.
  Pi key syntax is escaped so keys are treated literally, not as commands or
  environment references. The file is created if missing and uses permissions
  `600` on Unix. It is ignored by Git because Home Manager links `~/.pi` into
  this repository.
- `~/.pi/agent/auth.json`: removes the entire file after both Pi provider
  overrides succeed and the conflicting plugin is confirmed absent, because
  saved credentials take precedence over proxy keys.
  This removes saved credentials for **all Pi providers**, not just OpenAI and
  Anthropic. Dry runs only report the removal; failed Pi overrides leave the
  auth file intact. Plugin command failures also preserve the auth file. The
  script never reads or displays its contents.

The script runs `pi.sh list` and, when `npm:pi-anthropic-oauth` is installed,
runs `pi.sh uninstall npm:pi-anthropic-oauth` and verifies removal with another
`pi.sh list`. Its provider override conflicts with the proxy configuration.
Dry runs only list packages and report the planned uninstall. `pi.sh` must be
on PATH; package command output is not echoed because it can contain local data.

Use builtin `openai` for GPT models and builtin `anthropic` for Claude models.
Pi default model selections are not changed. Restart Pi after applying.

Missing, malformed, empty, or placeholder keys fail the gateway step without
changing gateway configurations or removing Pi credentials. Invalid URLs also
fail before gateway edits. Other settings still run. All edits to Codex config,
Claude settings, and Pi models
hide old values and file diffs, including during dry runs, so unrelated changes
cannot expose credentials in diff context. After key rotation or a URL change,
run the script again and restart the clients. The old `secrets.json` file is no
longer read; existing copies are left untouched.

Use the gateway root URL. A trailing slash or `/v1` is accepted: the script adds
`/v1` for Codex and uses the root for Claude. HTTP and HTTPS are supported;
URLs with embedded credentials, query strings, or fragments are rejected.

Codex documents `experimental_bearer_token` as a
[direct bearer token](https://developers.openai.com/codex/config-reference/).
This setup uses it intentionally to keep key loading independent of the shell.
All three client configuration files contain a plaintext copy of the key.
