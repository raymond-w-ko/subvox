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
const MAX_ATTEMPTS = 3;
const RETRY_DELAYS_MS = [400, 1200];

// Bump when the completion request or key scheme changes so stale cached
// labels (including leftover "" failures from older builds) are ignored
// and re-translated.
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

	// 1. Persistent cache hit. Empty/whitespace labels are treated as misses
	// so a failed translation can be retried on the next call.
	const cached = cacheGet(key);
	if (cached) {
		log("translateCommand: CACHE HIT key=", key, "->", JSON.stringify(cached));
		return Promise.resolve(cached);
	}
	log("translateCommand: CACHE MISS key=", key);

	// 2. In-flight dedupe. The promise is removed after settle so a later
	// call can retry a failed (uncached) translation.
	const existing = inflight.get(key);
	if (existing) return existing;

	const p = doTranslate(trimmed)
		.then((label) => {
			log(
				"translateCommand: store label=",
				JSON.stringify(label),
				"for",
				JSON.stringify(command.slice(0, 60)),
			);
			if (label) cacheSet(key, label);
			return label;
		})
		.finally(() => {
			inflight.delete(key);
		});
	inflight.set(key, p);
	return p;
}

function sleep(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

async function translateOnce(command: string): Promise<string | null> {
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

async function doTranslate(command: string): Promise<string | null> {
	for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
		const label = await translateOnce(command);
		if (label) {
			if (attempt > 1) log("doTranslate: succeeded on attempt", attempt);
			return label;
		}
		log("doTranslate: empty result attempt=", attempt, "of", MAX_ATTEMPTS);
		if (attempt < MAX_ATTEMPTS) {
			await sleep(RETRY_DELAYS_MS[attempt - 1] ?? RETRY_DELAYS_MS[RETRY_DELAYS_MS.length - 1]);
		}
	}
	return null;
}
