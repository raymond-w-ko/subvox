{ pkgs }:
let
  # Upstream ships the TTF; avoid rebuilding it and its image-processing tools.
  noto-color-emoji-bin = pkgs.stdenvNoCC.mkDerivation rec {
    pname = "noto-color-emoji-bin";
    version = "2.051";

    src = pkgs.fetchurl {
      url = "https://raw.githubusercontent.com/googlefonts/noto-emoji/v${version}/fonts/NotoColorEmoji.ttf";
      hash = "sha256-cqY1yz0vNSTFFiDN3kBrIXIE6KagbGoJb/jtS1/W4ns=";
    };

    dontUnpack = true;
    dontBuild = true;

    installPhase = ''
      runHook preInstall
      install -Dm644 "$src" "$out/share/fonts/noto/NotoColorEmoji.ttf"
      runHook postInstall
    '';

    meta = {
      description = "Prebuilt Noto color emoji font";
      homepage = "https://github.com/googlefonts/noto-emoji";
      license = pkgs.lib.licenses.ofl;
      platforms = pkgs.lib.platforms.all;
    };
  };
in
with pkgs;
[
  nerd-fonts.symbols-only
  nerd-fonts.droid-sans-mono
  nerd-fonts.jetbrains-mono
  noto-fonts
  noto-fonts-cjk-sans
  noto-color-emoji-bin
  liberation_ttf
  fira-code
  fira-code-symbols
  mplus-outline-fonts.githubRelease
  dina-font
  iosevka-bin
  aporetic
]
