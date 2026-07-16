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
- `Ctrl+H` stays left.
- `Ctrl+J` stays down.
- `Ctrl+K` stays up.
- `Ctrl+L` stays right.

These intentionally override the Dvorak-to-QWERTY physical mapping. For example, physical conversion would map Dvorak `Ctrl+J` to QWERTY `Ctrl+C`, but the active config keeps `Ctrl+J` as down navigation.

## Disabled Sentinel Rule

`__disabled__` is not a binding and is not converted by physical position. In Neru, it removes an inherited/default binding with the same normalized key name.

The disabled keys therefore target Neru's built-in defaults literally:

- `Shift+L`: default left click.
- `Shift+R`: default right click.
- `Shift+M`: default middle click.
- `Shift+I`: default mouse down.
- `Shift+U`: default mouse up.
- `` ` ``: default recursive-grid cursor-follow toggle.

For scroll mode, `Shift+G` is a built-in go-bottom binding. It is intentionally not disabled.

## Verified Mappings

Global hotkeys:

- Author `Ctrl+F` -> active `Ctrl+Y`: physical conversion.
- Author `Ctrl+S` -> active `Ctrl+;`: physical conversion; enters scroll mode.

Hint characters:

- Author: `aeudhtnspyfgcrqjkxbmwvz`
- Active: `adfhjkl;rtyuioxcvbnm,./`
- Result: verified physical conversion.

Recursive grid keys:

- Author: `fgcrlaoeuidhtns;qjkxbmwvz`
- Active: `yuiopasdfghjkl;zxcvbnm,./`
- Result: verified physical conversion.

Recursive grid disabled defaults:

- Author and active both disable `Shift+L`, `Shift+R`, `Shift+M`, `Shift+I`, `Shift+U`, and `` ` ``.
- Result: verified as literal default removal, not physical conversion.

Recursive grid actions:

- Active `q`: idle/cancel, local override for closer quit.
- Author `'` -> active `w`: move mouse.
- Author `.` -> active `e`: reset.
- Author `p` -> active `r`: mouse down.
- Author `y` -> active `t`: mouse up.
- Result: mostly physical conversion, with `q` reserved as a closer quit key.

Recursive grid semantic controls:

- `Tab`, `Enter`, `Shift+Enter`, `Ctrl+Enter`, `Space`, `Shift+Space`, and `Ctrl+Space` are unchanged.
- `Ctrl+C` and `Ctrl+H/J/K/L` are unchanged by the Vim precedence rule.
- Author `Ctrl+S` -> active `Ctrl+;`: moves mouse to current selection, then enters scroll mode.

Scroll disabled defaults:

- Author and active both disable `Shift+L`, `Shift+R`, `Shift+M`, `Shift+I`, and `Shift+U`.
- Result: verified as literal default removal, not physical conversion.

Scroll actions:

- Author `Ctrl+C` -> active `Ctrl+C`: Vim precedence.
- Author `f = action feed ctrl+f` -> active `y = action feed ctrl+y`: physical conversion.

The `action feed` mapping is intentionally treated as physical here because Neru feeds parsed key names/keycodes back to macOS. This means the active QWERTY config favors physical equivalence over semantic "Find" for that scroll-mode binding.

## Result

One correction was needed after checking Neru's hardcoded defaults:

- `__disabled__` entries are literal default removals and stay exempt from Dvorak-to-QWERTY conversion.
- Active config now disables only the built-in default bindings that the author intended to remove.
- Active config no longer disables scroll `Shift+G`, preserving Neru's built-in go-bottom binding.

The active QWERTY config preserves the author's physical key layout for actual bindings, with explicit semantic precedence for Vim `Ctrl+C` and `Ctrl+H/J/K/L` controls.
Both QWERTY configs use global `Ctrl+;` to enter scroll mode and recursive-grid `Ctrl+;` to move to the selected cell before entering scroll mode.
