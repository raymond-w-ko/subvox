-- Fuzzy finder
return {
  "nvim-telescope/telescope.nvim",
  branch = "master",
  dependencies = { "nvim-lua/plenary.nvim" },
  config = function()
    require("telescope").setup({
      defaults = {
        file_ignore_patterns = { "^.git/" },
      },
    })
  end,
  keys = {
    {
      "<C-p>",
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
