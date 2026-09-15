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
    settings =
      {
        format = lib.concatStrings [
          "[](blue)"
          "$username"
          "$hostname"
          "[](bg:peach fg:blue)"
          "$directory"
          "[](bg:yellow fg:peach)"
          "$git_branch"
          "$git_status"
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
          "[](bg:lavender fg:green)"
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

        username = {
          show_always = true;
          style_user = "bg:blue fg:crust";
          style_root = "bg:blue fg:crust";
          format = "[ $user]($style)";
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

        git_status = {
          style = "bg:yellow";
          format = "[[($all_status$ahead_behind )](fg:crust bg:yellow)]($style)";
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
