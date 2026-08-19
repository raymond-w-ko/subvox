import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import compactToolDisplay from "./index.js";
import { CONFIG } from "./config.js";

export default function (pi: ExtensionAPI): void {
  CONFIG.fileTools = "hashline";
  compactToolDisplay(pi);
}
