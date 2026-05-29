// Generate SVG for a keyboard layer

import { classifyKey } from './parse.js';

const SCALE = 120; // pixels per key-unit (2x for high-res)
const PAD = 40;
const KEY_R = 8; // border radius
const KEY_PAD = 4; // inner padding
const FONT_STACK = "'JetBrains Mono', 'Cascadia Mono', 'Consolas', 'Menlo', monospace";
const BASE_FONT_SIZE = 22;
const MIN_FONT_SIZE = 12;
const CHAR_WIDTH_RATIO = 0.62;

const COLORS = {
  'normal':       { bg: '#303033', fg: '#f0f0f0', border: '#606064' },
  'nop':          { bg: '#151617', fg: '#33363a', border: '#27292d' },
  'modifier':     { bg: '#123c66', fg: '#9fd0ff', border: '#3e7db4' },
  'layer-toggle': { bg: '#67410f', fg: '#ffd07a', border: '#b77a24' },
  'layer-switch': { bg: '#315f12', fg: '#b8ea7c', border: '#6dab33' },
  'combo':        { bg: '#5c1a6e', fg: '#efa7ff', border: '#9744aa' },
  'tap-hold':     { bg: '#14535a', fg: '#9de7e0', border: '#358f96' },
};

function escXml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function truncate(s, maxLen) {
  if (s.length <= maxLen) return s;
  if (maxLen <= 3) return s.slice(0, maxLen);
  return s.slice(0, maxLen - 3) + '...';
}

function fitLabel(text, keyWidthPx, preferredSize = BASE_FONT_SIZE) {
  const available = Math.max(12, keyWidthPx - KEY_PAD * 2 - 12);
  if (!text) return { text: '', fontSize: preferredSize };

  const preferredWidth = text.length * preferredSize * CHAR_WIDTH_RATIO;
  if (preferredWidth <= available) {
    return { text, fontSize: preferredSize };
  }

  const scaledSize = Math.floor(available / (text.length * CHAR_WIDTH_RATIO));
  if (scaledSize >= MIN_FONT_SIZE) {
    return { text, fontSize: scaledSize };
  }

  const maxChars = Math.max(1, Math.floor(available / (MIN_FONT_SIZE * CHAR_WIDTH_RATIO)));
  return { text: truncate(text, maxChars), fontSize: MIN_FONT_SIZE };
}

function renderText(x, y, label, fontSize, fill, extra = '') {
  return `<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="middle" font-size="${fontSize}" fill="${fill}"${extra}>${escXml(label)}</text>
`;
}

function renderKeysSvg(defsrc, layerKeys, aliases, layout, titleOffset) {
  let svg = '';
  for (let i = 0; i < defsrc.length; i++) {
    const srcKey = defsrc[i];
    const pos = layout[srcKey];
    if (!pos) continue;

    const dstKey = layerKeys[i];
    if (dstKey === undefined) continue;

    const info = classifyKey(dstKey, aliases);
    const colors = COLORS[info.type] || COLORS.normal;
    const inactive = info.type === 'nop';

    const x = PAD + pos.x * SCALE;
    const y = titleOffset + PAD + pos.y * SCALE;
    const w = pos.w * SCALE - 4;
    const h = pos.h * SCALE - 4;
    const strokeWidth = inactive ? 1.5 : 2;

    svg += `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${KEY_R}" fill="${colors.bg}" stroke="${colors.border}" stroke-width="${strokeWidth}"/>
`;

    if (info.hold) {
      const tap = fitLabel(info.tap, w, BASE_FONT_SIZE);
      const hold = fitLabel(info.hold, w, BASE_FONT_SIZE - 2);
      const tapY = y + h * 0.34;
      const holdY = y + h * 0.69;

      svg += `<line x1="${x + 10}" y1="${y + h / 2}" x2="${x + w - 10}" y2="${y + h / 2}" stroke="${colors.border}" stroke-width="1" stroke-dasharray="4,4" opacity="0.75"/>
`;
      svg += renderText(x + w / 2, tapY, tap.text, tap.fontSize, colors.fg, ' font-weight="700"');
      svg += renderText(x + w / 2, holdY, hold.text, hold.fontSize, colors.fg, ' opacity="0.78"');
    } else if (info.tap) {
      const label = fitLabel(info.tap, w);
      svg += renderText(x + w / 2, y + h / 2, label.text, label.fontSize, colors.fg, ' font-weight="600"');
    }
  }
  return svg;
}

function renderSvgDefs() {
  return `<defs>
  <style>
    text { font-family: ${FONT_STACK}; letter-spacing: 0; }
  </style>
</defs>
`;
}

export function renderLayerSvg(layerName, defsrc, layerKeys, aliases, layout, bounds) {
  const TITLE_H = 80;
  const W = Math.ceil(bounds.width * SCALE + PAD * 2);
  const H = Math.ceil(bounds.height * SCALE + PAD * 2 + TITLE_H);

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
${renderSvgDefs()}<rect width="${W}" height="${H}" fill="#101113" rx="12"/>
<text x="${W / 2}" y="52" text-anchor="middle" dominant-baseline="middle" font-size="34" font-weight="700" fill="#e6e6e6">${escXml(layerName)}</text>
`;

  svg += renderKeysSvg(defsrc, layerKeys, aliases, layout, TITLE_H);
  svg += '</svg>';
  return svg;
}

export function renderAllLayersSvg(defsrc, layers, aliases, layout, bounds) {
  const TITLE_H = 80;
  const LAYER_GAP = 28;
  const singleH = Math.ceil(bounds.height * SCALE + PAD * 2 + TITLE_H);
  const W = Math.ceil(bounds.width * SCALE + PAD * 2);
  const totalH = singleH * layers.length + LAYER_GAP * (layers.length + 1);

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${totalH}" viewBox="0 0 ${W} ${totalH}">
${renderSvgDefs()}<rect width="${W}" height="${totalH}" fill="#101113" rx="12"/>
`;

  for (let li = 0; li < layers.length; li++) {
    const layer = layers[li];
    const yOff = LAYER_GAP + li * (singleH + LAYER_GAP);

    svg += `<g transform="translate(0, ${yOff})">`;
    svg += `<text x="${W / 2}" y="52" text-anchor="middle" dominant-baseline="middle" font-size="34" font-weight="700" fill="#e6e6e6">${escXml(layer.name)}</text>
`;

    svg += renderKeysSvg(defsrc, layer.keys, aliases, layout, TITLE_H);
    svg += '</g>\n';
  }

  svg += '</svg>';
  return svg;
}

// Legend SVG
export function renderLegendSvg() {
  const entries = [
    ['normal', 'Normal key'],
    ['modifier', 'Modifier / One-shot'],
    ['layer-toggle', 'Layer toggle (hold)'],
    ['layer-switch', 'Layer switch'],
    ['combo', 'Shift/Ctrl combo'],
    ['tap-hold', 'Tap-hold (dual role)'],
    ['nop', 'No action'],
  ];
  const W = 600;
  const H = entries.length * 56 + 50;
  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
${renderSvgDefs()}<rect width="${W}" height="${H}" fill="#101113" rx="10"/>
<text x="${W / 2}" y="32" text-anchor="middle" dominant-baseline="middle" font-size="26" fill="#e6e6e6" font-weight="700">Legend</text>
`;
  entries.forEach(([type, label], i) => {
    const c = COLORS[type];
    const y = 60 + i * 56;
    svg += `<rect x="20" y="${y}" width="44" height="38" rx="6" fill="${c.bg}" stroke="${c.border}" stroke-width="${type === 'nop' ? 1.5 : 2}"/>`;
    svg += `<text x="80" y="${y + 19}" dominant-baseline="middle" font-size="24" fill="${c.fg}" font-weight="600">${label}</text>
`;
  });
  svg += '</svg>';
  return svg;
}
