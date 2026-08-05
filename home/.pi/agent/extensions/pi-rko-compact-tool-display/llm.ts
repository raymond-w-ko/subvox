/**
 * Thin bridge to Pi's own LLM stack — no raw HTTP, no inventing our own auth.
 *
 * Captures the session's ModelRegistry (from extension event contexts), resolves
 * a model, and runs a one-shot completion via `modelRegistry.complete(model,
 * context, options)`. This is the SAME request path pi's agent uses, so it
 * reuses stored credentials/API keys, base URLs, headers, and provider hooks.
 *
 * Model selection:
 *   - CONFIG.model (see config.ts) — defaults to openrouter/google/gemini-3.5-flash-lite,
 *     resolved via ModelRegistry.find, with a fallback to any configured model.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import type { Api, Model } from "@earendil-works/pi-ai";
import { CONFIG, MODEL_ID, MODEL_PROVIDER } from "./config.js";
import { log } from "./debug-log.js";

// Structural view of the ModelRegistry pieces we use.
interface RegistryLike {
	find?: (provider: string, id: string) => Model<Api> | undefined;
	getAll?: () => Model<Api>[];
	getAvailable?: () => Model<Api>[];
	complete?: (
		model: Model<Api>,
		context: { messages: Array<{ role: string; content: string; timestamp?: number }> },
		options?: Record<string, unknown>,
	) => Promise<
		| {
				content?: Array<{ type?: string; text?: string }>;
				stopReason?: string;
				errorMessage?: string;
		  }
		| undefined
	>;
}

let activeModel: Model<Api> | undefined;
let registry: RegistryLike | undefined;

/** Register event handlers that capture the current ModelRegistry + model. */
export function captureModelApi(pi: ExtensionAPI): void {
	log("captureModelApi: registering handlers");
	const grab = (ctx: any) => {
		const m = ctx?.getModel?.();
		const r = ctx?.modelRegistry;
		log("grab: event ctx ok=", !!ctx, "| getModel type=", typeof ctx?.getModel, "| model=", m?.id, "| registry?=", !!r, "| registry.complete?=", typeof r?.complete, "| registry.find?=", typeof r?.find);
		if (m) activeModel = m;
		if (r) registry = r;
	};

	pi.on("session_start" as any, (_event: any, ctx: any) => {
		log("EVENT session_start");
		grab(ctx);
	});
	pi.on("before_agent_start" as any, (_event: any, ctx: any) => {
		log("EVENT before_agent_start");
		grab(ctx);
	});
	pi.on("model_select" as any, (event: any) => {
		log("EVENT model_select model=", event?.model?.id);
		if (event?.model) activeModel = event.model;
	});
}

function resolveModel(): Model<Api> | undefined {
	const provider = MODEL_PROVIDER;
	const id = MODEL_ID;

	let model: Model<Api> | undefined;
	if (registry?.find) {
		model = registry.find(provider, id);
		log("resolveModel: find(", provider, ",", id, ") ->", model?.id ?? "NOT FOUND");
	} else {
		log("resolveModel: registry.find missing (registry?=", !!registry, ")");
	}
	if (model) return model;

	// Fallback: any configured model (getModel is unavailable on this ctx).
	const all = registry?.getAll?.() ?? [];
	const fallback = all[0];
	log("resolveModel: fallback ->", fallback?.id ?? "none", "(available=", all.length, ")");
	return fallback ?? activeModel;
}

/**
 * One-shot completion reusing Pi's provider/auth stack.
 * Returns the generated text ("" on any failure or before auth is captured).
 */
export async function oneShot(prompt: string, options?: { maxTokens?: number }): Promise<string> {
	log("oneShot: start");
	const model = resolveModel();
	if (!model) {
		log("oneShot: NO MODEL, returning ''");
		return "";
	}
	if (!registry?.complete) {
		log("oneShot: registry.complete MISSING, returning '' (typeof=", typeof registry?.complete, ")");
		return "";
	}
	// gemini-3.5-flash-lite (openrouter) requires reasoning, so "off" is invalid.
	const reasoning: any = CONFIG.thinking === "off" ? "low" : CONFIG.thinking;
	log("oneShot: calling registry.complete maxTokens=", options?.maxTokens ?? 40, "THINKING=", reasoning);

	try {
		const t0 = Date.now();
		const message = await registry.complete(
			model,
			{ messages: [{ role: "user", content: prompt, timestamp: Date.now() }] },
			{
				maxTokens: options?.maxTokens ?? 40,
				temperature: 0,
				reasoning,
				// `complete` goes through provider.stream(), which reads reasoningEffort
				// (only streamSimple maps `reasoning` → `reasoningEffort`).
				reasoningEffort: reasoning,
			},
		);
		const ms = Date.now() - t0;
		const content = message?.content ?? [];
		log("oneShot: complete resolved in", ms, "ms | stopReason=", message?.stopReason, "| errorMessage=", message?.errorMessage, "| contentLen=", content.length, "| contentTypes=", JSON.stringify(content.map((c: any) => c?.type)));
		const text = (message?.content ?? [])
			.filter((c: any) => c?.type === "text" && typeof c.text === "string")
			.map((c: any) => c.text)
			.join("")
			.trim();
		log("oneShot: text='", text, "'");
		return text;
	} catch (error) {
		const msg = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
		log("oneShot: THREW ->", msg, error instanceof Error && error.stack ? `\n${error.stack}` : "");
		return "";
	}
}
