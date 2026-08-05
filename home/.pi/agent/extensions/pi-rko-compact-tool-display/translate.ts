/**
 * Cheap background shell-command → human-readable label translator.
 *
 * Uses Pi's own completion stack (see llm.ts) — reuses the configured provider,
 * stored credentials/API keys, base URL, headers, and provider hooks.
 *
 * Caching: labels are deterministic (temperature 0, pinned model), so results
 * are persisted to disk keyed by `model|thinking|command` and reused across
 * reloads/sessions. In-memory in-flight dedupe avoids concurrent duplicate
 * requests. Changing the model or thinking level produces new keys (no stale
 * labels reused).
 *
 * Env:
 *   RKO_BASH_TRANSLATOR   "1" (default) enable, "0" disable
 */

import { oneShot } from "./llm.js";
import { cacheGet, cacheSet } from "./cache.js";

const MAX_LABEL = 48;
const TIMEOUT_MS = 4000;

function cacheKey(command: string): string {
	const model = process.env.RKO_TRANSLATE_MODEL || "openrouter/google/gemini-3.5-flash-lite";
	const thinking = process.env.RKO_TRANSLATE_THINKING || "off";
	return `${model}|${thinking}|${command}`;
}

// --- in-flight dedupe (within process) --------------------------------------
const inflight = new Map<string, Promise<string | null>>();

export function translateCommand(command: string): Promise<string | null> {
	const trimmed = (command || "").trim();
	if (process.env.RKO_BASH_TRANSLATOR === "0" || trimmed.length < 4) {
		return Promise.resolve(null);
	}

	const key = cacheKey(trimmed);

	// 1. Persistent cache hit ("" stored = known-failed, don't retry).
	const cached = cacheGet(key);
	if (cached !== undefined) return Promise.resolve(cached || null);

	// 2. In-flight dedupe.
	const existing = inflight.get(key);
	if (existing) return existing;

	const p = doTranslate(trimmed).then((label) => {
		cacheSet(key, label ?? "");
		return label;
	});
	inflight.set(key, p);
	return p;
}

async function doTranslate(command: string): Promise<string | null> {
	const prompt = `Rewrite this shell command as one short plain-English label describing WHAT IT DOES. Max ${MAX_LABEL} chars. Imperative phrase, no code markers, no quotes, no trailing punctuation. Respond with ONLY the label, no explanation.\n\nCommand: ${command}`;

	// Race against a hard timeout so a slow/hung provider never stalls the TUI.
	const result = await Promise.race([
		oneShot(prompt, { maxTokens: 40 }),
		new Promise<string>((resolve) => setTimeout(() => resolve(""), TIMEOUT_MS)),
	]);

	let label = (result || "")
		.replace(/^["'`]+/, "")
		.replace(/["'`]+$/, "")
		.split("\n")[0]
		.trim();
	if (!label) return null;
	if (label.length > MAX_LABEL) {
		label = `${label.slice(0, MAX_LABEL - 1)}…`;
	}
	return label;
}
