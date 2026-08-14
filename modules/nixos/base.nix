{
  user,
  pkgs,
  ...
}:
{
  imports = [
    ../shared/core.nix
    ./home-manager.nix
  ];

  nix.settings.trusted-users = [ user ];
  nix.gc.dates = "weekly";

  environment.localBinInPath = true;
  environment.sessionVariables.PKG_CONFIG_PATH = "${pkgs.openssl.dev}/lib/pkgconfig:${pkgs.sqlite.dev}/lib/pkgconfig";
  environment.sessionVariables.LIBRARY_PATH = "${pkgs.sqlite.out}/lib:${pkgs.openssl.out}/lib";

  programs.nix-ld.enable = true;

  i18n.defaultLocale = "en_US.UTF-8";
  i18n.extraLocaleSettings = {
    LC_ADDRESS = "en_US.UTF-8";
    LC_IDENTIFICATION = "en_US.UTF-8";
    LC_MEASUREMENT = "en_US.UTF-8";
    LC_MONETARY = "en_US.UTF-8";
    LC_NAME = "en_US.UTF-8";
    LC_NUMERIC = "en_US.UTF-8";
    LC_PAPER = "en_US.UTF-8";
    LC_TELEPHONE = "en_US.UTF-8";
    LC_TIME = "en_US.UTF-8";
  };

  users.users.${user} = {
    isNormalUser = true;
    description = "Raymond W. Ko";
    extraGroups = [ "wheel" ];
  };
}
