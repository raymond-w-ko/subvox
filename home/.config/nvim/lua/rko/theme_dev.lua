-- Tools to check and tune rko.theme without restarting nvim.
--
--   :ThemePreview  show the palette, grey ramp, tints and important groups
--   :ThemeAudit    list rule violations and groups without a style
--   :ThemeReload   reload lua/rko/theme.lua and re-run plugin highlights
--   :ThemeDev      toggle dev mode for this session:
--                    <F5> reload, <F6> toggle 'background',
--                    reload on save of theme.lua, open the preview
--
-- Headless audit (exit code 1 when there are errors):
--   nvim --headless -c 'lua require("rko.theme_dev").audit_cli()'
local M = {}

local api = vim.api
local ns = api.nvim_create_namespace("rko.theme_dev")
local THEME_FILE = vim.fn.stdpath("config") .. "/lua/rko/theme.lua"
local SAMPLE = " Sample 0123 "

local BASE_NAMES = {
  [0] = "unused", "red", "green", "yellow", "blue", "magenta", "cyan", "unused",
  "grey", "light_red", "light_green", "light_yellow", "light_blue", "light_magenta",
  "light_cyan", "unused",
}
local HUES = { "red", "green", "yellow", "blue", "magenta", "cyan" }

-- Groups that the preview always shows, also when they are undefined.
local SECTIONS = {
  {
    "Editor UI",
    {
      "Normal", "NormalNC", "NormalFloat", "FloatBorder", "FloatTitle", "CursorLine",
      "CursorColumn", "CursorLineNr", "LineNr", "SignColumn", "FoldColumn", "Folded",
      "ColorColumn", "Conceal", "NonText", "Whitespace", "EndOfBuffer", "Visual", "Search",
      "CurSearch", "IncSearch", "Substitute", "MatchParen", "Pmenu", "PmenuSel", "PmenuSbar",
      "PmenuThumb", "PmenuMatch", "PmenuMatchSel", "PmenuKind", "PmenuExtra", "StatusLine",
      "StatusLineNC", "TabLine", "TabLineFill", "TabLineSel", "WinBar", "WinBarNC",
      "WinSeparator", "Title", "Directory", "QuickFixLine", "TermCursor", "MsgArea", "ModeMsg",
      "MoreMsg", "Question", "ErrorMsg", "WarningMsg", "OkMsg", "WildMenu", "SpecialKey",
      "SnippetTabstop", "ComplMatchIns",
    },
  },
  {
    "Syntax",
    {
      "Comment", "Constant", "String", "Character", "Number", "Boolean", "Float",
      "Identifier", "Function", "Statement", "Conditional", "Repeat", "Label", "Operator",
      "Keyword", "Exception", "PreProc", "Include", "Define", "Macro", "PreCondit", "Type",
      "StorageClass", "Structure", "Typedef", "Special", "SpecialChar", "Tag", "Delimiter",
      "SpecialComment", "Debug", "Underlined", "Ignore", "Error", "Todo", "Added", "Changed",
      "Removed",
    },
  },
  {
    "Treesitter",
    {
      "@variable", "@variable.builtin", "@variable.parameter", "@variable.member",
      "@constant", "@constant.builtin", "@module", "@label", "@string", "@string.escape",
      "@string.regexp", "@character", "@number", "@boolean", "@type", "@type.builtin",
      "@attribute", "@property", "@function", "@function.builtin", "@function.call",
      "@function.method", "@constructor", "@operator", "@keyword", "@keyword.return",
      "@punctuation.delimiter", "@punctuation.bracket", "@punctuation.special", "@comment",
      "@comment.todo", "@comment.error", "@comment.warning", "@comment.note", "@tag",
      "@tag.attribute", "@tag.delimiter",
    },
  },
  {
    "Markup and diff",
    {
      "@markup.heading", "@markup.strong", "@markup.italic", "@markup.strikethrough",
      "@markup.underline", "@markup.quote", "@markup.math", "@markup.link",
      "@markup.link.label", "@markup.link.url", "@markup.raw", "@markup.list",
      "@markup.list.checked", "@markup.list.unchecked", "@diff.plus", "@diff.minus",
      "@diff.delta", "DiffAdd", "DiffChange", "DiffDelete", "DiffText", "SpellBad",
      "SpellCap", "SpellLocal", "SpellRare",
    },
  },
  {
    "Diagnostics and LSP",
    {
      "DiagnosticError", "DiagnosticWarn", "DiagnosticInfo", "DiagnosticHint", "DiagnosticOk",
      "DiagnosticUnderlineError", "DiagnosticUnderlineWarn", "DiagnosticUnderlineInfo",
      "DiagnosticUnderlineHint", "DiagnosticUnderlineOk", "DiagnosticVirtualTextError",
      "DiagnosticVirtualTextWarn", "DiagnosticVirtualTextInfo", "DiagnosticVirtualTextHint",
      "DiagnosticDeprecated", "DiagnosticUnnecessary", "LspReferenceText", "LspReferenceRead",
      "LspReferenceWrite", "LspInlayHint", "LspCodeLens", "LspSignatureActiveParameter",
    },
  },
}

-- Plugin groups are listed by prefix, for every group that exists now.
-- DevIcon* is left out because it has hundreds of groups; the audit checks it.
local PLUGIN_PREFIXES = { "GitSigns", "NvimTree", "RenderMarkdown", "Leap", "Tabs", "FFF", "Lazy", "lualine_" }

local function get_hl(name, link)
  return api.nvim_get_hl(0, { name = name, link = link, create = false })
end

-- Returns the defined group that a name resolves to. An undefined
-- "@a.b.c" falls back to "@a.b", then "@a", like nvim does. Returns nil when
-- nothing is defined.
local function defined_ancestor(name, all)
  while name do
    if all[name] then
      return name
    end
    name = name:match("^(@.+)%.[^.]+$")
  end
end

-- Returns the link chain of a group, without the group itself.
local function link_chain(name)
  local chain, seen = {}, { [name] = true }
  local hl = get_hl(name, true)
  while hl.link and not seen[hl.link] do
    table.insert(chain, hl.link)
    seen[hl.link] = true
    hl = get_hl(hl.link, true)
  end
  return chain
end

local function describe(hl)
  local parts = {}
  if hl.ctermfg then
    table.insert(parts, "fg=" .. hl.ctermfg)
  end
  if hl.ctermbg then
    table.insert(parts, "bg=" .. hl.ctermbg)
  end
  for attr in pairs(hl.cterm or {}) do
    table.insert(parts, attr)
  end
  return table.concat(parts, " ")
end

-- Returns the rule violations of one non-link group as { level, msg } items.
-- Only theme groups (`owned`) may use colors above 15.
local function violations(hl, owned)
  local theme = require("rko.theme")
  local out = {}
  for _, key in ipairs({ "ctermfg", "ctermbg" }) do
    local n = hl[key]
    if n and n > 15 and not owned then
      table.insert(out, { "error", ("%s=%d is above 15 in a plugin group"):format(key, n) })
    elseif n and theme.UNRELIABLE[n] then
      table.insert(out, { "warn", ("%s=%d can be the terminal bg in some themes"):format(key, n) })
    end
  end
  if hl.ctermfg and hl.ctermfg == hl.ctermbg then
    table.insert(out, { "warn", "ctermfg equals ctermbg" })
  end
  for attr in pairs(hl.cterm or {}) do
    if not theme.ALLOWED_ATTRS[attr] then
      table.insert(out, { "error", "cterm " .. attr })
    end
  end
  local plain = { fg = true, bg = true, sp = true, blend = true, cterm = true, ctermfg = true, ctermbg = true, default = true }
  for attr in pairs(hl) do
    if not plain[attr] and not theme.ALLOWED_ATTRS[attr] then
      table.insert(out, { "warn", "gui " .. attr })
    end
  end
  if (hl.fg or hl.bg) and not (hl.ctermfg or hl.ctermbg) then
    table.insert(out, { "warn", "GUI color only, no style in the terminal" })
  end
  return out
end

-- Returns the non-link groups of `nvim --clean`, which are the groups that
-- src/nvim/highlight_group.c defines. The result is cached.
local builtin_cache
local function builtin_groups()
  if builtin_cache then
    return builtin_cache
  end
  local code = "io.stdout:write(vim.json.encode(vim.tbl_keys(vim.iter(vim.api.nvim_get_hl(0, {}))"
    .. ":filter(function(_, h) return not h.link end):fold({}, function(acc, k) acc[k] = true return acc end))))"
  local res = vim.system({ vim.v.progpath, "--clean", "--headless", "-c", "lua " .. code, "-c", "qa!" }):wait()
  local ok, names = pcall(vim.json.decode, res.stdout or "")
  builtin_cache = ok and names or {}
  return builtin_cache
end

-- Returns all findings as { level = "error"|"warn"|"info", group, msg } items.
function M.audit()
  local theme = require("rko.theme")
  local findings = {}
  local function add(level, group, msg)
    table.insert(findings, { level = level, group = group, msg = msg })
  end

  if vim.o.termguicolors then
    add("error", "-", "'termguicolors' is on, so the ANSI colors are not used")
  end

  local all = api.nvim_get_hl(0, {})
  local owned = theme.groups()
  for name, hl in pairs(all) do
    if vim.startswith(name, "ThemeDev") then
      -- Swatches of the preview.
    elseif hl.link then
      if not defined_ancestor(hl.link, all) then
        add("warn", name, "links to undefined group " .. hl.link)
      end
    else
      for _, v in ipairs(violations(hl, theme.owns(name, owned))) do
        add(v[1], name, v[2])
      end
    end
  end

  for _, section in ipairs(SECTIONS) do
    for _, name in ipairs(section[2]) do
      local target = defined_ancestor(name, all)
      if not target then
        add("info", name, "undefined")
      elseif describe(get_hl(target, false)) == "" then
        add("info", name, "no terminal style (looks like plain text)")
      end
    end
  end

  for _, name in ipairs(builtin_groups()) do
    if not owned[name] then
      add("info", name, "builtin group not in theme.lua, uses the nvim default: " .. describe(get_hl(name, false)))
    end
  end

  for name, changes in pairs(theme.sanitized) do
    add("info", name, "fixed by sanitize: " .. table.concat(changes, ", "))
  end

  local rank = { error = 1, warn = 2, info = 3 }
  table.sort(findings, function(a, b)
    if a.level ~= b.level then
      return rank[a.level] < rank[b.level]
    end
    return a.group < b.group
  end)
  return findings
end

local function count(findings)
  local n = { error = 0, warn = 0, info = 0 }
  for _, f in ipairs(findings) do
    n[f.level] = n[f.level] + 1
  end
  return n
end

local function format_finding(f)
  return ("%-5s %-40s %s"):format(f.level, f.group, f.msg)
end

function M.audit_cli()
  if vim.v.vim_did_enter == 0 then
    api.nvim_create_autocmd("VimEnter", { once = true, callback = M.audit_cli })
    return
  end
  pcall(vim.cmd, "Lazy! load all")
  -- Plugins load first, then the scheduled sanitize runs, then the audit.
  vim.schedule(function()
    local findings = M.audit()
    for _, f in ipairs(findings) do
      io.stdout:write(format_finding(f), "\n")
    end
    local n = count(findings)
    io.stdout:write(("%d errors, %d warnings, %d info\n"):format(n.error, n.warn, n.info))
    vim.cmd(n.error > 0 and "cquit 1" or "qa!")
  end)
end

local function scratch(name)
  local buf = vim.fn.bufnr(name)
  if buf == -1 then
    buf = api.nvim_create_buf(false, true)
    api.nvim_buf_set_name(buf, name)
    vim.bo[buf].bufhidden = "hide"
  end
  local win = vim.fn.bufwinid(buf)
  if win == -1 then
    vim.cmd("tab sbuffer " .. buf)
  else
    api.nvim_set_current_win(win)
  end
  return buf
end

local function set_lines(buf, lines)
  vim.bo[buf].modifiable = true
  api.nvim_buf_set_lines(buf, 0, -1, false, lines)
  vim.bo[buf].modifiable = false
  vim.bo[buf].modified = false
end

function M.audit_buffer()
  local buf = scratch("theme://audit")
  local findings = M.audit()
  local n = count(findings)
  local lines = { ("%d errors, %d warnings, %d info"):format(n.error, n.warn, n.info), "" }
  for _, f in ipairs(findings) do
    table.insert(lines, format_finding(f))
  end
  set_lines(buf, lines)
  vim.keymap.set("n", "q", "<cmd>close<cr>", { buffer = buf })
end

local preview_buf
-- Line number (0-based) to group name, for gd in the preview.
local preview_groups = {}

local function render_preview()
  local buf = preview_buf
  if not (buf and api.nvim_buf_is_valid(buf)) then
    return
  end
  local lines, marks = {}, {}
  preview_groups = {}
  local function line(text)
    table.insert(lines, text)
    return #lines - 1
  end
  local function mark(lnum, col, len, group)
    table.insert(marks, { lnum, col, col + len, group })
  end

  local findings = M.audit()
  local n = count(findings)
  local title = line(("rko theme   background=%s   termguicolors=%s"):format(vim.o.background, vim.o.termguicolors))
  mark(title, 0, #lines[title + 1], "Title")
  line("r reload   b toggle background   a full audit   gd go to definition   q close")
  line(("Audit: %d errors, %d warnings, %d info"):format(n.error, n.warn, n.info))
  for _, f in ipairs(findings) do
    if f.level ~= "info" then
      local l = line("  " .. format_finding(f))
      mark(l, 0, #lines[l + 1], f.level == "error" and "ErrorMsg" or "WarningMsg")
    end
  end

  line("")
  local theme = require("rko.theme")
  local function swatch(name, spec)
    api.nvim_set_hl(0, name, spec)
    return name
  end

  local l = line("Base palette 0-15 (0, 7 and 15 are unused)")
  mark(l, 0, #lines[l + 1], "Title")
  for i = 0, 15 do
    local prefix = ("  %2d %-14s "):format(i, BASE_NAMES[i])
    l = line(prefix .. "        " .. "  text on default  " .. "bold text")
    mark(l, #prefix, 8, swatch("ThemeDevBg" .. i, { ctermbg = i }))
    mark(l, #prefix + 10, 17, swatch("ThemeDevFg" .. i, { ctermfg = i }))
    mark(l, #prefix + 27, 9, swatch("ThemeDevFgBold" .. i, { ctermfg = i, cterm = { bold = true } }))
  end

  line("")
  l = line("grey(k): k/25 from the bg to the fg")
  mark(l, 0, #lines[l + 1], "Title")
  local labels, cells = "  k ", "    "
  for k = 1, 24 do
    labels = labels .. ("%-3d"):format(k)
    cells = cells .. "   "
  end
  line(labels)
  l = line(cells)
  for k = 1, 24 do
    mark(l, 4 + (k - 1) * 3, 3, swatch("ThemeDevGrey" .. k, { ctermbg = theme.grey(k) }))
  end

  line("")
  l = line("tint(hue, k): the bg mixed toward a hue by k/5")
  mark(l, 0, #lines[l + 1], "Title")
  line("              k=1      k=2      k=3      k=4      k=5")
  for hue, hue_name in ipairs(HUES) do
    local prefix = ("  %d %-9s "):format(hue, hue_name)
    l = line(prefix .. (" Text    "):rep(5))
    for k = 1, 5 do
      local index = theme.tint(hue, k)
      mark(l, #prefix + (k - 1) * 9, 8, swatch(("ThemeDevTint%d_%d"):format(hue, k), { ctermbg = index }))
    end
  end

  local function group_line(name)
    local all = api.nvim_get_hl(0, {})
    local target = defined_ancestor(name, all)
    local exists = target ~= nil
    local info
    if not exists then
      info = "(undefined)"
    elseif target ~= name then
      info = "(inherits " .. target .. ")  " .. describe(get_hl(target, false))
    else
      local chain = link_chain(name)
      info = #chain > 0 and ("-> " .. table.concat(chain, " -> ") .. "  ") or ""
      info = info .. describe(get_hl(name, false))
    end
    local prefix = ("  %-36s "):format(name)
    local gl = line(prefix .. SAMPLE .. "  " .. info)
    mark(gl, #prefix, #SAMPLE, name)
    if not exists then
      mark(gl, #prefix + #SAMPLE + 2, #info, "Comment")
    end
    preview_groups[gl] = name
  end

  for _, section in ipairs(SECTIONS) do
    line("")
    l = line(section[1])
    mark(l, 0, #lines[l + 1], "Title")
    for _, name in ipairs(section[2]) do
      group_line(name)
    end
  end

  local names = vim.tbl_keys(api.nvim_get_hl(0, {}))
  table.sort(names)
  for _, prefix in ipairs(PLUGIN_PREFIXES) do
    local matched = vim.tbl_filter(function(name)
      return vim.startswith(name, prefix)
    end, names)
    if #matched > 0 then
      line("")
      l = line("Plugin: " .. prefix)
      mark(l, 0, #lines[l + 1], "Title")
      for _, name in ipairs(matched) do
        group_line(name)
      end
    end
  end

  set_lines(buf, lines)
  api.nvim_buf_clear_namespace(buf, ns, 0, -1)
  for _, m in ipairs(marks) do
    api.nvim_buf_set_extmark(buf, ns, m[1], m[2], { end_col = m[3], hl_group = m[4] })
  end
end

local function goto_definition()
  local name = preview_groups[api.nvim_win_get_cursor(0)[1] - 1]
  if not name then
    return
  end
  vim.cmd("split " .. vim.fn.fnameescape(THEME_FILE))
  local pattern = ([[\V\(\^\s\*%s =\|["%s"]\)]]):format(name, name)
  if vim.fn.search(pattern, "w") == 0 then
    vim.notify(name .. " is not in theme.lua. It comes from nvim or a plugin.", vim.log.levels.WARN)
  end
end

function M.toggle_background()
  vim.o.background = vim.o.background == "light" and "dark" or "light"
  vim.schedule(render_preview)
end

function M.preview()
  local buf = scratch("theme://preview")
  if preview_buf ~= buf then
    preview_buf = buf
    local function map(lhs, fn)
      vim.keymap.set("n", lhs, fn, { buffer = buf, nowait = true })
    end
    map("r", M.reload)
    map("b", M.toggle_background)
    map("a", M.audit_buffer)
    map("gd", goto_definition)
    map("q", "<cmd>close<cr>")
  end
  vim.wo.wrap = false
  vim.wo.cursorline = true
  render_preview()
end

-- Reloads theme.lua, then fires ColorScheme so plugins re-apply their
-- highlights. A group that you delete from theme.lua keeps its old value
-- until nvim restarts.
function M.reload()
  package.loaded["rko.theme"] = nil
  local ok, err = pcall(require, "rko.theme")
  if not ok then
    vim.notify("theme reload failed: " .. err, vim.log.levels.ERROR)
    return
  end
  vim.cmd("doautocmd <nomodeline> ColorScheme")
  -- Runs after the sanitize that the ColorScheme handler schedules.
  vim.schedule(function()
    render_preview()
    vim.notify("theme reloaded")
  end)
end

local dev_group
function M.dev_toggle()
  if dev_group then
    api.nvim_del_augroup_by_id(dev_group)
    dev_group = nil
    pcall(vim.keymap.del, "n", "<F5>")
    pcall(vim.keymap.del, "n", "<F6>")
    vim.notify("theme dev mode off")
    return
  end
  dev_group = api.nvim_create_augroup("rko.theme_dev", { clear = true })
  api.nvim_create_autocmd("BufWritePost", {
    group = dev_group,
    pattern = { "*/lua/rko/theme.lua", "*/lua/lualine/themes/rko.lua" },
    callback = M.reload,
  })
  vim.keymap.set("n", "<F5>", M.reload, { desc = "Reload theme" })
  vim.keymap.set("n", "<F6>", M.toggle_background, { desc = "Toggle background" })
  M.preview()
  vim.notify("theme dev mode on: <F5> reload, <F6> toggle background, reload on save")
end

function M.setup()
  local cmd = api.nvim_create_user_command
  cmd("ThemePreview", M.preview, { desc = "Preview theme highlight groups" })
  cmd("ThemeAudit", M.audit_buffer, { desc = "Audit highlight groups against theme rules" })
  cmd("ThemeReload", M.reload, { desc = "Reload lua/rko/theme.lua" })
  cmd("ThemeDev", M.dev_toggle, { desc = "Toggle theme dev mode" })
end

return M
