# AGENTS.md — subvox

> Guidelines for AI coding agents working in this codebase.

---

## RULE 0 - THE FUNDAMENTAL OVERRIDE PREROGATIVE

If I tell you to do something, even if it goes against what follows below, YOU MUST LISTEN TO ME. I AM IN CHARGE, NOT YOU.

---

## RULE NUMBER 1: NO FILE DELETION

**YOU ARE NEVER ALLOWED TO DELETE A FILE WITHOUT EXPRESS PERMISSION.** Even a new file that you yourself created, such as a test code file. You have a horrible track record of deleting critically important files or otherwise throwing away tons of expensive work. As a result, you have permanently lost any and all rights to determine that a file or folder should be deleted.

**YOU MUST ALWAYS ASK AND RECEIVE CLEAR, WRITTEN PERMISSION BEFORE EVER DELETING A FILE OR FOLDER OF ANY KIND.**

---

## Irreversible Git & Filesystem Actions — DO NOT EVER BREAK GLASS

1. **Absolutely forbidden commands:** `git reset --hard`, `git clean -fd`, `rm -rf`, or any command that can delete or overwrite code/data must never be run unless the user explicitly provides the exact command and states, in the same message, that they understand and want the irreversible consequences.
2. **No guessing:** If there is any uncertainty about what a command might delete or overwrite, stop immediately and ask the user for specific approval. "I think it's safe" is never acceptable.
3. **Safer alternatives first:** When cleanup or rollbacks are needed, request permission to use non-destructive options (`git status`, `git diff`, `git stash`, copying to backups) before ever considering a destructive command.
4. **Mandatory explicit plan:** Even after explicit user authorization, restate the command verbatim, list exactly what will be affected, and wait for a confirmation that your understanding is correct. Only then may you execute it—if anything remains ambiguous, refuse and escalate.
5. **Document the confirmation:** When running any approved destructive command, record (in the session notes / final response) the exact user text that authorized it, the command actually run, and the execution time. If that record is absent, the operation did not happen.

---

# subvox Repository Guidelines

## Pi Development
- `home/.pi/agent/extensions/pi-rko-compact-tool-display/` contains the `pi-rko-compact-tool-display` pi extension.
- A local `pi` source checkout is usually available at `~/src/pi`.

## Commands
```sh
# validate
nix flake check

# list allowed targets without taking action
./scripts/rebuild build
./scripts/rebuild switch

# build or activate an explicit target
./scripts/rebuild build nixvac
./scripts/rebuild switch nixvac
./scripts/rebuild switch 'rko@linux'  # Home Manager target
./scripts/rebuild build wsl2 --print  # show exact command without running it

# first NixOS flake switch before nix-command/flakes are enabled
./scripts/bootstrap-nixos nixvac

# format
nix fmt

# update inputs
nix flake update
# or: ./scripts/update
```

## Style
- 2-space indent, trailing semicolons
- Run `nix fmt` after editing nix files
- Run `nix flake check` before committing

## Commits
- Conventional commits: `feat:`, `fix:`, `chore:`, `refactor:`
- Include `flake.lock` changes with input updates
- No secrets or tokens in repo
