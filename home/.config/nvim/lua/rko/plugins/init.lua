-- Plugin specifications for lazy.nvim
return {
  -- Colorscheme
  {
    "raymond-w-ko/selenized.nvim",
    priority = 1000,
    config = function()
      vim.cmd("colorscheme selenized")
    end,
  },

  -- Auto pairs
  {
    "echasnovski/mini.pairs",
    version = false,
    event = "InsertEnter",
    config = function()
      require("mini.pairs").setup()
    end,
  },

  -- Fuzzy finder
  {
    "nvim-telescope/telescope.nvim",
    tag = "0.1.8",
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
  },

  -- Motion plugin
  {
    "https://codeberg.org/andyg/leap.nvim.git",
    dependencies = { "tpope/vim-repeat" },
    keys = {
      { "s", "<Plug>(leap-forward)", mode = { "n", "x", "o" }, desc = "Leap forward" },
      { "S", "<Plug>(leap-backward)", mode = { "n", "x", "o" }, desc = "Leap backward" },
      { "gs", "<Plug>(leap-from-window)", mode = "n", desc = "Leap from window" },
    },
  },

  -- Status line
  {
    "nvim-lualine/lualine.nvim",
    dependencies = {
      "raymond-w-ko/selenized.nvim",
      "nvim-tree/nvim-web-devicons",
    },
    config = function()
      require("lualine").setup({
        options = {
          theme = "selenized",
        },
      })
    end,
  },
}
