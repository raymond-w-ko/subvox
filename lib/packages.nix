{ inputs }:
let
  customOverlay = import ../overlays/custom.nix;

  allowedUnfree = [
    "claude-code"
    "raycast"
  ];

  standaloneOverlays = [
    (import inputs.rust-overlay)
    inputs.neru.overlays.default
    customOverlay
  ];

  systemOverlays = [
    (import inputs.rust-overlay)
    inputs.neru.overlays.default
    inputs.claude-code.overlays.default
    customOverlay
  ];
in
{
  inherit
    allowedUnfree
    standaloneOverlays
    systemOverlays
    ;

  mkPkgs =
    system:
    import inputs.nixpkgs {
      inherit system;
      overlays = standaloneOverlays;
      config.allowUnfreePredicate = pkg: builtins.elem (inputs.nixpkgs.lib.getName pkg) allowedUnfree;
    };
}
