-- Status line
return {
  "nvim-lualine/lualine.nvim",
  dependencies = {
    "raymond-w-ko/selenized.nvim",
    "nvim-tree/nvim-web-devicons",
  },
  config = function()
    require("lualine").setup({
      options = {
        theme = "auto",
        always_show_tabline = false,
      },
    })
  end,
}
