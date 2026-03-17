// Parse kanata .kbd files into structured data

export function tokenize(src) {
  const tokens = [];
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (ch === ';' && src[i + 1] === ';') {
      while (i < src.length && src[i] !== '\n') i++;
      continue;
    }
    if (/\s/.test(ch)) { i++; continue; }
    if (ch === '(' || ch === ')') {
      tokens.push(ch);
      i++;
      continue;
    }
    if (ch === '"') {
      let s = '"';
      i++;
      while (i < src.length && src[i] !== '"') {
        if (src[i] === '\\') { s += src[i++]; }
        s += src[i++];
      }
      s += '"';
      i++;
      tokens.push(s);
      continue;
    }
    // symbol/keyword
    let sym = '';
    while (i < src.length && !/[\s()]/.test(src[i])) {
      sym += src[i++];
    }
    tokens.push(sym);
  }
  return tokens;
}

export function parseSexp(tokens) {
  const forms = [];
  let i = 0;

  function readForm() {
    if (tokens[i] === '(') {
      i++; // skip (
      const list = [];
      while (i < tokens.length && tokens[i] !== ')') {
        list.push(readForm());
      }
      i++; // skip )
      return list;
    }
    return tokens[i++];
  }

  while (i < tokens.length) {
    forms.push(readForm());
  }
  return forms;
}

export function parseKbd(src) {
  const tokens = tokenize(src);
  const forms = parseSexp(tokens);

  let defsrc = [];
  const layers = [];
  const aliases = {};
  const vars = {};

  for (const form of forms) {
    if (!Array.isArray(form)) continue;
    const head = form[0];

    if (head === 'defsrc') {
      defsrc = form.slice(1);
    }

    if (head === 'deflayer') {
      const name = form[1];
      const keys = form.slice(2);
      layers.push({ name, keys });
    }

    if (head === 'defalias') {
      for (let j = 1; j < form.length - 1; j += 2) {
        const name = form[j];
        const value = form[j + 1];
        aliases[name] = value;
      }
    }

    if (head === 'defvar') {
      for (let j = 1; j < form.length - 1; j += 2) {
        vars[form[j]] = form[j + 1];
      }
    }
  }

  return { defsrc, layers, aliases, vars };
}

// Resolve an alias to a human-readable description
export function resolveAlias(name, aliases) {
  const val = aliases[name];
  if (!val) return { tap: name, hold: null, type: 'normal' };

  if (Array.isArray(val)) {
    const fn = val[0];

    if (fn === 'tap-hold' || fn === 'tap-hold-press' || fn === 'tap-hold-release') {
      const tap = resolveKeyLabel(val[3]);
      const hold = resolveKeyLabel(val[4]);
      const holdType = classifyHold(val[4]);
      return { tap, hold, type: holdType };
    }

    if (fn === 'one-shot-press' || fn === 'one-shot-release') {
      const key = resolveKeyLabel(val[2] || val[1]);
      return { tap: `OS ${key}`, hold: null, type: 'modifier' };
    }

    if (fn === 'layer-switch') {
      return { tap: `→${val[1]}`, hold: null, type: 'layer-switch' };
    }

    if (fn === 'layer-toggle') {
      return { tap: `[${val[1]}]`, hold: null, type: 'layer-toggle' };
    }
  }

  return { tap: resolveKeyLabel(val), hold: null, type: 'normal' };
}

function classifyHold(val) {
  if (typeof val === 'string') {
    if (val.startsWith('@l_') || val.startsWith('@')) {
      // check if it's a layer reference
      const inner = val.replace(/^@/, '');
      if (inner.startsWith('l_')) return 'layer-toggle';
    }
    if (['lctl', 'rctl', 'lalt', 'ralt', 'lmet', 'rmet', 'lsft', 'rsft'].includes(val)) {
      return 'modifier';
    }
  }
  return 'tap-hold';
}

const KEY_LABELS = {
  'spc': '␣', 'bspc': '⌫', 'ret': '⏎', 'tab': '⇥', 'esc': 'Esc',
  'lsft': 'L⇧', 'rsft': 'R⇧', 'lctl': 'LCtl', 'rctl': 'RCtl',
  'lalt': 'LAlt', 'ralt': 'RAlt', 'lmet': 'LMet', 'rmet': 'RMet',
  'caps': 'Caps', 'grv': '`', 'min': '-', 'bksl': '\\',
  'lbrc': '[', 'rbrc': ']', 'scln': ';', 'apos': "'", 'comm': ',',
  'ins': 'Ins', 'del': 'Del', 'home': 'Home', 'end': 'End',
  'up': '↑', 'down': '↓', 'left': '←', 'right': '→',
  'pp': '⏯', 'prev': '⏮', 'next': '⏭',
  'mute': '🔇', 'vold': '🔉', 'volu': '🔊',
  'brdown': '🔅', 'brup': '🔆',
  'lrld': '⟳', 'fn': 'Fn',
  'lctrl': 'LCtl', 'kp.': '.',
  'S-1': '!', 'S-2': '@', 'S-3': '#', 'S-4': '$', 'S-5': '%',
  'S-6': '^', 'S-7': '&', 'S-8': '*', 'S-9': '(', 'S-0': ')',
  'S-min': '_', 'S-=': '+', 'S-grv': '~', 'S-bksl': '|',
  'S-scln': ':', 'S-apos': '"', 'S-lbrc': '{', 'S-rbrc': '}',
};

export function resolveKeyLabel(val) {
  if (val === '•') return '';
  if (typeof val === 'string') {
    if (val.startsWith('@')) {
      return val.slice(1);
    }
    return KEY_LABELS[val] || val;
  }
  if (Array.isArray(val)) {
    return val.join(' ');
  }
  return String(val);
}

export function classifyKey(keyStr, aliases) {
  if (keyStr === '•') return { tap: '', hold: null, type: 'nop' };

  if (typeof keyStr === 'string' && keyStr.startsWith('@')) {
    const aliasName = keyStr.slice(1);
    return resolveAlias(aliasName, aliases);
  }

  // Shifted combos
  if (typeof keyStr === 'string' && /^[CAMS](-[CAMS])*-/.test(keyStr)) {
    return { tap: resolveKeyLabel(keyStr), hold: null, type: 'combo' };
  }

  return { tap: resolveKeyLabel(keyStr), hold: null, type: 'normal' };
}
