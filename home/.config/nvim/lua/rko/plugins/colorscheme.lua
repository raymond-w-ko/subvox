-- Colorscheme
return {
  "raymond-w-ko/selenized.nvim",
  lazy = false,
  priority = 1000,
  config = function()
    vim.o.background = "light"
    vim.cmd("colorscheme selenized")
  end,
}
