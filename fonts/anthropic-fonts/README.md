# Anthropic Fonts — Personal Use

I have been using Claude fonts from Anthropic for my own personal projects. I do not own the rights to these fonts — they belong to Anthropic. I just find it practical to have them available directly on GitHub for quick access across my machines and tools.

If you are from Anthropic and want this removed, just reach out.

---

## What is in here

### `/ttf`
Static TTF instances exported from the original variable fonts, covering weights **300 to 800** (Light, Regular, Medium, SemiBold, Bold, ExtraBold, Black).

Families included:
- **AnthropicSans** — Romans + Italics
- **AnthropicSerif** — Romans + Italics
- **AnthropicMono** — Romans

### `/woff2-original`
The original variable woff2 files as shipped by Anthropic. These are proper variable fonts with a `wght` axis (300-800). Use these for web projects via `@font-face`.

---

## Usage (web)

```css
@font-face {
  font-family: 'AnthropicSans';
  src: url('./woff2-original/AnthropicSans-Romans.woff2') format('woff2');
  font-weight: 300 800;
  font-style: normal;
}

@font-face {
  font-family: 'AnthropicSans';
  src: url('./woff2-original/AnthropicSans-Italics.woff2') format('woff2');
  font-weight: 300 800;
  font-style: italic;
}
```
