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

Every action has a keyboard shortcut shown in the footer: `g` generate, `v` validate, `a` apply, `s` switch, and `c` commit. Press `q` to quit.

`claude-code` and `codex-cli-nix` follow the repository's root `nixpkgs`. Updating either application therefore cannot silently update a private Nixpkgs revision. Update root `nixpkgs` through the core group when ready to test infrastructure changes.

If `flake.lock` already has uncommitted changes, the updater refuses to generate a candidate so existing work cannot be overwritten.
