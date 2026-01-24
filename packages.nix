# Package definitions for home-manager and system configurations
# Usage: import ./packages.nix { inherit pkgs; }
{ pkgs }:
let
  # Packages managed by home-manager programs.* (do NOT add here):
  #   neovim, git, lazygit, fzf, zoxide, bash, fish, tmux, bun, uv, direnv

  common = with pkgs; [
    # nix tools
    nixpkgs-review
    nix-update

    # core utils
    gh
    gdb
    gnumake
    htop
    curl
    wget
    ripgrep
    fd
    jq
    ncdu
    imagemagick

    # shells
    zsh
    eza

    # javascript
    nodejs_24
    tsx

    # python
    python314

    # java/clojure
    javaPackages.compiler.openjdk25
    babashka

    # go
    go

    # zig
    zig

    # rust
    rustc
    cargo

    # perl
    perl

    # ai tools
    codex
    (claude-code-bun.override { bunBinName = "claude"; })
  ];

  fonts = with pkgs; [
    nerd-fonts.droid-sans-mono
    noto-fonts
    noto-fonts-cjk-sans
    noto-fonts-color-emoji
    liberation_ttf
    fira-code
    fira-code-symbols
    mplus-outline-fonts.githubRelease
    dina-font
    iosevka
    aporetic
    jetbrains-mono
  ];

  linux = with pkgs; [
    # c / c++
    gcc
    openssl
    pkg-config

    perf
    kcov

    adwaita-icon-theme
    ghostty
    # gstreamer plugins for ghostty bell
    gst_all_1.gstreamer
    gst_all_1.gst-plugins-base
    gst_all_1.gst-plugins-good
    gst_all_1.gst-plugins-ugly
    gst_all_1.gst-plugins-bad
    gst_all_1.gst-libav
    gst_all_1.gst-vaapi
  ];

  darwin = with pkgs; [
    mactop
    kanata
    aerospace
    sketchybar
    raycast
  ];

in
{
  inherit
    common
    fonts
    linux
    darwin
    ;

  # All packages for the current platform
  forHome =
    common
    ++ (if pkgs.stdenv.isDarwin then darwin else [ ])
    ++ (if pkgs.stdenv.isLinux then linux else [ ]);

  # All packages including fonts
  forHomeWithFonts =
    common
    ++ fonts
    ++ (if pkgs.stdenv.isDarwin then darwin else [ ])
    ++ (if pkgs.stdenv.isLinux then linux else [ ]);

  # System-level packages (for environment.systemPackages)
  forSystem =
    common
    ++ (if pkgs.stdenv.isDarwin then darwin else [ ])
    ++ (if pkgs.stdenv.isLinux then linux else [ ]);
}
