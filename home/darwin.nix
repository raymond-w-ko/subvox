{ inputs, pkgs, ... }:
{
  imports = [ inputs.neru.homeManagerModules.default ];

  services.neru = {
    enable = true;
    package = pkgs.neru-source;
    config = builtins.readFile ../configs/neru-qwerty.toml;
  };
}
