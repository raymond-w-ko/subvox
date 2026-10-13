# subvox

## Home files

`home/` mirrors the user's `$HOME` and holds static files that Home Manager
symlinks or stages into matching home paths. Home Manager modules live in
`modules/home/`, and package lists live in `packages/`.

Deployment mappings are explicit in the Home Manager modules. For example,
`~/.pi` links to `subvox/home/.pi`, making `subvox/home/.pi/agent` available at
`~/.pi/agent`. The `home/.gdu.yaml` file is linked to `~/.gdu.yaml`.

## User executables

All host and standalone Home Manager profiles add `$HOME/.local/bin` to `PATH`
through `modules/home/common.nix`. NixOS hosts also enable
`environment.localBinInPath`. Apply the configuration with
`./scripts/rebuild switch <target>`, then start a new shell to pick up the updated
path.

## GitHub Actions artifacts

`scripts/artifact-management.py` requires Python 3 and an authenticated `gh` CLI.
By default, it lists artifacts across all repositories owned by the authenticated
user, including private repositories. Organization repositories are excluded.
Pass `OWNER/REPO` to list only that repository.

```sh
./scripts/artifact-management.py
./scripts/artifact-management.py raymond-w-ko/fff
./scripts/artifact-management.py --delete raymond-w-ko/fff
```

`--delete` permanently deletes every artifact in the explicitly named repository.
It cannot delete across all repositories. The script fetches all artifact pages
before deleting and stops on API errors. Successful deletions are not rolled back.

Run the offline tests with `python3 -B -m unittest discover -s scripts -p 'test_artifact_management.py'`.

## Bun

The shared overlay replaces `pkgs.bun` with `pkgs/bun/package.nix`, a local copy
of the upstream nixpkgs expression pinned to Bun 1.4.3 for a required bug fix.
The archive SHA-256 hashes are verified for x86_64 Linux, aarch64 Linux, and
aarch64 macOS. Both host configurations and standalone Home Manager profiles
use this package, including `programs.bun`.

The expression is based on
[`pkgs/by-name/bu/bun/package.nix`](https://github.com/NixOS/nixpkgs/blob/4ba99f3209788ed04f01af38f77ddb803ad6ec63/pkgs/by-name/bu/bun/package.nix).
It is vendored rather than fetched from a moving `master` URL during evaluation.
To update the pin, change the version and all three archive hashes in
`pkgs/bun/package.nix`. Apply it with `./scripts/rebuild switch <target>`.

## Disk usage

All host and standalone Home Manager profiles include `gdu`, an interactive disk
usage analyzer. It is supported on x86_64 Linux, aarch64 Linux, and aarch64 macOS.
Run `gdu` to inspect the current directory or `gdu /path/to/directory` for another
location. The shared `home/.gdu.yaml` configuration enables background and
parallel deletion, uses black text on a red background for the selected row,
and uses white text on a purple background for marked entries.

## Docker on macOS

The `macos` system configuration installs the Docker CLI and Colima. Colima runs
Docker in a Linux VM; the NixOS Docker service and `docker` group are not used.

Apply the configuration, start the VM, and verify Docker:

```sh
./scripts/rebuild switch macos
colima start --runtime docker
docker run --rm hello-world
```

Colima starts manually, not automatically at login. Use `colima stop` to stop the
VM. The standalone `rko@macos` Home Manager profile does not install these system
packages.

## GVfs

NixOS hosts enable GVfs for mounting, trash, and other file-management features.
Linux GUI Home Manager profiles install GVfs, expose its GIO modules, and register
its systemd user units. Standalone profiles still need host-provided D-Bus, FUSE,
and UDisks2 support for mounting. macOS profiles are unchanged.

NixOS hosts and Linux GUI Home Manager profiles also include `trash-cli` for
command-line access to the freedesktop.org trash, including `trash-put`,
`trash-list`, and `trash-restore`.
