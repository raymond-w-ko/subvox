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
 * Settings are top-level constants in config.ts (no env vars).
 */

import { oneShot } from "./llm.js";
import { cacheGet, cacheSet } from "./cache.js";
import { CONFIG } from "./config.js";
import { log } from "./debug-log.js";

const MAX_LABEL = 79;
const TIMEOUT_MS = 8000;

// Bump when the completion request or key scheme changes so stale cached
// labels (including poisoned "" failures and partial-command entries from
// the pre-debounce era) are ignored and re-translated.
const CACHE_VERSION = "2";

function cacheKey(command: string): string {
	const thinking = CONFIG.thinking === "off" ? "low" : CONFIG.thinking;
	return `${CACHE_VERSION}|${CONFIG.model}|${thinking}|${command}`;
}

// --- in-flight dedupe (within process) --------------------------------------
const inflight = new Map<string, Promise<string | null>>();

export function translateCommand(command: string): Promise<string | null> {
	const trimmed = (command || "").trim();
	log("translateCommand: ENTRY len=", trimmed.length, "cmd=", JSON.stringify(trimmed.slice(0, 50)), "at=", Date.now());
	if (!CONFIG.enabled || trimmed.length < 4) {
		log("translateCommand: early return (disabled=", !CONFIG.enabled, "len=", trimmed.length, ")");
		return Promise.resolve(null);
	}

	const key = cacheKey(trimmed);

	// 1. Persistent cache hit ("" stored = known-failed, don't retry).
	const cached = cacheGet(key);
	if (cached !== undefined) {
		log("translateCommand: CACHE HIT key=", key, "->", JSON.stringify(cached));
		return Promise.resolve(cached || null);
	}
	log("translateCommand: CACHE MISS key=", key);

	// 2. In-flight dedupe.
	const existing = inflight.get(key);
	if (existing) return existing;

	const p = doTranslate(trimmed).then((label) => {
		log("translateCommand: store label=", JSON.stringify(label), "for", JSON.stringify(command.slice(0, 60)));
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
