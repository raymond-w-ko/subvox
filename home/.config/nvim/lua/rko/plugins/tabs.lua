-- Tab line
return {
  "raymond-w-ko/tabs.nvim",
  dev = true,
  dependencies = {
    "nvim-tree/nvim-web-devicons",
  },
  event = "VeryLazy",
  opts = {},
  init = function()
    local tabs = require("tabs")
    local keys = {
      ["j"] = tabs.previous,
      ["l"] = tabs.next,
      [";"] = tabs.open,
    }
    for key, fn in pairs(keys) do
      for _, mod in ipairs({ "A", "D" }) do
        vim.keymap.set("n", "<" .. mod .. "-" .. key .. ">", fn)
      end
    end
  end,
}
