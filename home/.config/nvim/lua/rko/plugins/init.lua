-- Plugin specifications for lazy.nvim
return {
  -- Colorscheme
  {
    "raymond-w-ko/selenized.nvim",
    lazy = false,
    priority = 1000,
    config = function()
      vim.o.background = "light"
      vim.cmd("colorscheme selenized")
    end,
  },

  -- Auto pairs
  {
    "nvim-mini/mini.pairs",
    branch = "main",
    event = "InsertEnter",
    config = function()
      require("mini.pairs").setup()
    end,
  },

  -- Fuzzy finder
  {
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
  },

  -- Motion plugin
  {
    "https://codeberg.org/andyg/leap.nvim.git",
    dependencies = { "tpope/vim-repeat" },
    keys = {
      { "s", "<Plug>(leap)", mode = { "n", "x", "o" }, desc = "Leap forward" },
      { "S", "<Plug>(leap-from-window)", mode = "n", desc = "Leap from window" },
    },
    init = function()
      -- Set up autocmd before plugin loads (for colorscheme changes)
      vim.api.nvim_create_autocmd("ColorScheme", {
        group = vim.api.nvim_create_augroup("LeapColorTweaks", {}),
        callback = function()
          -- Only run if leap is loaded
          local ok, leap = pcall(require, "leap")
          if not ok then return end
          if vim.g.colors_name == "selenized" then
            vim.cmd("hi! LeapLabel guifg=#000000 guibg=#ffff00")
          end
          vim.cmd("hi! link LeapMatch None")
          leap.init_hl()
        end,
      })
    end,
    config = function()
      -- Apply highlights immediately when plugin loads
      if vim.g.colors_name == "selenized" then
        vim.cmd("hi! LeapLabel guifg=#000000 guibg=#ffff00")
      end
      vim.cmd("hi! link LeapMatch None")
      require("leap").init_hl()
    end,
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
