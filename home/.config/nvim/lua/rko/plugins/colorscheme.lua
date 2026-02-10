-- Colorscheme
return {
  "raymond-w-ko/pixel.nvim",
  lazy = false,
  priority = 1000,
  config = function()
    vim.cmd.colorscheme("pixel")
  end,
}
  -- "raymond-w-ko/selenized.nvim",
    -- vim.o.background = "light"
    -- vim.cmd("colorscheme selenized")
