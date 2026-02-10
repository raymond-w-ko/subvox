-- Tab line
return {
  "raymond-w-ko/tabs.nvim",
  dev = true,
  dependencies = {
    "nvim-tree/nvim-web-devicons",
    "raymond-w-ko/pixel.nvim",
  },
  event = "VeryLazy",
  opts = {},
  init = function()
    vim.keymap.set("n", "<A-m>", require("tabs").previous)
    vim.keymap.set("n", "<A-,>", require("tabs").next)
    vim.keymap.set("n", "<A-;>", require("tabs").open)
  end,
}
