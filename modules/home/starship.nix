{ lib, ... }:
let
  languageModules = [
    "c"
    "cpp"
    "rust"
    "golang"
    "nodejs"
    "php"
    "java"
    "kotlin"
    "haskell"
    "python"
  ];

  languageSymbols = {
    c = "";
    cpp = "";
    rust = "";
    golang = "";
    nodejs = "";
    php = "";
    java = "";
    kotlin = "";
    haskell = "";
    python = "";
  };
in
{
  programs.starship = {
    enable = true;
    enableFishIntegration = true;
    enableBashIntegration = true;
    settings = {
      format = lib.concatStrings [
        "[](blue)"
        "$os"
        "$username"
        "$hostname"
        "[](bg:peach fg:blue)"
        "$directory"
        "[](bg:yellow fg:peach)"
        "$git_branch"
        "$git_commit"
        "$git_state"
        "$git_status"
        "$git_metrics"
        "[](bg:green fg:yellow)"
        "$c"
        "$cpp"
        "$rust"
        "$golang"
        "$nodejs"
        "$php"
        "$java"
        "$kotlin"
        "$haskell"
        "$python"
        "$nix_shell"
        "$direnv"
        "[](bg:lavender fg:green)"
        "$cmd_duration"
        "$jobs"
        "$status"
        "$time"
        "[ ](fg:lavender)"
        "$line_break"
        "$character"
      ];

      palette = "catppuccin_mocha";

      palettes.catppuccin_mocha = {
        rosewater = "#f5e0dc";
        flamingo = "#f2cdcd";
        pink = "#f5c2e7";
        mauve = "#cba6f7";
        red = "#f38ba8";
        maroon = "#eba0ac";
        peach = "#fab387";
        yellow = "#f9e2af";
        green = "#a6e3a1";
        teal = "#94e2d5";
        sky = "#89dceb";
        sapphire = "#74c7ec";
        blue = "#89b4fa";
        lavender = "#b4befe";
        text = "#cdd6f4";
        subtext1 = "#bac2de";
        subtext0 = "#a6adc8";
        overlay2 = "#9399b2";
        overlay1 = "#7f849c";
        overlay0 = "#6c7086";
        surface2 = "#585b70";
        surface1 = "#45475a";
        surface0 = "#313244";
        base = "#1e1e2e";
        mantle = "#181825";
        crust = "#11111b";
      };

      os = {
        disabled = false;
        style = "bg:blue fg:crust";
        format = "[ $symbol]($style)";
        symbols = {
          NixOS = "";
          Macos = "";
          Linux = "";
          Ubuntu = "";
          Debian = "";
          Arch = "";
          Windows = "";
        };
      };

      username = {
        show_always = true;
        style_user = "bg:blue fg:crust";
        style_root = "bg:blue fg:crust";
        format = "[$user]($style)";
      };

      hostname = {
        ssh_only = false;
        style = "bg:blue fg:crust";
        format = "[@$hostname ]($style)";
      };

      directory = {
        style = "bg:peach fg:crust";
        format = "[ $path ]($style)";
        truncation_length = 3;
        truncation_symbol = "…/";
        substitutions = {
          Documents = "󰈙 ";
          Downloads = "󰉍 ";
          Music = "󰝚 ";
          Pictures = "󰉏 ";
          Developer = "󰲋 ";
        };
      };

      git_branch = {
        symbol = "";
        style = "bg:yellow";
        format = "[[ $symbol $branch ](fg:crust bg:yellow)]($style)";
      };

      git_commit = {
        disabled = false;
        only_detached = true;
        tag_disabled = false;
        tag_symbol = " ";
        style = "bg:yellow";
        format = "[[ $hash$tag ](fg:crust bg:yellow)]($style)";
      };

      git_state = {
        disabled = false;
        style = "bg:yellow";
        format = "[[ $state( $progress_current/$progress_total) ](fg:crust bg:yellow)]($style)";
        rebase = "REBASING";
        merge = "MERGING";
        revert = "REVERTING";
        cherry_pick = "PICKING";
        bisect = "BISECTING";
        am = "AM";
        am_or_rebase = "AM/REBASE";
      };

      git_status = {
        style = "bg:yellow";
        format = "[[($all_status$ahead_behind )](fg:crust bg:yellow)]($style)";
      };

      git_metrics = {
        disabled = false;
        only_nonzero_diffs = true;
        added_style = "fg:crust bg:yellow";
        deleted_style = "fg:crust bg:yellow";
        format = "([([+$added]($added_style))([-$deleted]($deleted_style)) ](bg:yellow))";
      };

      nix_shell = {
        disabled = false;
        symbol = " ";
        style = "bg:green";
        format = "[[ $symbol$state( \\($name\\)) ](fg:crust bg:green)]($style)";
        impure_msg = "impure";
        pure_msg = "pure";
        unknown_msg = "shell";
      };

      direnv = {
        disabled = false;
        symbol = " ";
        style = "bg:green";
        format = "[[ $symbol$loaded/$allowed ](fg:crust bg:green)]($style)";
        allowed_msg = "ok";
        not_allowed_msg = "denied";
        denied_msg = "denied";
        loaded_msg = "on";
        unloaded_msg = "off";
      };

      cmd_duration = {
        min_time = 2000;
        show_milliseconds = false;
        style = "bg:lavender";
        format = "[[ 󰔛 $duration ](fg:crust bg:lavender)]($style)";
      };

      jobs = {
        symbol = "";
        number_threshold = 1;
        symbol_threshold = 1;
        style = "bg:lavender";
        format = "[[ $symbol $number ](fg:crust bg:lavender)]($style)";
      };

      status = {
        disabled = false;
        symbol = "";
        success_symbol = "";
        not_executable_symbol = "";
        not_found_symbol = "";
        sigint_symbol = "";
        signal_symbol = "";
        map_symbol = true;
        pipestatus = false;
        style = "bg:lavender";
        format = "[[ $symbol $status ](fg:crust bg:lavender)]($style)";
      };

      time = {
        disabled = false;
        time_format = "%R";
        style = "bg:lavender";
        format = "[[  $time ](fg:crust bg:lavender)]($style)";
      };

      line_break.disabled = false;

      character = {
        disabled = false;
        success_symbol = "[❯](bold fg:green)";
        error_symbol = "[❯](bold fg:red)";
        vimcmd_symbol = "[❯](bold fg:green)";
        vimcmd_replace_one_symbol = "[❯](bold fg:lavender)";
        vimcmd_replace_symbol = "[❯](bold fg:lavender)";
        vimcmd_visual_symbol = "[❯](bold fg:yellow)";
      };
    }
    // lib.genAttrs languageModules (name: {
      style = "bg:green";
      symbol = builtins.getAttr name languageSymbols;
      disabled = false;
      format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
    });
  };
}
