-- Status line
return {
  "nvim-lualine/lualine.nvim",
  dependencies = {
    "raymond-w-ko/selenized.nvim",
    "nvim-tree/nvim-web-devicons",
  },
  config = function()
    local C = require("rko.theme").C
    require("lualine").setup({
      options = {
        -- lua/lualine/themes/rko.lua
        theme = "rko",
        always_show_tabline = false,
      },
      sections = {
        -- diff and diagnostics read GUI colors by default, so give them
        -- ANSI colors.
        lualine_b = {
          "branch",
          {
            "diff",
            diff_color = {
              added = { fg = C.light_green },
              modified = { fg = C.light_yellow },
              removed = { fg = C.light_red },
            },
          },
          {
            "diagnostics",
            diagnostics_color = {
              error = { fg = C.light_red },
              warn = { fg = C.light_yellow },
              info = { fg = C.light_cyan },
              hint = { fg = C.light_blue },
            },
          },
        },
      },
    })
  end,
}
