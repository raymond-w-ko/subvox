{ inputs, pkgs, ... }:
{
  imports = [ inputs.neru.homeManagerModules.default ];

  services.neru = {
    enable = true;
    package = pkgs.neru-source;
    config = builtins.readFile ../../configs/neru-qwerty.toml;
  };

  # Run the default Colima profile as a launchd agent, so Docker is up after login.
  # With xdg.enable and stateVersion >= 26.05, COLIMA_HOME is ~/.config/colima.
  # No settings here: the existing ~/.config/colima/default/colima.yaml stays in charge.
  services.colima.enable = true;
}
