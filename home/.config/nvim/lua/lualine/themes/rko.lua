-- lualine theme that matches rko.theme. lualine loads this file again on
-- ColorScheme and on a 'background' change.
local theme = require("rko.theme")
local C, grey = theme.C, theme.grey

local b = { fg = grey(24), bg = grey(6) }
local c = { fg = grey(18), bg = grey(3) }

local function mode(color)
  return { a = { fg = grey(1), bg = color, gui = "bold" }, b = b, c = c }
end

return {
  normal = mode(C.light_blue),
  insert = mode(C.light_green),
  visual = mode(C.light_magenta),
  replace = mode(C.light_red),
  command = mode(C.light_yellow),
  terminal = mode(C.light_cyan),
  inactive = { a = c, b = c, c = c },
}
