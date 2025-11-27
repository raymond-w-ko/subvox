{ config, pkgs, ... }:

{
  home.username = "rko";
  home.homeDirectory = "/home/rko";

  home.stateVersion = "26.05";

  programs.fish = {
    enable = true;
  };
  programs.git = {
    enable = true;
    settings = {
      user.name = "Raymond W. Ko";
      user.email = "raymond.w.ko@gmail.com";
    };
  };
}
