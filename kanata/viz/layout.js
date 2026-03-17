// Physical key positions for ANSI keyboard layout
// Each key: { x, y, w, h } in key-units (1u = standard key width)

const ROW_H = 1;
const GAP = 0.1;

const rows = [
  // Row 0: Function keys
  {
    y: 0,
    keys: [
      { id: 'f1', w: 1 }, { id: 'f2', w: 1 }, { id: 'f3', w: 1 }, { id: 'f4', w: 1 },
      { id: 'f5', w: 1, gap: 0.5 }, { id: 'f6', w: 1 }, { id: 'f7', w: 1 }, { id: 'f8', w: 1 },
      { id: 'f9', w: 1, gap: 0.5 }, { id: 'f10', w: 1 }, { id: 'f11', w: 1 }, { id: 'f12', w: 1 },
      { id: 'ins', w: 1, gap: 0.5 },
    ],
  },
  // Row 1: Number row
  {
    y: 1.25,
    keys: [
      { id: 'grv', w: 1 }, { id: '1', w: 1 }, { id: '2', w: 1 }, { id: '3', w: 1 },
      { id: '4', w: 1 }, { id: '5', w: 1 }, { id: '6', w: 1 }, { id: '7', w: 1 },
      { id: '8', w: 1 }, { id: '9', w: 1 }, { id: '0', w: 1 },
      { id: 'min', w: 1 }, { id: '=', w: 1 }, { id: 'bspc', w: 2 },
    ],
  },
  // Row 2: QWERTY row
  {
    y: 2.25,
    keys: [
      { id: 'tab', w: 1.5 }, { id: 'q', w: 1 }, { id: 'w', w: 1 }, { id: 'e', w: 1 },
      { id: 'r', w: 1 }, { id: 't', w: 1 }, { id: 'y', w: 1 }, { id: 'u', w: 1 },
      { id: 'i', w: 1 }, { id: 'o', w: 1 }, { id: 'p', w: 1 },
      { id: 'lbrc', w: 1 }, { id: 'rbrc', w: 1 }, { id: 'bksl', w: 1.5 },
    ],
  },
  // Row 3: Home row
  {
    y: 3.25,
    keys: [
      { id: 'caps', w: 1.75 }, { id: 'a', w: 1 }, { id: 's', w: 1 }, { id: 'd', w: 1 },
      { id: 'f', w: 1 }, { id: 'g', w: 1 }, { id: 'h', w: 1 }, { id: 'j', w: 1 },
      { id: 'k', w: 1 }, { id: 'l', w: 1 }, { id: 'scln', w: 1 },
      { id: 'apos', w: 1 }, { id: 'ret', w: 2.25 },
    ],
  },
  // Row 4: Bottom row
  {
    y: 4.25,
    keys: [
      { id: 'lsft', w: 2.25 }, { id: 'z', w: 1 }, { id: 'x', w: 1 }, { id: 'c', w: 1 },
      { id: 'v', w: 1 }, { id: 'b', w: 1 }, { id: 'n', w: 1 }, { id: 'm', w: 1 },
      { id: 'comm', w: 1 }, { id: '.', w: 1 }, { id: '/', w: 1 },
      { id: 'rsft', w: 2.75 },
    ],
  },
  // Row 5: Space row (arrows handled separately in buildLayout)
  {
    y: 5.25,
    keys: [
      { id: 'fn', w: 1.25, optional: true },
      { id: 'lctl', w: 1.25 }, { id: 'lalt', w: 1.25 }, { id: 'lmet', w: 1.25 },
      { id: 'spc', w: 6.25 },
      { id: 'rmet', w: 1.25 }, { id: 'ralt', w: 1.25 },
    ],
  },
];

export function buildLayout(defsrcKeys) {
  const keySet = new Set(defsrcKeys);
  const layout = {};

  for (const row of rows) {
    let x = 0;
    for (const key of row.keys) {
      if (key.optional && !keySet.has(key.id)) continue;
      if (key.gap) x += key.gap;
      layout[key.id] = {
        x,
        y: row.y,
        w: key.w,
        h: ROW_H,
      };
      x += key.w + GAP;
    }
  }

  // Arrow keys: inverted-T pushed right, past rsft
  // up on row 4 (4.25), left/down/right on row 5 (5.25)
  const rsft = layout['rsft'];
  if (rsft) {
    const arrowStart = rsft.x + rsft.w + 0.4; // gap after rsft
    layout['left']  = { x: arrowStart,               y: 5.25, w: 1, h: ROW_H };
    layout['down']  = { x: arrowStart + 1 + GAP,     y: 5.25, w: 1, h: ROW_H };
    layout['right'] = { x: arrowStart + 2 + GAP * 2, y: 5.25, w: 1, h: ROW_H };
    layout['up']    = { x: arrowStart + 1 + GAP,     y: 4.25, w: 1, h: ROW_H };
  }

  return layout;
}

// Total keyboard dimensions in key-units
export function getKeyboardBounds(layout) {
  let maxX = 0, maxY = 0;
  for (const k of Object.values(layout)) {
    maxX = Math.max(maxX, k.x + k.w);
    maxY = Math.max(maxY, k.y + k.h);
  }
  return { width: maxX, height: maxY };
}
