{ pkgs, ... }:
{
  home.packages = [ pkgs.dconf ];

  home.sessionVariables.SSL_CERT_FILE = "/etc/ssl/certs/ca-bundle.crt";

  dconf = {
    enable = true;
    settings = {
      "org/gnome/desktop/interface" = {
        enable-animations = false;
      };
    };
  };
}
