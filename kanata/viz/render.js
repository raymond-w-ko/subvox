// Generate SVG for a keyboard layer

import { classifyKey } from './parse.js';

const SCALE = 120; // pixels per key-unit (2x for high-res)
const PAD = 40;
const KEY_R = 8; // border radius
const KEY_PAD = 4; // inner padding

const COLORS = {
  'normal':       { bg: '#2d2d2d', fg: '#e0e0e0', border: '#555' },
  'nop':          { bg: '#1a1a1a', fg: '#444',     border: '#333' },
  'modifier':     { bg: '#1a3a5c', fg: '#7cb7ff',  border: '#3a6a9c' },
  'layer-toggle': { bg: '#5c3a1a', fg: '#ffb74d',  border: '#9c6a2a' },
  'layer-switch': { bg: '#3a5c1a', fg: '#a5d66f',  border: '#6a9c2a' },
  'combo':        { bg: '#4a1a5c', fg: '#ce93d8',  border: '#7a3a8c' },
  'tap-hold':     { bg: '#1a4a4a', fg: '#80cbc4',  border: '#2a7a7a' },
};

function escXml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function truncate(s, maxLen) {
  if (s.length <= maxLen) return s;
  return s.slice(0, maxLen - 1) + '…';
}

function fontSizeForWidth(text, keyWidthPx) {
  const available = keyWidthPx - KEY_PAD * 2 - 8;
  const charW = 13; // approximate char width at 22px font
  const needed = text.length * charW;
  if (needed <= available) return 22;
  const scaled = Math.floor(22 * available / needed);
  return Math.max(14, scaled);
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

    const x = PAD + pos.x * SCALE;
    const y = titleOffset + PAD + pos.y * SCALE;
    const w = pos.w * SCALE - 4;
    const h = pos.h * SCALE - 4;

    // Key background
    svg += `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${KEY_R}" fill="${colors.bg}" stroke="${colors.border}" stroke-width="2"/>
`;

    if (info.hold) {
      // Tap-hold: tap on top, hold on bottom
      const tapLabel = truncate(info.tap, Math.floor(w / 11));
      const holdLabel = truncate(info.hold, Math.floor(w / 11));
      const tapSize = fontSizeForWidth(tapLabel, w);
      const holdSize = fontSizeForWidth(holdLabel, w);

      // Divider line
      svg += `<line x1="${x + 8}" y1="${y + h / 2}" x2="${x + w - 8}" y2="${y + h / 2}" stroke="${colors.border}" stroke-width="1" stroke-dasharray="4,4"/>
`;
      svg += `<text x="${x + w / 2}" y="${y + h / 2 - 12}" text-anchor="middle" font-size="${tapSize}" fill="${colors.fg}">${escXml(tapLabel)}</text>
`;
      svg += `<text x="${x + w / 2}" y="${y + h / 2 + 28}" text-anchor="middle" font-size="${holdSize}" fill="${colors.fg}" opacity="0.7">${escXml(holdLabel)}</text>
`;
    } else if (info.tap) {
      const label = truncate(info.tap, Math.floor(w / 9));
      const fontSize = fontSizeForWidth(label, w);
      svg += `<text x="${x + w / 2}" y="${y + h / 2 + 8}" text-anchor="middle" font-size="${fontSize}" fill="${colors.fg}">${escXml(label)}</text>
`;
    }
  }
  return svg;
}

export function renderLayerSvg(layerName, defsrc, layerKeys, aliases, layout, bounds) {
  const TITLE_H = 80;
  const W = Math.ceil(bounds.width * SCALE + PAD * 2);
  const H = Math.ceil(bounds.height * SCALE + PAD * 2 + TITLE_H);

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<defs>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&amp;display=swap');
    text { font-family: 'JetBrains Mono', 'Consolas', monospace; }
  </style>
</defs>
<rect width="${W}" height="${H}" fill="#111" rx="12"/>
<text x="${W / 2}" y="52" text-anchor="middle" font-size="36" font-weight="bold" fill="#e0e0e0">${escXml(layerName)}</text>
`;

  svg += renderKeysSvg(defsrc, layerKeys, aliases, layout, TITLE_H);
  svg += '</svg>';
  return svg;
}

export function renderAllLayersSvg(defsrc, layers, aliases, layout, bounds) {
  const TITLE_H = 80;
  const singleH = Math.ceil(bounds.height * SCALE + PAD * 2 + TITLE_H);
  const W = Math.ceil(bounds.width * SCALE + PAD * 2);
  const totalH = singleH * layers.length + 40;

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${totalH}" viewBox="0 0 ${W} ${totalH}">
<defs>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&amp;display=swap');
    text { font-family: 'JetBrains Mono', 'Consolas', monospace; }
  </style>
</defs>
<rect width="${W}" height="${totalH}" fill="#111" rx="12"/>
`;

  for (let li = 0; li < layers.length; li++) {
    const layer = layers[li];
    const yOff = li * singleH + 20;

    svg += `<g transform="translate(0, ${yOff})">`;

    // Title
    svg += `<text x="${W / 2}" y="52" text-anchor="middle" font-size="36" font-weight="bold" fill="#e0e0e0">${escXml(layer.name)}</text>
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
<rect width="${W}" height="${H}" fill="#111" rx="10"/>
<text x="${W / 2}" y="36" text-anchor="middle" font-size="26" fill="#e0e0e0" font-family="monospace">Legend</text>
`;
  entries.forEach(([type, label], i) => {
    const c = COLORS[type];
    const y = 60 + i * 56;
    svg += `<rect x="20" y="${y}" width="44" height="38" rx="6" fill="${c.bg}" stroke="${c.border}" stroke-width="2"/>`;
    svg += `<text x="80" y="${y + 27}" font-size="24" fill="${c.fg}" font-family="monospace">${label}</text>
`;
  });
  svg += '</svg>';
  return svg;
}
