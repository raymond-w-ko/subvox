#!/usr/bin/env node
// CLI: node index.js <path-to.kbd> [--svg-only]
// Generates a single combined all-layers PNG + legend

import { readFileSync, mkdirSync, writeFileSync } from 'fs';
import { basename, dirname, join } from 'path';
import sharp from 'sharp';
import { parseKbd } from './parse.js';
import { buildLayout, getKeyboardBounds } from './layout.js';
import { renderAllLayersSvg, renderLegendSvg } from './render.js';

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node index.js <path-to.kbd> [--svg-only]');
  process.exit(1);
}

const kbdPath = args[0];
const svgOnly = args.includes('--svg-only');

const src = readFileSync(kbdPath, 'utf-8');
const parsed = parseKbd(src);
const { defsrc, layers, aliases } = parsed;

const layout = buildLayout(defsrc);
const bounds = getKeyboardBounds(layout);

// Output directory
const kbdName = basename(kbdPath, '.kbd');
const outDir = join(dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1')), 'out', kbdName);
mkdirSync(outDir, { recursive: true });

console.log(`Parsing ${kbdPath}: ${defsrc.length} keys, ${layers.length} layers`);
console.log(`Output: ${outDir}`);

async function main() {
  // Combined all-layers image
  const combinedSvg = renderAllLayersSvg(defsrc, layers, aliases, layout, bounds);
  writeFileSync(join(outDir, 'all-layers.svg'), combinedSvg);

  if (!svgOnly) {
    await sharp(Buffer.from(combinedSvg))
      .png()
      .toFile(join(outDir, 'all-layers.png'));
    console.log('  ✓ all-layers.png');
  } else {
    console.log('  ✓ all-layers.svg');
  }

  // Legend
  const legendSvg = renderLegendSvg();
  writeFileSync(join(outDir, 'legend.svg'), legendSvg);
  if (!svgOnly) {
    await sharp(Buffer.from(legendSvg)).png().toFile(join(outDir, 'legend.png'));
    console.log('  ✓ legend.png');
  }

  console.log('Done!');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
