#!/usr/bin/env node
// CLI: node index.js <path-to.kbd> [--svg-only]
// Generates a combined sheet, individual layers, and a legend in SVG and PNG.

import { readFileSync, mkdirSync, writeFileSync } from 'fs';
import { basename, dirname, join } from 'path';
import { fileURLToPath } from 'url';
import sharp from 'sharp';
import { parseKbd } from './parse.js';
import { buildLayout, getKeyboardBounds } from './layout.js';
import { renderAllLayersSvg, renderLayerSvg, renderLegendSvg } from './render.js';

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
const platform = kbdName.startsWith('macos') ? 'macos' : 'windows';
const name = kbdName === 'windows' ? 'Windows'
  : kbdName === 'macos' ? 'macOS' : kbdName;
const renderOptions = { platform, name, layers };
const moduleDir = dirname(fileURLToPath(import.meta.url));
const outDir = join(moduleDir, 'out', kbdName);
mkdirSync(outDir, { recursive: true });

console.log(`Parsing ${kbdPath}: ${defsrc.length} keys, ${layers.length} layers`);
console.log(`Output: ${outDir}`);

async function main() {
  async function writeImage(filename, svg) {
    writeFileSync(join(outDir, filename + '.svg'), svg);
    if (!svgOnly) {
      await sharp(Buffer.from(svg)).png().toFile(join(outDir, filename + '.png'));
    }
    console.log(`  ✓ ${filename}${svgOnly ? '.svg' : '.svg + .png'}`);
  }

  await writeImage('all-layers', renderAllLayersSvg(defsrc, layers, aliases, layout, bounds, renderOptions));
  await writeImage('legend', renderLegendSvg());
  const layerDir = join(outDir, 'layers');
  mkdirSync(layerDir, { recursive: true });
  for (let i = 0; i < layers.length; i++) {
    const layer = layers[i];
    const svg = renderLayerSvg(layer.name, defsrc, layer.keys, aliases, layout, bounds,
      { ...renderOptions, index: i });
    const filename = `${String(i + 1).padStart(2, '0')}-${layer.name.replace(/[^a-z0-9_-]/gi, '-')}`;
    await writeImage(join('layers', filename), svg);
    // Keep the existing Windows base-preview link current on every generation.
    if (!svgOnly && kbdName === 'windows' && layer.name === 'base') {
      await sharp(Buffer.from(svg)).png().toFile(join(outDir, 'base-crop.png'));
    }
  }

  console.log('Done!');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
