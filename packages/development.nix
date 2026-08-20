{ pkgs, inputs }:
let
  pythonDarwin = pkgs.python314.override {
    packageOverrides = self: super: {
      rapidfuzz = super.rapidfuzz.overridePythonAttrs (old: {
        env = (old.env or { }) // {
          RAPIDFUZZ_BUILD_EXTENSION = 0;
        };
        doCheck = false;
        doInstallCheck = false;
        pythonImportsCheck = [ ];
      });
    };
  };
  pythonPkg = if pkgs.stdenv.hostPlatform.isDarwin then pythonDarwin else pkgs.python314;
  poetryPkg =
    let
      poetryApplication =
        if pkgs.stdenv.hostPlatform.isDarwin then
          pkgs.poetry.override { python3 = pythonDarwin; }
        else
          pkgs.poetry;
      # Temporary workaround for https://github.com/NixOS/nixpkgs/issues/544083.
      patchedPoetryPackage = poetryApplication.python.pkgs.poetry.overridePythonAttrs (old: {
        disabledTests = (old.disabledTests or [ ]) ++ [
          "test_execute_executes_a_batch_of_operations"
          "test_execute_prints_warning_for_yanked_package"
        ];
      });
    in
    poetryApplication.withPlugins (ps: [
      (ps.poetry-plugin-shell.override { poetry = patchedPoetryPackage; })
    ]);

  # Packages managed by Home Manager programs.* (do not add here):
  # neovim, git, lazygit, fzf, zoxide, bash, fish, tmux, bun, uv, direnv
  common = with pkgs; [
    # nix tools
    nixpkgs-review
    nix-update

    # core utils
    gh
    gnumake
    htop
    btop
    file
    which
    tree
    less
    rsync
    lsof
    patch
    bc
    curl
    wget
    ripgrep
    fd
    jq
    ncdu
    imagemagick
    zip
    unzip
    difftastic
    delta

    # encryption
    age
    age-plugin-yubikey

    # shells
    zsh
    eza

    # javascript
    nodejs_24
    tsx

    # python
    pythonPkg
    poetryPkg

    # java/clojure
    javaPackages.compiler.openjdk25
    babashka

    # go
    go

    # zig
    zig

    # rust (nightly via rust-overlay — matches fff.nvim's toolchain)
    (pkgs.rust-bin.nightly."2026-03-14".default.override {
      extensions = [
        "clippy"
        "rustfmt"
        "llvm-tools"
        "miri"
        "rust-src"
        "rust-analyzer"
      ];
    })

    # perl
    perl

    # ai tools
    inputs.codex-cli-nix.packages.${pkgs.stdenv.hostPlatform.system}.default
    claude-code
  ];

  linux = with pkgs; [
    # c / c++
    gcc
    llvmPackages.libclang
    gdb # move back to common once compilation works on darwin again
    openssl
    pkg-config
    sqlite
    sqlite.dev
    bubblewrap
    traceroute

    # system diagnostics
    procps
    psmisc
    util-linux
    iproute2
    iputils
    dnsutils
    pciutils
    usbutils
    strace

    perf
    kcov
  ];

  darwin = with pkgs; [
    openssh
    openssl
    pkg-config
    mactop
  ];

  platform =
    (if pkgs.stdenv.hostPlatform.isDarwin then darwin else [ ])
    ++ (if pkgs.stdenv.hostPlatform.isLinux then linux else [ ]);
in
{
  inherit common linux darwin;

  forHome = common ++ platform;
}
