-- Fuzzy finder
return {
  "nvim-telescope/telescope.nvim",
  branch = "master",
  dependencies = { "nvim-lua/plenary.nvim" },
  config = function()
    local actions = require("telescope.actions")
    require("telescope").setup({
      defaults = {
        path_display = { truncate = 3 },
        file_ignore_patterns = { "^.git/" },
        mappings = {
          i = {
            ["<space>"] = actions.to_fuzzy_refine,
          },
          n = {
            ["<space>"] = actions.to_fuzzy_refine,
          },
        },
      },
    })
  end,
  keys = {
    {
      "<leader>f",
      function()
        require("telescope.builtin").find_files({ hidden = true })
      end,
      desc = "Find files",
    },
    {
      "<leader>/",
      function()
        require("telescope.builtin").live_grep({ additional_args = { "--hidden" } })
      end,
      desc = "Live grep",
    },
  },
}
