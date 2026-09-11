# Local AI settings

`bin/apply_my_ai_settings.py` configures Codex and Claude Code to use CLIProxyAPI,
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

Missing, malformed, empty, or placeholder keys fail the gateway step without
changing either gateway configuration. Invalid URLs also fail before gateway
edits. Other settings still run. All edits to Codex config and Claude settings
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
Both client configuration files contain a plaintext copy of the key.
