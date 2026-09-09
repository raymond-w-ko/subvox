# Kanata

Documentation and design notes for our [Kanata configuration](../../kanata/).

Our configuration is inspired by Ben Vallack, a YouTuber and tinkerer.

Reference: [Ben Vallack's latest Voyager layout](https://configure.zsa.io/voyager/layouts/9WygO/latest/0).

- [Ben Vallack's layout, in QWERTY](ben-vallack-qwerty-reference.md) — September 2026 layer reference.

## Current layout images

- Windows: [all layers](../../kanata/viz/out/windows.alice/all-layers.png), [base](../../kanata/viz/out/windows.alice/layers/01-base.png), [shortcuts](../../kanata/viz/out/windows.alice/layers/03-shortcut.png).
- macOS: [all layers](../../kanata/viz/out/macos.laptop/all-layers.png), [base](../../kanata/viz/out/macos.laptop/layers/01-base.png), [shortcuts](../../kanata/viz/out/macos.laptop/layers/03-shortcut.png).

The diagrams use soft colors to distinguish modifiers, layer controls, and key chords. On dual-role keys, the tap action sits above the divider and the hold action below it. Small corner labels identify the physical key. Layer headings show the entry keys from the base layout.

Regenerate both layouts from the repository root:

```sh
node kanata/viz/index.js kanata/windows.alice.kbd
node kanata/viz/index.js kanata/macos.laptop.kbd
```

If dependencies are missing, run `npm ci --prefix kanata/viz` first. Output includes a combined sheet, a legend, and individual images under `kanata/viz/out/<layout>/layers/`, each in SVG and PNG. Add `--svg-only` to generate only SVG files. The physical arrangement is an ANSI-style reference, not an exact drawing of each device.
