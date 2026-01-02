# Repository Guidelines

## Project Structure & Module Organization
- `flake.nix` and `flake.lock` define inputs (nixpkgs, home-manager, nix-darwin, NixOS-WSL) and outputs for each host.
- `profiles/common.nix` holds shared system defaults (packages, shells, home-manager wiring).
- `hosts/` contains host-specific NixOS/Darwin modules (currently `wsl2.nix`; add `vm.nix`/`darwin.nix` before enabling those outputs).
- `home/` keeps user-level home-manager modules (e.g., `home/rko.nix`).

## Build, Test, and Development Commands
- Validate flake and eval consistency: `nix flake check`.
- Build without applying for quick safety: `nix build .#nixosConfigurations.wsl2.config.system.build.toplevel` (swap host attr as needed).
- Apply NixOS changes on WSL: `sudo nixos-rebuild switch --flake .#wsl2`.
- Apply on macOS (darwin output): `darwin-rebuild switch --flake .#darwin` once `hosts/darwin.nix` exists.
- Update inputs carefully: `nix flake update`; commit resulting `flake.lock` with a dedicated message.

## Coding Style & Naming Conventions
- Nix files use 2-space indentation, trailing semicolons on attr sets, and concise comments explaining non-obvious choices.
- Keep host module names aligned with flake outputs (`wsl2`, `vm`, `darwin`) and place per-host overrides in `hosts/<name>.nix`.
- Prefer small reusable options in `profiles/`; keep secrets and machine-specific paths inside host files.
- Run a formatter before pushing (`nix fmt` if configured, otherwise `nixpkgs-fmt`/`alejandra`).

## Testing Guidelines
- Always run `nix flake check` before opening a PR or switching a system.
- For risky changes, build each target you affect (e.g., `.#nixosConfigurations.vm` or `.#darwinConfigurations.darwin`) to catch eval errors early.
- Name tests and modules after the machine or feature they configure to simplify diff review.

## Commit & Pull Request Guidelines
- Follow conventional commits (e.g., `chore: pin nixpkgs`, `feat(wsl2): enable graphics`). Keep commits focused on related files.
- Include `flake.lock` changes in the same commit that updated inputs; avoid mixing with unrelated edits.
- PRs should state the host(s) impacted, commands run (`nix flake check`, builds), and any manual steps required after merge.
- Avoid destructive git commands (`git reset --hard`, force-pushing without `--force-with-lease`).
- Do not add secrets or machine-specific tokens; `.env` and similar files stay user-owned.

## Agent-Specific Notes
- Coordinate before removing files; prefer refactors over deletions when other agents may be editing adjacent code.
- Never edit environment variable files or undo others’ work; ask first if a conflicting change appears.
- Use `rg` for searches and keep edits minimal and purposeful.
