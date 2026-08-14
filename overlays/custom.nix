final: prev:
let
  zigPackages = prev.lib.recurseIntoAttrs (
    final.callPackage ../pkgs/zig {
      zigVersions = {
        "0.15.2" = {
          llvmPackages = final.llvmPackages_20;
          hash = "sha256-u3pEMcYN71d83MJh14vtzU4DJXnMHu/Jw86d9XvwKE8=";
          patches = [ ../pkgs/zig/xcode-26.4-compat.patch ];
        };
      };
    }
  );
  zig = zigPackages."0.16";
in
{
  pythonPackagesExtensions =
    prev.pythonPackagesExtensions
    ++ prev.lib.optionals prev.stdenv.hostPlatform.isDarwin [
      (python-final: python-prev: {
        afdko = python-prev.afdko.overridePythonAttrs (old: {
          doCheck = false;
          # pythonPackages.cmake's wrapper fails scikit-build-core's lipo probe on Darwin.
          env = (old.env or { }) // {
            CMAKE_EXECUTABLE = "${final.cmake}/bin/cmake";
          };
        });

        # Upstream race: https://github.com/ipython/ipython/issues/12164
        ipython = python-prev.ipython.overridePythonAttrs (old: {
          disabledTests = (old.disabledTests or [ ]) ++ [ "test_system_interrupt" ];
        });
      })
    ];

  mactop = prev.callPackage ../pkgs/mactop/package.nix { };
  raycast = prev.callPackage ../pkgs/raycast/package.nix { };

  inherit zigPackages zig;
  zig_0_13 = zigPackages."0.13";
  zig_0_14 = zigPackages."0.14";
  zig_0_15 = zigPackages."0.15";
  zig_0_16 = zig;

  zigStdenv = if prev.stdenv.cc.isZig then prev.stdenv else prev.lowPrio zig.passthru.stdenv;
}
// prev.lib.optionalAttrs prev.stdenv.hostPlatform.isDarwin {
  # Temporary workaround until nixpkgs PR #536365 reaches nixos-unstable.
  ld64 = prev.ld64.overrideAttrs {
    hardeningDisable = [ "libcxxhardeningfast" ];
  };
}
