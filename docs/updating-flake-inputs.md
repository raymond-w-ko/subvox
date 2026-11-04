# Updating flake inputs

Run the guarded updater from the repository root:

```sh
./scripts/update
```

The default selection is the frequently updated group: `neru`, `claude-code`, and `codex-cli-nix`.
Core inputs (`nixpkgs`, `nix-darwin`, `home-manager`, `nixos-wsl`, and `rust-overlay`) are selected manually.
You can preselect a group from the command line:

```sh
./scripts/update high
./scripts/update core
./scripts/update all
./scripts/update neru home-manager
```

The updater writes changes to a temporary candidate lock first. **Generate candidate** shows direct and transitive revisions without changing `flake.lock`. The updater identifies its current target (`wsl2` under WSL, `macos` under Darwin, otherwise the Linux hostname) and passes that target explicitly to `scripts/rebuild`. **Validate + build** evaluates the flake, then runs `scripts/rebuild build <target>` against the candidate lock. **Apply validated lock** replaces `flake.lock` only after validation succeeds. **Switch system** runs `scripts/rebuild switch <target>`. **Commit lock** is optional and never pushes.

The updater detects the terminal's light or dark background at startup (`--theme auto`, the default). It queries the terminal's background color with OSC 11, a terminal control sequence, and waits up to 200 ms for a reply. If no usable reply arrives, it reads the background palette index from `COLORFGBG`. If neither source is available, it uses dark. Detection does not run when you request an explicit theme.

Use `./scripts/update --theme light` or `--theme dark` to override detection. Theme options can be combined with input selections, for example `./scripts/update --theme light core`. Press `t` to switch between light and dark without changing your selection or update state. Theme changes last only for the current session; the updater does not track later terminal theme changes.

Both themes use colors from the standard xterm 256-color palette. The launcher also limits generated shades to that palette, even on true-color terminals. Set `TEXTUAL_COLOR_SYSTEM` to override this default if needed, for example `TEXTUAL_COLOR_SYSTEM=truecolor ./scripts/update`.

Every action has a keyboard shortcut shown in the footer: `g` generate, `v` validate, `a` apply, `s` switch, and `c` commit. Press `q` to quit.

`claude-code` and `codex-cli-nix` follow the repository's root `nixpkgs`. Updating either application therefore cannot silently update a private Nixpkgs revision. Update root `nixpkgs` through the core group when ready to test infrastructure changes.

If `flake.lock` already has uncommitted changes, the updater refuses to generate a candidate so existing work cannot be overwritten.
