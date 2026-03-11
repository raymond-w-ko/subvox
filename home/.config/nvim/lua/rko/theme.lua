-- generated from src/nvim/highlight_group.c
local CTERM = {
  black = 0,
  dark_red = 1,
  dark_green = 2,
  dark_yellow = 3,
  dark_blue = 4,
  dark_magenta = 5,
  dark_cyan = 6,
  light_grey = 7,
  dark_grey = 8,
  light_red = 9,
  light_green = 10,
  light_yellow = 11,
  light_blue = 12,
  light_magenta = 13,
  light_cyan = 14,
  white = 15,
}

local function ctermfg(color)
  return "ctermfg=" .. color
end

local function ctermbg(color)
  return "ctermbg=" .. color
end

local function set(group, spec)
  vim.api.nvim_set_hl(0, group, {})
  vim.cmd(("highlight %s %s"):format(group, table.concat(spec, " ")))
end

local both = {
  { "Cursor", { "guifg=bg", "guibg=fg", "ctermfg=NONE" } },
  { "CursorLineNr", { "gui=bold", "cterm=bold" } },
  { "PmenuMatch", { "gui=bold", "cterm=bold" } },
  { "PmenuMatchSel", { "gui=bold", "cterm=bold" } },
  { "PmenuSel", { "gui=reverse" } },
  { "RedrawDebugNormal", { "gui=reverse" } },
  { "TabLineSel", { "gui=bold", "cterm=bold" } },
  { "TermCursor", { "gui=reverse" } },
  { "Underlined", { "gui=underline" } },
  { "lCursor", { "guifg=bg", "guibg=fg", "ctermfg=NONE" } },
  { "@markup.strong", { "gui=bold", "cterm=bold" } },
  { "@markup.italic", { "gui=italic", "cterm=italic" } },
  { "@markup.strikethrough", { "gui=strikethrough" } },
  { "@markup.underline", { "gui=underline" } },
  { "@markup.heading.1.delimiter.vimdoc", { "guifg=bg", "guibg=bg", "guisp=fg", "gui=underdouble,nocombine", "ctermfg=NONE" } },
  { "@markup.heading.2.delimiter.vimdoc", { "guifg=bg", "guibg=bg", "guisp=fg", "gui=underline,nocombine", "ctermfg=NONE" } },
}

local light = {
  { "Normal", { "guifg=NvimDarkGrey2", "guibg=NvimLightGrey2", ctermfg(CTERM.black) } },
  { "Added", { "guifg=NvimDarkGreen", ctermfg(CTERM.dark_green) } },
  { "Changed", { "guifg=NvimDarkCyan", ctermfg(CTERM.dark_cyan) } },
  { "ColorColumn", { "guibg=NvimLightGrey4" } },
  { "Conceal", { "guifg=NvimLightGrey4", ctermfg(CTERM.dark_grey) } },
  { "CurSearch", { "guifg=NvimLightGrey1", "guibg=NvimDarkYellow", ctermfg(CTERM.white), ctermbg(CTERM.dark_yellow) } },
  { "CursorColumn", { "guibg=NvimLightGrey3" } },
  { "CursorLine", { "guibg=NvimLightGrey3" } },
  { "DiffAdd", { "guifg=NvimDarkGrey1", "guibg=NvimLightGreen", ctermfg(CTERM.black), ctermbg(CTERM.light_green) } },
  { "DiffChange", { "guifg=NvimDarkGrey1", "guibg=NvimLightGrey4", ctermfg(CTERM.dark_grey) } },
  { "DiffDelete", { "guifg=NvimDarkRed", "gui=bold", ctermfg(CTERM.dark_red), "cterm=bold" } },
  { "DiffText", { "guifg=NvimDarkGrey1", "guibg=NvimLightCyan", ctermfg(CTERM.black), ctermbg(CTERM.light_cyan) } },
  { "Directory", { "guifg=NvimDarkCyan", ctermfg(CTERM.dark_cyan) } },
  { "ErrorMsg", { "guifg=NvimDarkRed", ctermfg(CTERM.dark_red) } },
  { "FloatShadow", { "guibg=NvimLightGrey4" } },
  { "FloatShadowThrough", { "guibg=NvimLightGrey4" } },
  { "Folded", { "guifg=NvimDarkGrey4", "guibg=NvimLightGrey1", ctermfg(CTERM.dark_grey) } },
  { "LineNr", { "guifg=NvimLightGrey4", ctermfg(CTERM.dark_grey) } },
  { "MatchParen", { "guibg=NvimLightGrey4", "gui=bold", ctermfg(CTERM.black), ctermbg(CTERM.light_magenta), "cterm=bold" } },
  { "ModeMsg", { "guifg=NvimDarkGreen", ctermfg(CTERM.dark_green) } },
  { "MoreMsg", { "guifg=NvimDarkCyan", ctermfg(CTERM.dark_cyan) } },
  { "NonText", { "guifg=NvimLightGrey4", ctermfg(CTERM.dark_grey) } },
  { "NormalFloat", { "guibg=NvimLightGrey1" } },
  { "OkMsg", { "guifg=NvimDarkGreen", ctermfg(CTERM.dark_green) } },
  { "PmenuSel", { "gui=reverse", ctermfg(CTERM.black), ctermbg(CTERM.light_blue) } },
  { "Pmenu", { "guibg=NvimLightGrey3" } },
  { "PmenuThumb", { "guibg=NvimLightGrey4" } },
  { "Question", { "guifg=NvimDarkCyan", ctermfg(CTERM.dark_cyan) } },
  { "QuickFixLine", { "guifg=NvimDarkCyan", ctermfg(CTERM.dark_cyan) } },
  { "RedrawDebugClear", { "guibg=NvimLightYellow", ctermfg(CTERM.black), ctermbg(CTERM.light_yellow) } },
  { "RedrawDebugComposed", { "guibg=NvimLightGreen", ctermfg(CTERM.black), ctermbg(CTERM.light_green) } },
  { "RedrawDebugRecompose", { "guibg=NvimLightRed", ctermfg(CTERM.black), ctermbg(CTERM.light_red) } },
  { "Removed", { "guifg=NvimDarkRed", ctermfg(CTERM.dark_red) } },
  { "Search", { "guifg=NvimDarkGrey1", "guibg=NvimLightYellow", ctermfg(CTERM.black), ctermbg(CTERM.light_yellow) } },
  { "SignColumn", { "guifg=NvimLightGrey4", ctermfg(CTERM.dark_grey) } },
  { "SpellBad", { "guisp=NvimDarkRed", "gui=undercurl" } },
  { "SpellCap", { "guisp=NvimDarkYellow", "gui=undercurl" } },
  { "SpellLocal", { "guisp=NvimDarkGreen", "gui=undercurl" } },
  { "SpellRare", { "guisp=NvimDarkCyan", "gui=undercurl" } },
  { "StatusLine", { "guifg=NvimDarkGrey2", "guibg=NvimLightGrey4", ctermfg(CTERM.black) } },
  { "StatusLineNC", { "guifg=NvimDarkGrey3", "guibg=NvimLightGrey3", ctermfg(CTERM.dark_grey) } },
  { "Title", { "guifg=NvimDarkGrey2", "gui=bold", ctermfg(CTERM.black), "cterm=bold" } },
  { "Visual", { "guibg=NvimLightGrey4", ctermfg(CTERM.black), ctermbg(CTERM.dark_grey) } },
  { "WarningMsg", { "guifg=NvimDarkYellow", ctermfg(CTERM.dark_yellow) } },
  { "WinBar", { "guifg=NvimDarkGrey4", "guibg=NvimLightGrey1", "gui=bold", ctermfg(CTERM.dark_grey), "cterm=bold" } },
  { "WinBarNC", { "guifg=NvimDarkGrey4", "guibg=NvimLightGrey1", ctermfg(CTERM.dark_grey) } },
  { "Constant", { "guifg=NvimDarkGrey2", ctermfg(CTERM.black) } },
  { "Operator", { "guifg=NvimDarkGrey2", ctermfg(CTERM.black) } },
  { "PreProc", { "guifg=NvimDarkGrey2", ctermfg(CTERM.black) } },
  { "Type", { "guifg=NvimDarkGrey2", ctermfg(CTERM.black) } },
  { "Delimiter", { "guifg=NvimDarkGrey2", ctermfg(CTERM.black) } },
  { "Comment", { "guifg=NvimDarkGrey4", ctermfg(CTERM.dark_grey) } },
  { "String", { "guifg=NvimDarkGreen", ctermfg(CTERM.dark_green) } },
  { "Identifier", { "guifg=NvimDarkBlue", ctermfg(CTERM.dark_blue) } },
  { "Function", { "guifg=NvimDarkCyan", ctermfg(CTERM.dark_cyan) } },
  { "Statement", { "guifg=NvimDarkGrey2", "gui=bold", ctermfg(CTERM.black), "cterm=bold" } },
  { "Special", { "guifg=NvimDarkCyan", ctermfg(CTERM.dark_cyan) } },
  { "Error", { "guifg=NvimDarkGrey1", "guibg=NvimLightRed", ctermfg(CTERM.black), ctermbg(CTERM.light_red) } },
  { "Todo", { "guifg=NvimDarkGrey2", "gui=bold", ctermfg(CTERM.black), "cterm=bold" } },
  { "DiagnosticError", { "guifg=NvimDarkRed", ctermfg(CTERM.dark_red) } },
  { "DiagnosticWarn", { "guifg=NvimDarkYellow", ctermfg(CTERM.dark_yellow) } },
  { "DiagnosticInfo", { "guifg=NvimDarkCyan", ctermfg(CTERM.dark_cyan) } },
  { "DiagnosticHint", { "guifg=NvimDarkBlue", ctermfg(CTERM.dark_blue) } },
  { "DiagnosticOk", { "guifg=NvimDarkGreen", ctermfg(CTERM.dark_green) } },
  { "DiagnosticUnderlineError", { "guisp=NvimDarkRed", "gui=underline" } },
  { "DiagnosticUnderlineWarn", { "guisp=NvimDarkYellow", "gui=underline" } },
  { "DiagnosticUnderlineInfo", { "guisp=NvimDarkCyan", "gui=underline" } },
  { "DiagnosticUnderlineHint", { "guisp=NvimDarkBlue", "gui=underline" } },
  { "DiagnosticUnderlineOk", { "guisp=NvimDarkGreen", "gui=underline" } },
  { "DiagnosticDeprecated", { "guisp=NvimDarkRed", "gui=strikethrough" } },
  { "@variable", { "guifg=NvimDarkGrey2", ctermfg(CTERM.black) } },
}

local dark = {
  { "Normal", { "guifg=NvimLightGrey2", "guibg=NvimDarkGrey2", ctermfg(CTERM.light_grey) } },
  { "Added", { "guifg=NvimLightGreen", ctermfg(CTERM.light_green) } },
  { "Changed", { "guifg=NvimLightCyan", ctermfg(CTERM.light_cyan) } },
  { "ColorColumn", { "guibg=NvimDarkGrey4" } },
  { "Conceal", { "guifg=NvimDarkGrey4", ctermfg(CTERM.dark_grey) } },
  { "CurSearch", { "guifg=NvimDarkGrey1", "guibg=NvimLightYellow", ctermfg(CTERM.black), ctermbg(CTERM.light_yellow) } },
  { "CursorColumn", { "guibg=NvimDarkGrey3" } },
  { "CursorLine", { "guibg=NvimDarkGrey3" } },
  { "DiffAdd", { "guifg=NvimLightGrey1", "guibg=NvimDarkGreen", ctermfg(CTERM.white), ctermbg(CTERM.dark_green) } },
  { "DiffChange", { "guifg=NvimLightGrey1", "guibg=NvimDarkGrey4", ctermfg(CTERM.dark_grey) } },
  { "DiffDelete", { "guifg=NvimLightRed", "gui=bold", ctermfg(CTERM.light_red), "cterm=bold" } },
  { "DiffText", { "guifg=NvimLightGrey1", "guibg=NvimDarkCyan", ctermfg(CTERM.white), ctermbg(CTERM.dark_cyan) } },
  { "Directory", { "guifg=NvimLightCyan", ctermfg(CTERM.light_cyan) } },
  { "ErrorMsg", { "guifg=NvimLightRed", ctermfg(CTERM.light_red) } },
  { "FloatShadow", { "guibg=NvimDarkGrey4" } },
  { "FloatShadowThrough", { "guibg=NvimDarkGrey4" } },
  { "Folded", { "guifg=NvimLightGrey4", "guibg=NvimDarkGrey1", ctermfg(CTERM.dark_grey) } },
  { "LineNr", { "guifg=NvimDarkGrey4", ctermfg(CTERM.dark_grey) } },
  { "MatchParen", { "guibg=NvimDarkGrey4", "gui=bold", ctermfg(CTERM.white), ctermbg(CTERM.dark_magenta), "cterm=bold" } },
  { "ModeMsg", { "guifg=NvimLightGreen", ctermfg(CTERM.light_green) } },
  { "MoreMsg", { "guifg=NvimLightCyan", ctermfg(CTERM.light_cyan) } },
  { "NonText", { "guifg=NvimDarkGrey4", ctermfg(CTERM.dark_grey) } },
  { "NormalFloat", { "guibg=NvimDarkGrey1" } },
  { "OkMsg", { "guifg=NvimLightGreen", ctermfg(CTERM.light_green) } },
  { "PmenuSel", { "gui=reverse", ctermfg(CTERM.white), ctermbg(CTERM.dark_blue) } },
  { "Pmenu", { "guibg=NvimDarkGrey3" } },
  { "PmenuThumb", { "guibg=NvimDarkGrey4" } },
  { "Question", { "guifg=NvimLightCyan", ctermfg(CTERM.light_cyan) } },
  { "QuickFixLine", { "guifg=NvimLightCyan", ctermfg(CTERM.light_cyan) } },
  { "RedrawDebugClear", { "guibg=NvimDarkYellow", ctermfg(CTERM.white), ctermbg(CTERM.dark_yellow) } },
  { "RedrawDebugComposed", { "guibg=NvimDarkGreen", ctermfg(CTERM.white), ctermbg(CTERM.dark_green) } },
  { "RedrawDebugRecompose", { "guibg=NvimDarkRed", ctermfg(CTERM.white), ctermbg(CTERM.dark_red) } },
  { "Removed", { "guifg=NvimLightRed", ctermfg(CTERM.light_red) } },
  { "Search", { "guifg=NvimLightGrey1", "guibg=NvimDarkYellow", ctermfg(CTERM.dark_yellow), ctermbg(CTERM.black) } },
  { "SignColumn", { "guifg=NvimDarkGrey4", ctermfg(CTERM.dark_grey) } },
  { "SpellBad", { "guisp=NvimLightRed", "gui=undercurl" } },
  { "SpellCap", { "guisp=NvimLightYellow", "gui=undercurl" } },
  { "SpellLocal", { "guisp=NvimLightGreen", "gui=undercurl" } },
  { "SpellRare", { "guisp=NvimLightCyan", "gui=undercurl" } },
  { "StatusLine", { "guifg=NvimLightGrey2", "guibg=NvimDarkGrey4", ctermfg(CTERM.light_grey) } },
  { "StatusLineNC", { "guifg=NvimLightGrey3", "guibg=NvimDarkGrey3", ctermfg(CTERM.light_grey) } },
  { "Title", { "guifg=NvimLightGrey2", "gui=bold", ctermfg(CTERM.light_grey), "cterm=bold" } },
  { "Visual", { "guibg=NvimDarkGrey4", ctermfg(CTERM.white), ctermbg(CTERM.dark_grey) } },
  { "WarningMsg", { "guifg=NvimLightYellow", ctermfg(CTERM.light_yellow) } },
  { "WinBar", { "guifg=NvimLightGrey4", "guibg=NvimDarkGrey1", "gui=bold", ctermfg(CTERM.dark_grey), "cterm=bold" } },
  { "WinBarNC", { "guifg=NvimLightGrey4", "guibg=NvimDarkGrey1", ctermfg(CTERM.dark_grey) } },
  { "Constant", { "guifg=NvimLightGrey2", ctermfg(CTERM.light_grey) } },
  { "Operator", { "guifg=NvimLightGrey2", ctermfg(CTERM.light_grey) } },
  { "PreProc", { "guifg=NvimLightGrey2", ctermfg(CTERM.light_grey) } },
  { "Type", { "guifg=NvimLightGrey2", ctermfg(CTERM.light_grey) } },
  { "Delimiter", { "guifg=NvimLightGrey2", ctermfg(CTERM.light_grey) } },
  { "Comment", { "guifg=NvimLightGrey4", ctermfg(CTERM.dark_grey) } },
  { "String", { "guifg=NvimLightGreen", ctermfg(CTERM.dark_green) } },
  { "Identifier", { "guifg=NvimLightBlue", ctermfg(CTERM.light_blue) } },
  { "Function", { "guifg=NvimLightCyan", ctermfg(CTERM.light_cyan) } },
  { "Statement", { "guifg=NvimLightGrey2", "gui=bold", ctermfg(CTERM.light_grey), "cterm=bold" } },
  { "Special", { "guifg=NvimLightCyan", ctermfg(CTERM.light_cyan) } },
  { "Error", { "guifg=NvimLightGrey1", "guibg=NvimDarkRed", ctermfg(CTERM.white), ctermbg(CTERM.dark_red) } },
  { "Todo", { "guifg=NvimLightGrey2", "gui=bold", ctermfg(CTERM.light_grey), "cterm=bold" } },
  { "DiagnosticError", { "guifg=NvimLightRed", ctermfg(CTERM.light_red) } },
  { "DiagnosticWarn", { "guifg=NvimLightYellow", ctermfg(CTERM.light_yellow) } },
  { "DiagnosticInfo", { "guifg=NvimLightCyan", ctermfg(CTERM.light_cyan) } },
  { "DiagnosticHint", { "guifg=NvimLightBlue", ctermfg(CTERM.light_blue) } },
  { "DiagnosticOk", { "guifg=NvimLightGreen", ctermfg(CTERM.light_green) } },
  { "DiagnosticUnderlineError", { "guisp=NvimLightRed", "gui=underline" } },
  { "DiagnosticUnderlineWarn", { "guisp=NvimLightYellow", "gui=underline" } },
  { "DiagnosticUnderlineInfo", { "guisp=NvimLightCyan", "gui=underline" } },
  { "DiagnosticUnderlineHint", { "guisp=NvimLightBlue", "gui=underline" } },
  { "DiagnosticUnderlineOk", { "guisp=NvimLightGreen", "gui=underline" } },
  { "DiagnosticDeprecated", { "guisp=NvimLightRed", "gui=strikethrough" } },
  { "@variable", { "guifg=NvimLightGrey2", ctermfg(CTERM.light_grey) } },
}

local cmdline = {
  { "NvimInternalError", { "guifg=Red", "guibg=Red", ctermfg(CTERM.white), ctermbg(CTERM.dark_red) } },
}

local function apply(list)
  for _, item in ipairs(list) do
    set(item[1], item[2])
  end
end

local function load()
  apply(both)
  apply(vim.o.background == "light" and light or dark)
  apply(cmdline)
end

load()

return { load = load }
