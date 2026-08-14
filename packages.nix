# Aggregate package interface. Focused consumers should import packages/* directly.
{ pkgs, inputs }:
let
  development = import ./packages/development.nix { inherit pkgs inputs; };
  gui = import ./packages/gui.nix { inherit pkgs; };
  fonts = import ./packages/fonts.nix { inherit pkgs; };
in
{
  inherit fonts;
  inherit (development) common;

  linux = development.linux;
  linuxGui = gui.linux;
  darwin = development.darwin;
  darwinGui = gui.darwin;

  # Headless development environment for the current platform.
  forHome = development.forHome;

  # GUI additions layered over the headless development environment.
  forGuiHome = gui.forHome;

  # Complete interactive workstation package set.
  forFullHome = development.forHome ++ gui.forHome;

  # Complete workstation package set including fonts.
  forHomeWithFonts = development.forHome ++ gui.forHome ++ fonts;

  # System-level package view retained for callers that need the full set.
  forSystem = development.forHome ++ gui.forHome;
}
