-- Colorscheme
return {
  "raymond-w-ko/pixel.nvim",
  lazy = false,
  priority = 1000,
  config = function()
    vim.o.termguicolors = false
    vim.cmd.colorscheme("pixel")
    -- vim.o.termguicolors = true
  end,
}
  -- "raymond-w-ko/selenized.nvim",
    -- vim.o.background = "light"
    -- vim.cmd("colorscheme selenized")
