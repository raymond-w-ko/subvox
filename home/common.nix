{
  inputs,
  pkgs,
  config,
  ...
}:
let
  repoDir = "${config.home.homeDirectory}/subvox";
  dotfilesDir = "${repoDir}/home";
  developmentPackages = import ../packages/development.nix { inherit pkgs inputs; };
in
{
  home.packages = developmentPackages.forHome;

  home.sessionVariables = {
    LIBCLANG_PATH = "${pkgs.llvmPackages.libclang.lib}/lib";
  }
  // pkgs.lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
    SSL_CERT_FILE = "/etc/ssl/certs/ca-bundle.crt";
  };

  # Disable manual generation to avoid builtins.toFile warning.
  manual.manpages.enable = false;

  # `programs.fish` enables man caches by default, but some Home Manager
  # profiles resolve `programs.man.package` to null (notably macOS).
  programs.man.generateCaches = config.programs.man.package != null;

  xdg.enable = true;

  home.file.".config/nvim/".source =
    config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.config/nvim";

  home.file.".claude/CLAUDE.md".source =
    config.lib.file.mkOutOfStoreSymlink "${repoDir}/ai/AGENTS.md";
  home.file.".codex/AGENTS.md".source = config.lib.file.mkOutOfStoreSymlink "${repoDir}/ai/AGENTS.md";
  home.file.".pi/".source = config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.pi";

  programs.direnv = {
    enable = true;
    nix-direnv.enable = true;
    enableBashIntegration = true;
    enableZshIntegration = true;
  };

  programs.zoxide = {
    enable = true;
    enableBashIntegration = true;
    enableZshIntegration = true;
    enableFishIntegration = true;
    options = [
      "--cmd"
      "j"
    ];
  };

  programs.fzf = {
    enable = true;
    enableBashIntegration = true;
    enableZshIntegration = true;
    enableFishIntegration = true;
  };

  programs.bash.enable = true;

  programs.fish = {
    enable = true;
    interactiveShellInit = ''
      set fish_greeting
      fish_config theme choose base16-default --color-theme=dark
      set -gx fish_prompt_pwd_dir_length 3
      set -gx fish_prompt_pwd_full_dirs 3

      fish_add_path $HOME/subvox/bin
      fish_add_path $HOME/bin

      set -l newpath (for p in $PATH
        if not string match -rq '^/mnt/c/' -- $p
          echo $p
        end
      end)
      set -gx PATH (string join ":" $newpath)

      test -f $HOME/.config/secrets.fish && source $HOME/.config/secrets.fish
    '';
    shellAbbrs = {
      e = "eza -l";
      ee = "eza -la";
      l = "eza -l";
      ll = "eza -la";
      v = "nvim";
      cd = "__zoxide_z";

      g = "git";
      gs = "git status";
      gsw = "git switch";
      gcfxd = "git clean -fxd";
      gd = "git diff";

      ga = "git add";
      gf = "git fetch";
      gl = "git pull";
      gm = "git merge";
      gc = "git commit";
      gca = "git commit -a";
      gcam = "git commit -a -m";
      gcav = "git commit -a -v";
      gp = "git push";
      gpfnv = "git push --force-with-lease --no-verify";

      ts = "tmux new -s";
      ta = "tmux attach -d -t";
      tl = "tmux list-sessions";

      oc = "opencode";
      c = "claude --dangerously-skip-permissions";
      x = "codex --yolo";
      i = "pi.sh";
      ir = "pi.sh --resume";

      ".." = "__zoxide_z ..";
      "..." = "__zoxide_z ../..";
      "...." = "__zoxide_z ../../..";
      "....." = "__zoxide_z ../../../..";
    };
  };

  programs.tmux = {
    enable = true;
    terminal = "tmux-256color";
    prefix = "f4";
    keyMode = "emacs";
    mouse = true;
    focusEvents = true;
    clock24 = true;
    newSession = false;
    baseIndex = 1;
    historyLimit = 10000;
    extraConfig = ''
      set -g default-shell ${pkgs.fish}/bin/fish
      set -g extended-keys on
      set -g extended-keys-format csi-u
      set -g status-justify centre
      set -g status-position top
      setw -g monitor-activity on
    '';
    plugins = with pkgs; [
      {
        plugin = tmuxPlugins.sensible;
      }
      {
        plugin = tmuxPlugins.catppuccin;
        extraConfig = ''
          set -g @catppuccin_flavor "frappe"
          set -g @catppuccin_window_status_style "basic"
          set -g status-right-length 100
          set -g status-left-length 100
          set -g status-left ""
          set -g status-right "#{E:@catppuccin_status_application}"
          set -ag status-right "#{E:@catppuccin_status_session}"
          set -ag status-right "#{E:@catppuccin_status_uptime}"
        '';
      }
    ];
  };

  programs.git = {
    enable = true;
    lfs.enable = true;
    settings = {
      user.name = "Raymond W. Ko";
      user.email = "raymond.w.ko@gmail.com";
      pull.rebase = true;
      init.defaultBranch = "master";
      core = {
        autocrlf = false;
        eol = "lf";
        pager = "delta";
      };
      credential.helper = "";
      credential."https://github.com".helper = "!gh auth git-credential";
      credential."https://gist.github.com".helper = "!gh auth git-credential";
      alias = {
        co = "checkout";
        br = "branch";
        cp = "cherry-pick";
        dl = "-c diff.external=difft log -p --ext-diff";
        ds = "-c diff.external=difft show --ext-diff";
        dft = "-c diff.external=difft diff";
        undo = "reset --soft HEAD^";
        lg = "log --graph --full-history --pretty=format:\"%h%x09%ar%x09%d%x20%s\"";
      };
    };
  };

  programs.lazygit = {
    enable = true;
    enableBashIntegration = true;
    enableZshIntegration = true;
    enableFishIntegration = true;
    shellWrapperName = "lg";
    settings.gui.theme.lightTheme = false;
  };

  programs.neovim = {
    enable = true;
    defaultEditor = true;
    vimAlias = true;
    sideloadInitLua = true;
  };

  programs.bun.enable = true;
  programs.uv.enable = true;
  programs.gpg.enable = true;
}
