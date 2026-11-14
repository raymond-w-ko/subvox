/**
 * Personal settings — top-level constants, no env vars. Edit here.
 */
export const CONFIG = {
	/** File-tool owner. Use "hashline" when pi-hashline-edit-pro is loaded. */
	fileTools: "builtin" as "builtin" | "hashline",
	/** Master switch for bash-command translation. */
	enabled: true,
	/** Claude Haiku 5.5 via OpenRouter for the background one-shot translation. */
	model: "openrouter/anthropic/claude-haiku-5.5",
	/** Thinking level for the translation call. Use "off" to disable reasoning. */
	thinking: "low",
	/** Write diagnostics to /tmp/rko-llm.log. */
	debug: false,
};

export const MODEL_PROVIDER = CONFIG.model.split("/")[0];
export const MODEL_ID = CONFIG.model.slice(CONFIG.model.indexOf("/") + 1);
