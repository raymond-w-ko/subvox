// Render the complete keyboard and individual layers from the same layout data.
import { classifyKey, resolveKeyLabel } from './parse.js';

const SCALE = 112;
const PAD = 64;
const TITLE_H = 164;
const FOOTER_H = 98;
const GAP = 36;
const FONT = "'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif";
const INK = '#233342';
const MUTED = '#657480';
const PAPER = '#eef1f3';

const COLORS = {
  normal:         { bg: '#ffffff', fg: '#304351', border: '#d5dce2', label: 'Key' },
  modifier:       { bg: '#e5eefb', fg: '#305d91', border: '#b9cdeb', label: 'Modifier' },
  'layer-toggle': { bg: '#eee8fa', fg: '#675193', border: '#cfc0e9', label: 'Hold for layer' },
  'layer-switch': { bg: '#e0f1e9', fg: '#2b6b50', border: '#afd4c1', label: 'Switch layer' },
  combo:          { bg: '#fae9e4', fg: '#99513e', border: '#e8c2b5', label: 'Key chord' },
  'tap-hold':     { bg: '#e0f0f1', fg: '#28666b', border: '#b0d2d5', label: 'Tap / hold' },
  nop:            { bg: '#f1f3f5', fg: '#84909b', border: '#e4e8ec', label: 'No action' },
};

const LAYERS = {
  base: ['Base', 'Everyday typing, modifiers and layer access.'],
  gaming: ['Gaming', 'A direct layout for games.'],
  shortcut: ['Shortcuts', 'Navigation, editing and tab control.'],
  sym1: ['Symbols', 'Punctuation, operators and brackets.'],
  misc: ['App controls', 'Application shortcuts and clipboard actions.'],
  num: ['Numbers', 'Mirrored number pads within reach.'],
  fn: ['Function keys', 'Function keys on the letter rows.'],
};

const DISPLAY = {
  '␣': 'Space', '⌫': 'Backspace', '⏎': 'Enter', '⇥': 'Tab',
  'L⇧': 'L Shift', 'R⇧': 'R Shift', LCtl: 'L Ctrl', RCtl: 'R Ctrl',
  LAlt: 'L Alt', RAlt: 'R Alt', LMet: 'L Meta', RMet: 'R Meta',
  '⏯': 'Play / pause', '⏮': 'Previous', '⏭': 'Next',
  '🔇': 'Mute', '🔉': 'Volume -', '🔊': 'Volume +',
  '🔅': 'Brightness -', '🔆': 'Brightness +', '⟳': 'Reload',
  Ins: 'Insert', Del: 'Delete',
};

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function text(x, y, value, size = 22, fill = INK, weight = 400, anchor = 'start') {
  return `<text x="${x}" y="${y}" font-size="${size}" fill="${fill}" font-weight="${weight}" text-anchor="${anchor}" dominant-baseline="middle">${esc(value)}</text>\n`;
}

function layerTitle(name) {
  return LAYERS[name.toLowerCase()]?.[0] || name;
}

function prettyLabel(value, platform) {
  const chord = String(value).match(/^([CAMS](?:-[CAMS])*)-(.+)$/);
  if (chord) {
    const modifiers = { C: 'Ctrl', A: 'Alt', M: platform === 'macos' ? 'Cmd' : 'Win', S: 'Shift' };
    return [...chord[1].split('-').map(key => modifiers[key]),
      prettyLabel(resolveKeyLabel(chord[2]), platform)].join('+');
  }
  const label = DISPLAY[value] || String(value);
  if (label.endsWith(' Meta')) {
    return label.replace('Meta', platform === 'macos' ? 'Cmd' : 'Win');
  }
  return /^[a-z]$|^f\d+$/.test(label) ? label.toUpperCase() : label;
}

// Wrap full labels rather than truncating key chords or layer names.
function keyLabel(cx, cy, value, width, color, preferredSize = 27) {
  const maxWidth = width - 18;
  let lines = [value];
  if (value.length * preferredSize * 0.56 > maxWidth) {
    const isChord = value.includes('+') && !/\s/.test(value);
    const parts = isChord ? value.match(/[^+]+\+?/g) : value.split(' ');
    const lineLimit = Math.max(8, Math.floor(maxWidth / (preferredSize * 0.56)));
    if (parts?.length > 1) {
      lines = [];
      let line = '';
      for (const part of parts) {
        const candidate = line ? line + (isChord ? '' : ' ') + part : part;
        if (line && candidate.length > lineLimit) {
          lines.push(line);
          line = part;
        } else {
          line = candidate;
        }
      }
      if (line) lines.push(line);
    }
  }
  const longest = Math.max(...lines.map(line => line.length), 1);
  const size = Math.min(preferredSize, maxWidth / (longest * 0.56), 62 / lines.length);
  return lines.map((line, i) => text(cx, cy + (i - (lines.length - 1) / 2) * (size + 3),
    line, size, color, 600, 'middle')).join('');
}

function svgStart(width, height, title) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img">
<title>${esc(title)}</title>
<defs><style>text { font-family: ${FONT}; }</style></defs>
<rect width="${width}" height="${height}" fill="${PAPER}"/>
`;
}

function dimensions(bounds) {
  return {
    width: Math.ceil(bounds.width * SCALE + PAD * 2),
    height: Math.ceil(bounds.height * SCALE + TITLE_H + FOOTER_H),
  };
}

function renderKeys(defsrc, layerKeys, aliases, layout, platform) {
  let svg = '';
  defsrc.forEach((source, index) => {
    const pos = layout[source];
    if (!pos || layerKeys[index] === undefined) return;
    const info = classifyKey(layerKeys[index], aliases);
    const c = COLORS[info.type] || COLORS.normal;
    const x = PAD + pos.x * SCALE;
    const y = TITLE_H + pos.y * SCALE;
    const w = pos.w * SCALE - 10;
    const h = pos.h * SCALE - 10;
    const physical = prettyLabel(resolveKeyLabel(source), platform);
    let tap = prettyLabel(info.tap, platform);
    const hold = info.type === 'layer-toggle' && info.hold
      ? layerTitle(info.hold) : info.hold && prettyLabel(info.hold, platform);
    let mode = '';
    if (tap.startsWith('OS ')) {
      mode = 'ONE SHOT';
      tap = prettyLabel(info.tap.slice(3), platform);
    } else if (info.type === 'layer-switch') {
      mode = 'SWITCH';
      tap = layerTitle(info.tap.replace(/^->\s*/, ''));
    } else if (info.type === 'layer-toggle' && !hold) {
      mode = 'LAYER';
      tap = layerTitle(info.tap.replace(/^\[|\]$/g, ''));
    }
    svg += `<g data-source="${esc(source)}"><title>${esc(physical + ': ' + (info.type === 'nop' ? 'No action' : (mode ? mode + ' ' : '') + tap + (hold ? '; hold ' + hold : '')))}</title>\n`;
    if (info.type !== 'nop') {
      svg += `<rect x="${x}" y="${y + 3}" width="${w}" height="${h}" rx="13" fill="#dce2e7"/>\n`;
    }
    svg += `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="13" fill="${c.bg}" stroke="${c.border}" stroke-width="1.3"/>\n`;
    if (info.type === 'nop') {
      svg += text(x + 12, y + 18, physical, 13, c.fg);
    } else if (hold) {
      if (tap !== physical) svg += text(x + 12, y + 16, physical, 12, MUTED);
      svg += keyLabel(x + w / 2, y + (tap !== physical ? 36 : 32), tap, w, c.fg, tap !== physical ? 24 : 27);
      svg += `<line x1="${x + 14}" y1="${y + 55}" x2="${x + w - 14}" y2="${y + 55}" stroke="${c.border}"/>\n`;
      svg += keyLabel(x + w / 2, y + 77, hold, w, c.fg, 18);
    } else {
      const remapped = tap !== physical || mode;
      if (remapped) svg += text(x + 12, y + 18, physical, 13, MUTED);
      if (mode) svg += text(x + w / 2, y + 43, mode, 11, c.fg, 600, 'middle');
      svg += keyLabel(x + w / 2, y + (mode ? 70 : remapped ? 61 : h / 2),
        tap, w, c.fg);
    }
    svg += '</g>\n';
  });
  return svg;
}

function legendRow(width, y) {
  let x = PAD;
  let svg = '';
  const spacing = (width - PAD * 2) / Object.keys(COLORS).length;
  for (const c of Object.values(COLORS)) {
    svg += `<circle cx="${x + 6}" cy="${y}" r="6" fill="${c.fg}"/>\n`;
    svg += text(x + 23, y, c.label, 17, MUTED);
    x += spacing;
  }
  return svg;
}

function entryHint(name, defsrc, layers, aliases, platform) {
  if (name === 'base') return 'DEFAULT';
  const base = layers.find(layer => layer.name === 'base');
  if (!base) return '';
  const holds = [];
  const switches = [];
  base.keys.forEach((key, i) => {
    const info = classifyKey(key, aliases);
    const source = prettyLabel(resolveKeyLabel(defsrc[i]), platform);
    if (info.type === 'layer-toggle' && info.hold?.toLowerCase() === name.toLowerCase()) holds.push(source);
    if (info.type === 'layer-switch' && info.tap === '-> ' + name) switches.push(source);
  });
  if (holds.length) return 'HOLD  ' + holds.join('  /  ');
  if (switches.length) return 'PRESS  ' + switches.join('  /  ');
  return '';
}

function renderCard(layer, defsrc, aliases, layout, bounds, options = {}) {
  const { width, height } = dimensions(bounds);
  const { platform = 'windows', index = 0, layers = [], name = 'Kanata' } = options;
  const hint = entryHint(layer.name, defsrc, layers, aliases, platform);
  let svg = `<rect x="20" y="12" width="${width - 40}" height="${height - 24}" rx="28" fill="#fafbfc" stroke="#dce2e7"/>\n`;
  svg += text(PAD, 49, String(index + 1).padStart(2, '0') + '  /  ' + name.toUpperCase(), 15, MUTED, 600);
  svg += text(PAD, 92, layerTitle(layer.name), 40, INK, 700);
  svg += text(PAD, 132, LAYERS[layer.name]?.[1] || '', 20, MUTED);
  if (hint) {
    const pillWidth = Math.max(146, hint.length * 10 + 44);
    svg += `<rect x="${width - PAD - pillWidth}" y="61" width="${pillWidth}" height="48" rx="24" fill="#e9edf1"/>\n`;
    svg += text(width - PAD - pillWidth / 2, 85, hint, 17, INK, 600, 'middle');
  }
  svg += renderKeys(defsrc, layer.keys, aliases, layout, platform);
  svg += legendRow(width, height - 42);
  return svg;
}

export function renderLayerSvg(layerName, defsrc, layerKeys, aliases, layout, bounds, options = {}) {
  const { width, height } = dimensions(bounds);
  return svgStart(width, height, layerTitle(layerName)) +
    renderCard({ name: layerName, keys: layerKeys }, defsrc, aliases, layout, bounds, options) + '</svg>';
}

export function renderAllLayersSvg(defsrc, layers, aliases, layout, bounds, options = {}) {
  const { width, height } = dimensions(bounds);
  const header = 252;
  const totalHeight = header + layers.length * (height + GAP) + 20;
  const name = options.name || 'Kanata';
  let svg = svgStart(width, totalHeight, name + ' — all layers');
  svg += text(PAD, 56, 'KANATA  /  LAYOUT REFERENCE', 17, MUTED, 600);
  svg += text(PAD, 117, name, 56, INK, 700);
  svg += text(PAD, 174, 'Tap above the divider. Hold below it. Small corner labels show the physical key.', 24, MUTED);
  svg += text(width - PAD, 117, layers.length + ' LAYERS  /  ' + defsrc.length + ' KEYS', 19, MUTED, 600, 'end');
  for (let i = 0; i < layers.length; i++) {
    svg += `<g transform="translate(0, ${header + i * (height + GAP)})">\n`;
    svg += renderCard(layers[i], defsrc, aliases, layout, bounds, { ...options, index: i, layers });
    svg += '</g>\n';
  }
  return svg + '</svg>';
}

export function renderLegendSvg() {
  const width = 900;
  const height = 780;
  let svg = svgStart(width, height, 'Reading the layout');
  svg += text(56, 68, 'Reading the layout', 36, INK, 700);
  svg += text(56, 116, 'Tap above the divider; hold below it.', 23, MUTED);
  svg += text(56, 150, 'Small corner labels identify the physical key.', 23, MUTED);
  Object.values(COLORS).forEach((c, i) => {
    const y = 204 + i * 72;
    svg += `<rect x="56" y="${y}" width="58" height="46" rx="12" fill="${c.bg}" stroke="${c.border}"/>\n`;
    svg += text(136, y + 23, c.label, 25, c.fg, 600);
  });
  svg += text(56, 739, 'L / R = left / right modifier. ONE SHOT = one-shot modifier.', 20, MUTED);
  return svg + '</svg>';
}
