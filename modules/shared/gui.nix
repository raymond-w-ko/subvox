{ pkgs, ... }:
{
  fonts.packages = import ../../packages/fonts.nix { inherit pkgs; };
}
