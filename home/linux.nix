{ pkgs, ... }:
{
  home.packages = [ pkgs.dconf ];

  dconf = {
    enable = true;
    settings = {
      "org/gnome/desktop/interface" = {
        enable-animations = false;
      };
    };
  };
}
