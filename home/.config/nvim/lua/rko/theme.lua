-- Terminal-palette theme. Every color is a palette index, so the terminal
-- theme decides the real colors. Needs 'notermguicolors'.
--
-- Colors come from three sources:
--   * the default fg and bg (no ctermfg/ctermbg),
--   * the hues 1-6 and 9-14 (C.red ... C.light_cyan),
--   * the generated 256-color palette: M.grey() and M.tint().
-- 0, 7 and 15 are not used. Many themes make one of them equal to the
-- terminal background (gruvbox-light: 0 is the bg, 15 is the darkest text).
--
-- Indexes 16-255 assume a terminal that generates them from the theme
-- (Ghostty palette-generate, the dullahan client default): 232-255 is a ramp
-- between the theme bg and fg, and 16-231 is a cube that mixes bg, fg and
-- hues 1-6. With the stock xterm palette they are still usable greys and tints.
--
-- Group spec: { fg = n, bg = n, bold = true } or { link = "Group" }.
-- Only bold is allowed. The groups here also replace plugin groups of the
-- same name. M.load() strips every other attribute (italic, underline,
-- reverse, ...) from all other groups and maps their colors above 15 to the
-- hue 1-14 that is nearest.
--
-- Dev tools: :ThemeDev, :ThemePreview, :ThemeAudit, :ThemeReload
-- (see lua/rko/theme_dev.lua).
local M = {}

local C = {
  red = 1,
  green = 2,
  yellow = 3,
  blue = 4,
  magenta = 5,
  cyan = 6,
  grey = 8,
  light_red = 9,
  light_green = 10,
  light_yellow = 11,
  light_blue = 12,
  light_magenta = 13,
  light_cyan = 14,
}
M.C = C

-- Attributes that are kept. Everything else is removed.
M.ALLOWED_ATTRS = { bold = true, nocombine = true }

-- Group name prefixes that get their colors from this theme in another file
-- (lua/lualine/themes/rko.lua), so M.load() leaves them alone.
local OWNED_PREFIXES = { "lualine_", "ThemeDev" }

-- Colors that can be equal to the terminal background in some themes.
M.UNRELIABLE = { [0] = true, [7] = true, [15] = true }

local function light()
  return vim.o.background == "light"
end

-- A grey k/25 of the way from the theme bg to the theme fg (k = 1..24).
-- The generated ramp always runs dark to light, so a light theme reads it
-- from the other end.
function M.grey(k)
  return light() and 256 - k or 231 + k
end

-- The theme bg mixed toward hue 1-6 (red, green, yellow, blue, magenta,
-- cyan) by k/5 (k = 1..5). The cube corner 16 is the darkest color and 231
-- the lightest, so the bg corner depends on 'background'.
function M.tint(hue, k)
  local function axis(bit)
    if light() then
      return bit == 1 and 5 or 5 - k
    end
    return bit * k
  end
  return 16 + 36 * axis(hue % 2) + 6 * axis(math.floor(hue / 2) % 2) + axis(math.floor(hue / 4))
end

-- Returns the group table for the current 'background'.
function M.groups()
  local grey, tint = M.grey, M.tint
  local dim = grey(14)
  -- Text on a strong hue background: about the terminal bg color.
  local on_color = grey(1)

  local groups = {
    -- Editor UI
    Normal = {},
    NormalFloat = {},
    FloatBorder = { fg = dim },
    FloatShadow = { bg = grey(4) },
    FloatShadowThrough = { bg = grey(4) },
    Cursor = {},
    lCursor = {},
    TermCursor = { fg = on_color, bg = grey(22) },
    CursorLine = { bg = grey(2) },
    CursorColumn = { bg = grey(2) },
    ColorColumn = { bg = grey(2) },
    CursorLineNr = { bold = true },
    LineNr = { fg = dim },
    SignColumn = {},
    Folded = { fg = dim, bg = grey(2) },
    Conceal = { fg = dim },
    NonText = { fg = grey(10) },
    Visual = { bg = grey(6) },
    Search = { bg = tint(C.yellow, 2) },
    CurSearch = { fg = on_color, bg = C.light_yellow, bold = true },
    Substitute = { link = "Search" },
    MatchParen = { bg = tint(C.magenta, 2), bold = true },
    Pmenu = { bg = grey(3) },
    PmenuSel = { bg = grey(7), bold = true },
    PmenuSbar = { bg = grey(3) },
    PmenuThumb = { bg = grey(10) },
    PmenuMatch = { fg = C.light_blue, bold = true },
    PmenuMatchSel = { fg = C.light_blue, bold = true },
    StatusLine = { bg = grey(5) },
    StatusLineNC = { fg = dim, bg = grey(2) },
    TabLineSel = { bold = true },
    WinBar = { fg = dim, bold = true },
    WinBarNC = { fg = dim },
    WinSeparator = { fg = grey(8) },
    Title = { bold = true },
    Directory = { fg = C.light_cyan },
    QuickFixLine = { bg = grey(3), bold = true },
    ModeMsg = { fg = C.light_green },
    MoreMsg = { fg = C.light_cyan },
    Question = { fg = C.light_cyan },
    OkMsg = { fg = C.light_green },
    ErrorMsg = { fg = C.light_red },
    WarningMsg = { fg = C.light_yellow },
    NvimInternalError = { fg = C.light_red, bg = tint(C.red, 2) },
    RedrawDebugNormal = { bg = grey(4) },
    RedrawDebugClear = { bg = tint(C.yellow, 2) },
    RedrawDebugComposed = { bg = tint(C.green, 2) },
    RedrawDebugRecompose = { bg = tint(C.red, 2) },

    -- Syntax
    Comment = { fg = C.magenta },
    Constant = {},
    String = { fg = C.green },
    Identifier = { fg = C.light_blue },
    Function = { fg = C.red },
    Statement = { fg = C.blue, bold = true },
    Operator = {},
    PreProc = { fg = C.light_magenta },
    Type = {},
    Special = { fg = C.cyan },
    Delimiter = {},
    Underlined = { fg = C.light_blue },
    Error = { fg = C.light_red, bg = tint(C.red, 1) },
    Todo = { bg = tint(C.yellow, 1), bold = true },
    ["@variable"] = {},

    -- Markup
    ["@markup.strong"] = { bold = true },
    ["@markup.italic"] = {},
    ["@markup.strikethrough"] = { fg = dim },
    ["@markup.underline"] = { link = "Underlined" },
    ["@markup.heading.1.delimiter.vimdoc"] = { fg = dim },
    ["@markup.heading.2.delimiter.vimdoc"] = { fg = dim },

    -- Diff and spelling
    Added = { fg = C.light_green },
    Changed = { fg = C.light_cyan },
    Removed = { fg = C.light_red },
    DiffAdd = { bg = tint(C.green, 1) },
    DiffChange = { bg = tint(C.blue, 1) },
    DiffText = { bg = tint(C.blue, 2) },
    DiffDelete = { fg = C.light_red, bg = tint(C.red, 1) },
    -- Underline is not allowed, so a tinted background marks the text.
    SpellBad = { bg = tint(C.red, 1) },
    SpellCap = { bg = tint(C.yellow, 1) },
    SpellLocal = { bg = tint(C.green, 1) },
    SpellRare = { bg = tint(C.cyan, 1) },

    -- Diagnostics
    DiagnosticError = { fg = C.light_red },
    DiagnosticWarn = { fg = C.light_yellow },
    DiagnosticInfo = { fg = C.light_cyan },
    DiagnosticHint = { fg = C.light_blue },
    DiagnosticOk = { fg = C.light_green },
    DiagnosticUnderlineError = { bg = tint(C.red, 1) },
    DiagnosticUnderlineWarn = { bg = tint(C.yellow, 1) },
    DiagnosticUnderlineInfo = { bg = tint(C.cyan, 1) },
    DiagnosticUnderlineHint = { bg = tint(C.blue, 1) },
    DiagnosticUnderlineOk = { bg = tint(C.green, 1) },
    DiagnosticDeprecated = { fg = dim },

    -- Plugins
    -- gitsigns links GitSignsNoEOLPreview to this, but nvim 0.12 does not define it.
    DiffNoEOL = { fg = dim },
    GitSignsStagedAdd = { fg = C.green },
    GitSignsStagedChange = { fg = C.cyan },
    GitSignsStagedDelete = { fg = C.red },
    NvimTreeWindowPicker = { fg = on_color, bg = C.light_blue, bold = true },
    TabsFocused = { fg = C.light_green },
    TabsUnfocused = { fg = dim },
    TabsSelected = { bg = grey(5), bold = true },
    TabsSeparator = { fg = grey(8) },
  }

  -- gitsigns only defines the staged groups with GUI colors, so derive the
  -- variants from the base groups above.
  local kinds = {
    Add = "Add",
    Untracked = "Add",
    Change = "Change",
    Changedelete = "Change",
    Delete = "Delete",
    Topdelete = "Delete",
  }
  for kind, base in pairs(kinds) do
    local name = "GitSignsStaged" .. kind
    if kind ~= base then
      groups[name] = { link = "GitSignsStaged" .. base }
    end
    groups[name .. "Nr"] = { link = name }
    groups[name .. "Cul"] = { link = name }
  end
  groups.GitSignsStagedAddLn = { link = "DiffAdd" }
  groups.GitSignsStagedUntrackedLn = { link = "DiffAdd" }
  groups.GitSignsStagedChangeLn = { link = "DiffChange" }
  groups.GitSignsStagedChangedeleteLn = { link = "DiffChange" }
  groups.GitSignsDiffStaged = { link = "DiffAdd" }

  return groups
end

-- Returns true when the theme sets the colors of group `name`. `groups` is
-- the result of M.groups().
function M.owns(name, groups)
  if groups[name] then
    return true
  end
  for _, prefix in ipairs(OWNED_PREFIXES) do
    if vim.startswith(name, prefix) then
      return true
    end
  end
  return false
end

local function to_hl(spec)
  if spec.link then
    return { link = spec.link }
  end
  return { ctermfg = spec.fg, ctermbg = spec.bg, cterm = spec.bold and { bold = true } or nil }
end

local function xterm256_rgb(n)
  if n >= 232 then
    local v = 8 + (n - 232) * 10
    return v, v, v
  end
  local levels = { 0, 95, 135, 175, 215, 255 }
  n = n - 16
  return levels[math.floor(n / 36) + 1], levels[math.floor(n / 6) % 6 + 1], levels[n % 6 + 1]
end

-- Maps a stock xterm 256-color index to a hue 1-14 or to 8 (grey), so a
-- muted red stays red instead of turning grey. Plugins pick these indexes
-- for the stock palette, not for the generated one.
function M.to_ansi(n)
  if n <= 15 then
    return n
  end
  local r, g, b = xterm256_rgb(n)
  local max, min = math.max(r, g, b), math.min(r, g, b)
  if max - min < 40 then
    return C.grey
  end
  local hue
  if max == r then
    hue = ((g - b) / (max - min)) % 6
  elseif max == g then
    hue = (b - r) / (max - min) + 2
  else
    hue = (r - g) / (max - min) + 4
  end
  -- hue is 0-6: red, yellow, green, cyan, blue, magenta.
  local base = ({ C.red, C.yellow, C.green, C.cyan, C.blue, C.magenta })[math.floor(hue + 0.5) % 6 + 1]
  return (max + min) / 2 >= 150 and base + 8 or base
end

-- Rewrites one non-link plugin group so it obeys the theme rules. Returns a
-- list of the changes, or nil when the group is already clean.
local function sanitize_group(name, hl)
  local changes = {}
  local new = { fg = hl.fg, bg = hl.bg, sp = hl.sp, blend = hl.blend, cterm = {} }

  for _, key in ipairs({ "ctermfg", "ctermbg" }) do
    local n = hl[key]
    if n and n > 15 then
      new[key] = M.to_ansi(n)
      table.insert(changes, ("%s %d->%d"):format(key, n, new[key]))
    else
      new[key] = n
    end
  end

  for attr in pairs(hl.cterm or {}) do
    if M.ALLOWED_ATTRS[attr] then
      new.cterm[attr] = true
    else
      table.insert(changes, "cterm " .. attr)
    end
  end

  local ignored = { fg = true, bg = true, sp = true, blend = true, cterm = true, ctermfg = true, ctermbg = true, default = true }
  for attr, value in pairs(hl) do
    if not ignored[attr] then
      if M.ALLOWED_ATTRS[attr] then
        new[attr] = value
      else
        table.insert(changes, "gui " .. attr)
      end
    end
  end

  if #changes == 0 then
    return nil
  end
  vim.api.nvim_set_hl(0, name, new)
  return changes
end

-- Changes that M.load() made to other groups in this session, keyed by
-- group name.
M.sanitized = {}

local loaded_background

-- Sets the theme groups, then cleans every other group, including the
-- groups that plugins create.
function M.load()
  local groups = M.groups()
  for name, spec in pairs(groups) do
    vim.api.nvim_set_hl(0, name, to_hl(spec))
  end
  for name, hl in pairs(vim.api.nvim_get_hl(0, {})) do
    if not hl.link and not M.owns(name, groups) then
      M.sanitized[name] = sanitize_group(name, hl) or M.sanitized[name]
    end
  end
  -- 'background' can change during startup, when OptionSet does not fire,
  -- so lualine would keep the colors of the old background.
  if vim.o.background ~= loaded_background then
    loaded_background = vim.o.background
    if package.loaded.lualine then
      require("lualine").setup()
    end
  end
end

local function load_later()
  vim.schedule(M.load)
end

local group = vim.api.nvim_create_augroup("rko.theme", { clear = true })
vim.api.nvim_create_autocmd("OptionSet", {
  group = group,
  pattern = "background",
  callback = M.load,
})
-- Plugins define or redefine highlights on these events. Load again after
-- their handlers have run.
vim.api.nvim_create_autocmd({ "ColorScheme", "VimEnter" }, { group = group, callback = load_later })
vim.api.nvim_create_autocmd("User", {
  group = group,
  pattern = { "VeryLazy", "LazyLoad" },
  callback = load_later,
})

M.load()

return M
