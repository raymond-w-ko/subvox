{ pkgs, ... }:
{
  home.packages = [
    pkgs.dconf
    pkgs.gvfs
  ];

  systemd.user.packages = [ pkgs.gvfs ];
  home.sessionVariables.GIO_EXTRA_MODULES = "${pkgs.gvfs}/lib/gio/modules";

  dconf = {
    enable = true;
    settings = {
      "org/gnome/desktop/interface" = {
        enable-animations = false;
      };
    };
  };
}
