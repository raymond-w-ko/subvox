/**
 * Thin bridge to Pi's own LLM stack — no raw HTTP, no inventing our own auth.
 *
 * Captures the session's bound Model (and ModelRegistry) from extension event
 * contexts, then performs one-shot completions via `model.api.streamSimple(...)`.
 * This reuses Pi's configured providers, stored credentials/API keys, base URLs,
 * headers, and provider hooks automatically.
 *
 * Model selection:
 *   - Default: the session's active model (`ctx.getModel()`).
 *   - Optional override: `RKO_TRANSLATE_MODEL=provider/id` to pin a specific
 *     (cheap/fast) model from the same provider's catalog via ModelRegistry.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import type { Api, Model } from "@earendil-works/pi-ai";

let activeModel: Model<Api> | undefined;
let registry: { find?: (provider: string, id: string) => Model<Api> | undefined } | undefined;

const PINNED_PROVIDER = "openrouter";
const PINNED_MODEL = "google/gemini-3.5-flash-lite";

/** Register event handlers that capture the current bound model + registry. */
export function captureModelApi(pi: ExtensionAPI): void {
	const grab = (ctx: any) => {
		activeModel = ctx?.getModel?.() ?? activeModel;
		registry = ctx?.modelRegistry ?? registry;
	};

	pi.on("session_start" as any, (_event: any, ctx: any) => grab(ctx));
	pi.on("before_agent_start" as any, (_event: any, ctx: any) => grab(ctx));
	pi.on("model_select" as any, (event: any) => {
		if (event?.model) activeModel = event.model;
	});
}

function resolveModel(): Model<Api> | undefined {
	// Optional override wins; otherwise hardcoded cheap/fast model.
	const pinned = process.env.RKO_TRANSLATE_MODEL;
	const provider = pinned && pinned.includes("/") ? pinned.split("/")[0] : PINNED_PROVIDER;
	const id =
		pinned && pinned.includes("/")
			? pinned.slice(pinned.indexOf("/") + 1)
			: PINNED_MODEL;
	if (registry?.find) {
		const m = registry.find(provider, id);
		if (m && (m as any).api) return m;
	}
	return activeModel;
}

/**
 * One-shot completion reusing Pi's provider/auth stack.
 * Returns the generated text ("" on any failure).
 */
export async function oneShot(prompt: string, options?: { maxTokens?: number }): Promise<string> {
	const model = resolveModel();
	if (!model || !(model as any).api) return "";

	try {
		const stream = (model as any).api.streamSimple(
			model,
			{
				messages: [{ role: "user", content: prompt }],
			},
			{
				maxTokens: options?.maxTokens ?? 40,
				temperature: 0,
				reasoning: (process.env.RKO_TRANSLATE_THINKING as any) || "off",
			},
		);
		const message = await stream.result();
		const text = (message?.content ?? [])
			.filter((c: any) => c.type === "text" && typeof c.text === "string")
			.map((c: any) => c.text)
			.join("")
			.trim();
		return text;
	} catch {
		return "";
	}
}
