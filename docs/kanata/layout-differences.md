# Current layout versus Ben Vallack

Updated 2026-09-10. Compared with the [September 2026 QWERTY reference](ben-vallack-qwerty-reference.md), based on the supplied screenshots.

## What now matches

Both Windows and macOS use Ben's positions for these base-layer holds. Win means Command on macOS.

| Hold action | Left key | Right key |
| --- | --- | --- |
| Ctrl | S | L |
| Alt | D | K |
| Win / Command | F | J |
| Shortcuts | V | M |
| Symbols / Sym A | C | , |
| App controls / Sym B | X | . |
| Numbers | Z | / |

The move also places our extra Shift holds on **A / ;** and Function-layer holds on **B / N**. The top letter row now has ordinary taps. Letter and punctuation taps and hold timing retain their previous behavior. App controls also matches Ben's page navigation: hold **X** or **.**, then press **I** for Page Up or **K** for Page Down.

## Remaining differences

| Area | Our layout | Ben's reference |
| --- | --- | --- |
| Shift | Hold A / ;, plus one-shot Shift on Caps Lock, apostrophe, and Right Shift in Base | Right thumb Shift; no letter-key Shift holds shown |
| Space | Tap Space; hold Ctrl on Windows or Command on macOS, including the utility layers | Left thumb: Space / Meh on Main; Win on layers 1–4 |
| Extra layer | Function layer on B / N | Mouse layer on Y; no Function layer shown |
| Layer inheritance | Unassigned utility-layer keys do nothing | Many keys inherit Main, including some modifier and layer holds |
| Keyboard | Full keyboard keys remain available in Base | Compact Voyager layout; most outer and number-row keys are blank |
| Gaming | Right Alt switches between Base and Gaming; Caps Lock sends Space in Gaming | Different outer-key and thumb bindings; entry method is not shown |

Meh means Ctrl + Alt + Shift. Our utility layers keep Space and one-shot Right Shift. Their other bindings are listed below.

## Shortcuts

The left-hand shortcut actions use Ben's positions, except A is disabled rather than typing A. Platform-specific bracket and screenshot shortcuts retain their native Windows/macOS behavior.

| Key | Our action |
| --- | --- |
| Q / W | Tab / Esc |
| D | Outdent / hold End |
| F | Indent |
| G | Screenshot |
| Z | Cycle application windows |
| X | Delete / hold Home |
| C / V | Previous / next tab |
| E / R / T / A / S / B | Disabled |

Arrow keys and Enter also share Ben's positions. These actions still differ:

| Action | Our position or behavior | Ben's position or behavior |
| --- | --- | --- |
| Backspace | U | O |
| Delete a word | O: Ctrl+Backspace on Windows, Alt+Backspace on macOS | No corresponding binding shown |
| Screenshot | G: Win+Shift+S on Windows; Ctrl+Command+Shift+4 on macOS | G: Ctrl+Win+Shift+4 |
| Bracket shortcuts | D / F use Ctrl on Windows, Command on macOS; holding D sends End | D / F use Win; holding D sends End |
| Comma | No binding on slash | Slash types comma |

The macOS bracket shortcuts use the same GUI modifier as Ben's Win label. Windows keeps Ctrl for those actions.

## Symbols and app controls

| Area | Our layout | Ben's reference |
| --- | --- | --- |
| Sym A: W | Shift+2 (`@` on US QWERTY) | Alt+3 |
| Sym A: S | Underscore | @ |
| Sym A: bottom left | Z = tilde, C = double quote, V = apostrophe | These keys are disabled |
| Sym B: copy / paste | V / B use Ctrl on Windows, Command on macOS; T is unassigned | V / T use Win |

The macOS copy/paste bindings use the same GUI modifier as Ben, but paste is on B. The left-hand Alt+bracket bindings already match. Symbol output still depends on the host keyboard layout.

## Numbers and gaming

The right-hand number grid matches Ben. We also have a mirrored left-hand number grid, Backspace on G / H, and Enter on Z / slash. Our decimal keys send keypad decimal; Ben's screenshot shows a period but does not establish its keycode.

Gaming keeps ordinary QWERTY typing, normal modifier keys, and Space. Ben adds Caps Word, Alt holds on Z / slash, Backspace / Shift on the left edge, apostrophe / Right Shift on the right edge, and thumb Tab / Ctrl and Delete / Shift bindings. Those features are not present in our Gaming layer.

## Timing and validation

Our tap timeout is 225 ms. Hold thresholds remain 225 ms normally, 275 ms for slower holds, and 325 ms for Shift holds. One-shot timeout remains 500 ms. Ben's timing and tap-hold policies are not visible in the screenshots.

The Windows configuration passes Kanata's `--check`. The macOS configuration passes structural and mapping checks; native macOS validation is still needed because the Windows validator does not recognize the macOS `fn` key. Interactive typing and rollover behavior have not been tested.
