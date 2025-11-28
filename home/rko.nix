{ config, pkgs, ... }:

{
  home.username = "rko";
  home.homeDirectory = "/home/rko";

  home.stateVersion = "26.05";

  programs.zoxide = {
    enable = true;
    enableBashIntegration = true;
    enableZshIntegration = true;
    enableFishIntegration = true;
    options = ["--cmd" "j"];
  };

  programs.fish = {
    enable = true;
    binds = {};
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
      gc = "git commit";
      gca = "git commit -a";
      gcam = "git commit -a -m";
      gp = "git push";
      gpfnv = "git push --force-with-lease --no-verify";

      ts = "tmux new -s";
      ta = "tmux attach -d -t";
      tl = "tmux list-sessions";

      oc = "opencode";
      cx = "codex";

      ".." = "__zoxide_z ..";
      "..." = "__zoxide_z ../..";
      "...." = "__zoxide_z ../../..";
    };
  };
  programs.git = {
    enable = true;
    settings = {
      user.name = "Raymond W. Ko";
      user.email = "raymond.w.ko@gmail.com";
    };
  };
}
