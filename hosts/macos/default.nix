{
  inputs,
  user,
  packageConfig,
  pkgs,
  ...
}:
{
  imports = [
    inputs.home-manager.darwinModules.home-manager
    ../common/all.nix
    { home-manager.users.${user}.home.stateVersion = "26.05"; }
  ];

  nix = {
    enable = true;
    gc.interval = {
      Weekday = 0;
      Hour = 0;
      Minute = 0;
    };
  };

  nixpkgs.hostPlatform = "aarch64-darwin";

  system = {
    configurationRevision = inputs.self.rev or inputs.self.dirtyRev or null;
    stateVersion = 6;
    primaryUser = user;
    defaults.NSGlobalDomain.NSWindowShouldDragOnGesture = true;
  };

  users.users.${user}.home = "/Users/${user}";

  environment.variables.PKG_CONFIG_PATH = "${pkgs.openssl.dev}/lib/pkgconfig:${pkgs.sqlite.dev}/lib/pkgconfig";

  environment.shells = with pkgs; [
    bash
    fish
    zsh
  ];

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    extraSpecialArgs = {
      inherit inputs user packageConfig;
    };

    users.${user} = import ../../home/common.nix;
  };
}
