# Neru Keymap Comparison

## Files

- Author Dvorak reference: `configs/neru-y3owk1n.toml`
- Active QWERTY config: `configs/neru-qwerty.toml`
- Active Windows QWERTY config: `configs/neru-qwerty.windows.toml`

## Conversion Rule

Most author bindings are converted by physical key position from Dvorak labels to QWERTY labels.

```text
Dvorak: ' , . p y f g c r l
QWERTY: q w e r t y u i o p

Dvorak: a o e u i d h t n s
QWERTY: a s d f g h j k l ;

Dvorak: ; q j k x b m w v z
QWERTY: z x c v b n m , . /
```

## Precedence Rule

Vim-style controls stay semantic and are not converted by physical position:

- `Ctrl+C` stays `Ctrl+C` for idle/cancel.
- `Ctrl+D` stays `Ctrl+D` for page down.
- `Ctrl+U` stays `Ctrl+U` for page up.
- `Ctrl+H` stays left.
- `Ctrl+J` stays down.
- `Ctrl+K` stays up.
- `Ctrl+L` stays right.

These intentionally override the Dvorak-to-QWERTY physical mapping. For example, physical conversion would map Dvorak `Ctrl+J` to QWERTY `Ctrl+C`, but the active config keeps `Ctrl+J` as down navigation.

## Disabled Sentinel Rule

Copy every `__disabled__` entry from the author config 1:1. Do not convert its key by physical position. The key names a hardcoded Neru default rather than a user binding.

Neru declares the relevant hardcoded defaults in `internal/config/config_defaults.go`:

- Recursive grid: `Escape`, `` ` ``, `Space`, `Backspace`, `Shift+L`, `Shift+R`, `Shift+M`, `Shift+I`, `Shift+U`, `Up`, `Down`, `Left`, and `Right`.
- Scroll: `Escape`, `k`, `j`, `h`, `l`, `gg`, `Shift+G`, `u`, `PageUp`, `d`, `PageDown`, `Shift+L`, `Shift+R`, `Shift+M`, `Shift+I`, `Shift+U`, `Up`, `Down`, `Left`, and `Right`.

This rule includes spelling and modifiers. For example, author `d = "__disabled__"` stays `d = "__disabled__"`, not `h = "__disabled__"` after Dvorak-to-QWERTY conversion.

## Verified Mappings

Global hotkeys:

- Author `Ctrl+F` -> active `Ctrl+Y`: physical conversion.
- Author `Ctrl+S` -> active `Ctrl+;`: physical conversion; enters scroll mode.

Recursive grid keys:

- Author: `gcrhtnmwv`
- Active: `uiojklm,.`
- Result: verified physical conversion.

Recursive grid disabled defaults:

- Author and active both disable `Shift+M`, `Shift+I`, `Shift+U`, `Shift+R`, and `` ` ``.
- Result: verified as literal default removal, not physical conversion.

Recursive grid actions:

- Active `q`: idle/cancel, local override for closer quit.
- Author `,` -> active `w`: center mouse.
- Author `.` -> active `e`: reset.
- Author `p` -> active `r`: mouse down.
- Author `i`, `u`, `e`, and `o` -> active `g`, `f`, `d`, and `s`: move mouse, left click, middle click, and right click.
- Author `s = action feed ctrl+s` -> active `; = action feed ctrl+;`: physical conversion of both the binding and fed key.
- Result: mostly physical conversion, with `q` reserved as a closer quit key.

Recursive grid semantic controls:

- `Tab` is unchanged.
- `Ctrl+C` and `Ctrl+H/J/K/L` are unchanged by the Vim precedence rule.
- `Shift+H/J/K/L` are unchanged for cell movement.
- Author `Ctrl+F` -> active `Ctrl+Y`: reruns recursive grid at depth 2 by physical position.
- Author `Ctrl+S` -> active `Ctrl+;`: moves mouse to current selection, then enters scroll mode.

Scroll disabled defaults:

- Author and active both disable `Shift+L`, `Shift+M`, `Shift+I`, `Shift+U`, `Shift+R`, and `d`.
- The literal `d` sentinel takes precedence over the physical conversion of author `e = action middle_click`, which would also use active `d`. The active scroll table therefore omits that translated middle-click binding.
- Result: verified as literal default removal, not physical conversion.

Scroll actions:

- Author `Ctrl+C` -> active `Ctrl+C`: Vim precedence.
- Author `Ctrl+D` -> active `Ctrl+D` and author `Ctrl+U` -> active `Ctrl+U`: Vim half-page controls stay semantic.
- Author `,`, `p`, `i`, `u`, and `o` -> active `w`, `r`, `g`, `f`, and `s`: physical conversion for non-conflicting mouse actions.
- Author `f = action feed ctrl+f` -> active `y = action feed ctrl+y`: physical conversion.
- Explicit `Enter`, `Shift+Enter`, and `Ctrl+Enter` mouse bindings were removed to match the author config.

The `action feed` mappings are intentionally treated as physical because Neru feeds parsed key names/keycodes back to the OS. The active QWERTY configs therefore favor physical equivalence over semantic command names.

## Result

Corrections after checking Neru's hardcoded defaults:

- Every `__disabled__` entry is copied 1:1 and stays exempt from Dvorak-to-QWERTY conversion.
- Active configs include the author's literal scroll `d` sentinel.
- The translated scroll middle-click binding is omitted because it collides with that reserved `d` key.
- Active config no longer disables scroll `Shift+G`, preserving Neru's built-in go-bottom binding.

The active QWERTY config preserves the author's physical key layout where it does not conflict with a copied sentinel. Vim and Unix control primitives stay semantic.
Both QWERTY configs use global `Ctrl+;` to enter scroll mode and recursive-grid `Ctrl+;` to move to the selected cell before entering scroll mode.
