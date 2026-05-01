{
  lib,
  zsh,
}:

zsh.overrideAttrs (
  oldAttrs:
  let
    patches = oldAttrs.patches or [ ];
    hasSigsuspendPatch = lib.any (
      patch: builtins.baseNameOf (toString patch) == "fix-sigsuspend-probe-c23.patch"
    ) patches;
  in
  {
    patches = patches ++ lib.optional (!hasSigsuspendPatch) ./fix-sigsuspend-probe-c23.patch;
  }
)
