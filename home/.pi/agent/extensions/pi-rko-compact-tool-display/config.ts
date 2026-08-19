/**
 * Personal settings — top-level constants, no env vars. Edit here.
 */
export const CONFIG = {
	/** File-tool owner. Use "hashline" when pi-hashline-edit-pro is loaded. */
	fileTools: "builtin" as "builtin" | "hashline",
	/** Master switch for bash-command translation. */
	enabled: true,
	/** Model used for the background one-shot translation. */
	model: "openrouter/google/gemini-3.5-flash-lite",
	/** Thinking level for the translation call (gemini-3.5-flash-lite requires reasoning). */
	thinking: "low",
	/** Write diagnostics to /tmp/rko-llm.log. */
	debug: false,
};

export const MODEL_PROVIDER = CONFIG.model.split("/")[0];
export const MODEL_ID = CONFIG.model.slice(CONFIG.model.indexOf("/") + 1);
