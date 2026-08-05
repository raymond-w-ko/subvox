/**
 * Tiny debug logger → /tmp/rko-llm.log (only when CONFIG.debug is true).
 */
import { appendFileSync } from "node:fs";
import { CONFIG } from "./config.js";

let enabled = CONFIG.debug;

export function setDebug(v: boolean): void {
	enabled = v;
}

export function log(...args: unknown[]): void {
	if (!enabled) return;
	try {
		const line = `[${new Date().toISOString()}] ${args
			.map((a) => (typeof a === "string" ? a : safeJson(a)))
			.join(" ")}\n`;
		appendFileSync("/tmp/rko-llm.log", line);
	} catch {
		/* never break on logging */
	}
}

function safeJson(v: unknown): string {
	try {
		return JSON.stringify(v);
	} catch {
		return String(v);
	}
}
