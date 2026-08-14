{ pkgs, config, ... }:
let
  repoDir = "${config.home.homeDirectory}/subvox";
  dotfilesDir = "${repoDir}/home";
  guiPackages = import ../packages/gui.nix { inherit pkgs; };
in
{
  home.packages = guiPackages.forHome;

  home.file.".config/ghostty/".source =
    config.lib.file.mkOutOfStoreSymlink "${dotfilesDir}/.config/ghostty";
}
