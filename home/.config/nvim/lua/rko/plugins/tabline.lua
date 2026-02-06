-- Tab line
return {
  "raymond-w-ko/nvim-tabline",
  dependencies = { "nvim-tree/nvim-web-devicons" },
  config = function()
    vim.o.showtabline = 2
    require("tabline").setup({})
  end,
}
