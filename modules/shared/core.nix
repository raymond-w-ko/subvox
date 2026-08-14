{
  user,
  packageConfig,
  pkgs,
  lib,
  ...
}:
{
  nix.settings.experimental-features = [
    "nix-command"
    "flakes"
  ];

  nix.gc = {
    automatic = true;
    options = "--delete-older-than 30d";
  };

  nixpkgs.overlays = packageConfig.systemOverlays;
  nixpkgs.config.allowUnfreePredicate =
    pkg: builtins.elem (lib.getName pkg) packageConfig.allowedUnfree;

  time.timeZone = "America/New_York";
  security.sudo.keepTerminfo = true;
  programs.fish.enable = true;
  users.users.${user}.shell = pkgs.fish;
}
