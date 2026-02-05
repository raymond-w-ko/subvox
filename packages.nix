# Package definitions for home-manager and system configurations
# Usage: import ./packages.nix { inherit pkgs codex-cli-nix; }
{ pkgs, codex-cli-nix }:
let
  pythonDarwin = pkgs.python314.override {
    packageOverrides = self: super: {
      rapidfuzz = super.rapidfuzz.overridePythonAttrs (old: {
        env = (old.env or { }) // { RAPIDFUZZ_BUILD_EXTENSION = 0; };
        doCheck = false;
        doInstallCheck = false;
        pythonImportsCheck = [ ];
      });
    };
  };
  pythonPkg = if pkgs.stdenv.isDarwin then pythonDarwin else pkgs.python313;
  poetryPkg =
    let
      basePoetry =
        if pkgs.stdenv.isDarwin
        then pkgs.poetry.override { python3 = pythonDarwin; }
        else pkgs.poetry;
    in
    basePoetry.withPlugins (ps: [ ps.poetry-plugin-shell ]);

  # Packages managed by home-manager programs.* (do NOT add here):
  #   neovim, git, lazygit, fzf, zoxide, bash, fish, tmux, bun, uv, direnv

  common = with pkgs; [
    # nix tools
    nixpkgs-review
    nix-update

    # core utils
    gh
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
    pythonPkg
    poetryPkg
    # poetry plugin: shell is included via poetryPkg

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
    codex-cli-nix.packages.${pkgs.stdenv.hostPlatform.system}.default
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
    gdb # move back to common once compilation works on darwin again
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
    openssl
    pkg-config

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
