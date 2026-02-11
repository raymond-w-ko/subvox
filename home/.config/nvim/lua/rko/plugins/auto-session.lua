return {
  "rmagatti/auto-session",
  lazy = false,
  dependencies = { "raymond-w-ko/tabs.nvim" },

  ---enables autocomplete for opts
  ---@module "auto-session"
  ---@type AutoSession.Config
  opts = {
    suppressed_dirs = { "~/", "~/Projects", "~/Downloads", "/", "/tmp" },
    -- log_level = 'debug',
    save_extra_data = function()
      return vim.fn.json_encode(require("tabs").get_visited_paths())
    end,
    restore_extra_data = function(_, extra_data)
      require("tabs").restore_visited_order(vim.fn.json_decode(extra_data))
    end,
  },
}
