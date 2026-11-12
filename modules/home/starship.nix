{
  config,
  lib,
  osConfig,
  ...
}:
let
  hostName = config.subvox.starship.hostName;
  # Hash only at Nix evaluation time. Map to HSV with 50% saturation and
  # 95% value (RGB channels 121..242), so every hue supports dark text.
  hash = builtins.hashString "sha256" hostName;
  hue = lib.mod (lib.fromHexString (builtins.substring 0 8 hash)) 360;
  sector = builtins.div hue 60;
  offset = lib.mod hue 60;
  rising = 121 + builtins.div (121 * offset) 60;
  falling = 242 - builtins.div (121 * offset) 60;
  rgb = builtins.elemAt [
    [
      242
      rising
      121
    ]
    [
      falling
      242
      121
    ]
    [
      121
      242
      rising
    ]
    [
      121
      falling
      242
    ]
    [
      rising
      121
      242
    ]
    [
      242
      121
      falling
    ]
  ] sector;
  hostColor =
    if hostName == null then
      "red"
    else
      "#${lib.concatMapStrings (channel: lib.toLower (lib.toHexString channel)) rgb}";
  # Do not use palette.crust here: light palettes define it as a light colour.
  hostForeground = if hostName == null then "crust" else "#171b24";
  hostStyle = "bg:${hostColor} fg:${hostForeground}";
in
{
  options.subvox.starship.hostName = lib.mkOption {
    type = lib.types.nullOr lib.types.nonEmptyStr;
    default = osConfig.networking.hostName or null;
    defaultText = lib.literalExpression "osConfig.networking.hostName or null";
    example = "nixvac";
    description = ''
      Hostname used to derive the first prompt block's colour at build time.
      Defaults to the system configuration's hostname. Set this explicitly
      for standalone Home Manager or systems without a declared hostname.
      Null keeps the palette's red colour. Starship always displays the
      runtime hostname; no extra command runs to compute its colour.
    '';
  };

  config.programs.starship = {
    enable = true;
    enableFishIntegration = true;
    enableBashIntegration = true;
    # Catppuccin Powerline: https://starship.rs/presets/catppuccin-powerline
    settings = {
      "$schema" = "https://starship.rs/config-schema.json";
      format = lib.concatStrings [
        "[](${hostColor})"
        "$os"
        "$username"
        "$hostname"
        "[](bg:peach fg:${hostColor})"
        "$directory"
        "[](bg:yellow fg:peach)"
        "$git_branch"
        "$git_status"
        "[](fg:yellow bg:green)"
        "$c"
        "$rust"
        "$golang"
        "$nodejs"
        "$bun"
        "$php"
        "$java"
        "$kotlin"
        "$haskell"
        "$python"
        "[](fg:green bg:sapphire)"
        "$conda"
        "[](fg:sapphire bg:lavender)"
        "$time"
        "[ ](fg:lavender)"
        "$cmd_duration"
        "$line_break"
        "$character"
      ];
      # Switch to any palette defined below: Catppuccin or Ayu.
      palette = "ayu_mirage";
      os = {
        disabled = false;
        style = hostStyle;
        symbols = {
          Windows = " ";
          Ubuntu = "󰕈 ";
          SUSE = " ";
          Raspbian = "󰐿 ";
          Mint = "󰣭 ";
          Macos = "󰀵 ";
          Manjaro = " ";
          Linux = "󰌽 ";
          Gentoo = "󰣨 ";
          Fedora = "󰣛 ";
          Alpine = " ";
          Amazon = " ";
          Android = " ";
          AOSC = " ";
          Arch = "󰣇 ";
          Artix = "󰣇 ";
          CachyOS = " ";
          CentOS = " ";
          Debian = "󰣚 ";
          Redhat = "󱄛 ";
          RedHatEnterprise = "󱄛 ";
          Void = " ";
        };
      };
      username = {
        show_always = true;
        style_user = hostStyle;
        style_root = hostStyle;
        format = "[$user]($style)";
      };
      hostname = {
        ssh_only = false;
        ssh_symbol = "";
        format = "[@$hostname ]($style)";
        style = hostStyle;
      };
      directory = {
        style = "bg:peach fg:crust";
        format = "[ $path ]($style)";
        truncation_length = 3;
        truncation_symbol = "…/";
        substitutions = {
          Documents = "󰈙 ";
          Downloads = " ";
          Music = "󰝚 ";
          Pictures = " ";
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
      nodejs = {
        symbol = "";
        style = "bg:green";
        format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
      };
      bun = {
        symbol = "";
        style = "bg:green";
        format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
      };
      c = {
        symbol = " ";
        style = "bg:green";
        format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
      };
      rust = {
        symbol = "";
        style = "bg:green";
        format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
      };
      golang = {
        symbol = "";
        style = "bg:green";
        format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
      };
      php = {
        symbol = "";
        style = "bg:green";
        format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
      };
      java = {
        symbol = " ";
        style = "bg:green";
        format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
      };
      jj_bookmark = {
        symbol = "";
        style = "bg:yellow";
        format = "[[ $symbol $bookmark(@$remote)$diverged( \\\\(+$overflow_count others\\\\)) ](fg:crust bg:yellow)]($style)";
      };
      jj_status = {
        style = "bg:yellow";
        format = "[[($all )](fg:crust bg:yellow)]($style)";
      };
      kotlin = {
        symbol = "";
        style = "bg:green";
        format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
      };
      haskell = {
        symbol = "";
        style = "bg:green";
        format = "[[ $symbol( $version) ](fg:crust bg:green)]($style)";
      };
      python = {
        symbol = "";
        style = "bg:green";
        format = "[[ $symbol( $version)(\\(#$virtualenv\\)) ](fg:crust bg:green)]($style)";
      };
      docker_context = {
        symbol = "";
        style = "bg:sapphire";
        format = "[[ $symbol( $context) ](fg:crust bg:sapphire)]($style)";
      };
      conda = {
        symbol = "  ";
        style = "fg:crust bg:sapphire";
        format = "[$symbol$environment ]($style)";
        ignore_base = false;
      };
      time = {
        disabled = false;
        time_format = "%R";
        style = "bg:lavender";
        format = "[[  $time ](fg:crust bg:lavender)]($style)";
      };
      line_break = {
        disabled = true;
      };
      character = {
        disabled = false;
        success_symbol = "[❯](bold fg:green)";
        error_symbol = "[❯](bold fg:red)";
        vimcmd_symbol = "[❮](bold fg:green)";
        vimcmd_replace_one_symbol = "[❮](bold fg:lavender)";
        vimcmd_replace_symbol = "[❮](bold fg:lavender)";
        vimcmd_visual_symbol = "[❮](bold fg:yellow)";
      };
      cmd_duration = {
        show_milliseconds = true;
        format = " in $duration ";
        style = "bg:lavender";
        disabled = false;
        show_notifications = true;
        min_time_to_notify = 45000;
      };
      palettes = {
        catppuccin_mocha = {
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
        catppuccin_frappe = {
          rosewater = "#f2d5cf";
          flamingo = "#eebebe";
          pink = "#f4b8e4";
          mauve = "#ca9ee6";
          red = "#e78284";
          maroon = "#ea999c";
          peach = "#ef9f76";
          yellow = "#e5c890";
          green = "#a6d189";
          teal = "#81c8be";
          sky = "#99d1db";
          sapphire = "#85c1dc";
          blue = "#8caaee";
          lavender = "#babbf1";
          text = "#c6d0f5";
          subtext1 = "#b5bfe2";
          subtext0 = "#a5adce";
          overlay2 = "#949cbb";
          overlay1 = "#838ba7";
          overlay0 = "#737994";
          surface2 = "#626880";
          surface1 = "#51576d";
          surface0 = "#414559";
          base = "#303446";
          mantle = "#292c3c";
          crust = "#232634";
        };
        catppuccin_latte = {
          rosewater = "#dc8a78";
          flamingo = "#dd7878";
          pink = "#ea76cb";
          mauve = "#8839ef";
          red = "#d20f39";
          maroon = "#e64553";
          peach = "#fe640b";
          yellow = "#df8e1d";
          green = "#40a02b";
          teal = "#179299";
          sky = "#04a5e5";
          sapphire = "#209fb5";
          blue = "#1e66f5";
          lavender = "#7287fd";
          text = "#4c4f69";
          subtext1 = "#5c5f77";
          subtext0 = "#6c6f85";
          overlay2 = "#7c7f93";
          overlay1 = "#8c8fa1";
          overlay0 = "#9ca0b0";
          surface2 = "#acb0be";
          surface1 = "#bcc0cc";
          surface0 = "#ccd0da";
          base = "#eff1f5";
          mantle = "#e6e9ef";
          crust = "#dce0e8";
        };
        catppuccin_macchiato = {
          rosewater = "#f4dbd6";
          flamingo = "#f0c6c6";
          pink = "#f5bde6";
          mauve = "#c6a0f6";
          red = "#ed8796";
          maroon = "#ee99a0";
          peach = "#f5a97f";
          yellow = "#eed49f";
          green = "#a6da95";
          teal = "#8bd5ca";
          sky = "#91d7e3";
          sapphire = "#7dc4e4";
          blue = "#8aadf4";
          lavender = "#b7bdf8";
          text = "#cad3f5";
          subtext1 = "#b8c0e0";
          subtext0 = "#a5adcb";
          overlay2 = "#939ab7";
          overlay1 = "#8087a2";
          overlay0 = "#6e738d";
          surface2 = "#5b6078";
          surface1 = "#494d64";
          surface0 = "#363a4f";
          base = "#24273a";
          mantle = "#1e2030";
          crust = "#181926";
        };
        ayu_mirage = {
          rosewater = "#ffdfb3";
          flamingo = "#f28779";
          pink = "#f27983";
          mauve = "#dfbfff";
          red = "#ff6666";
          maroon = "#f29e74";
          peach = "#ffad66";
          yellow = "#ffd173";
          green = "#d5ff80";
          teal = "#95e6cb";
          sky = "#5ccfe6";
          sapphire = "#73d0ff";
          blue = "#80bfff";
          lavender = "#b8cfe6";
          text = "#cccac2";
          subtext1 = "#afb3bb";
          subtext0 = "#9da1aa";
          overlay2 = "#8a9199";
          overlay1 = "#707a8c";
          overlay0 = "#576072";
          surface2 = "#3f4757";
          surface1 = "#282e3b";
          surface0 = "#242936";
          base = "#1f2430";
          mantle = "#1a1f29";
          crust = "#171b24";
        };
        ayu_dark = {
          rosewater = "#e6c08a";
          flamingo = "#f07178";
          pink = "#f26d78";
          mauve = "#d2a6ff";
          red = "#d95757";
          maroon = "#f29668";
          peach = "#ff8f40";
          yellow = "#ffb454";
          green = "#aad94c";
          teal = "#95e6cb";
          sky = "#39bae6";
          sapphire = "#59c2ff";
          blue = "#73b8ff";
          lavender = "#99adbf";
          text = "#bfbdb6";
          subtext1 = "#9da1aa";
          subtext0 = "#848996";
          overlay2 = "#6c7380";
          overlay1 = "#555e73";
          overlay0 = "#41495b";
          surface2 = "#2d3442";
          surface1 = "#1b1f29";
          surface0 = "#161a24";
          base = "#141821";
          mantle = "#10141c";
          crust = "#0d1017";
        };
        ayu_light = {
          rosewater = "#d9b077";
          flamingo = "#f07171";
          pink = "#ff7383";
          mauve = "#a37acc";
          red = "#e65050";
          maroon = "#ed9366";
          peach = "#ff7e33";
          yellow = "#f2a300";
          green = "#86b300";
          teal = "#4cbf99";
          sky = "#55b4d4";
          sapphire = "#399ee6";
          blue = "#478acc";
          lavender = "#787b80";
          text = "#5c6166";
          subtext1 = "#656c75";
          subtext0 = "#6e7884";
          overlay2 = "#778392";
          overlay1 = "#828e9f";
          overlay0 = "#99a4b2";
          surface2 = "#b0b9c4";
          surface1 = "#c8ced6";
          surface0 = "#e0e4e8";
          base = "#fcfcfc";
          mantle = "#fafafa";
          crust = "#f8f9fa";
        };
      };
    };
  };
}
