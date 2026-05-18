#!/usr/bin/env python3
"""Idempotently fetch/build AI tools and write Claude/Codex settings."""

from __future__ import annotations

import argparse
import concurrent.futures as futures
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import threading

from _setup_ai_config import (
    create_template,
    repair_codex_config,
    setup_global_agent_configs,
    setup_home_settings,
    setup_project_settings,
)


HOME = Path.home()
SRC = HOME / "src"
BIN = HOME / "bin"
PRINT_LOCK = threading.Lock()
RED = "\033[1;31m"
RESET = "\033[0m"


@dataclass(frozen=True)
class OutputSpec:
    name: str
    source: str
    unlink_existing_symlink: bool = False


@dataclass(frozen=True)
class ProjectSpec:
    name: str
    repo: str
    rel_dir: str
    outputs: tuple[OutputSpec, ...] = ()
    build_cmd: tuple[str, ...] = ()
    build_requires: tuple[str, ...] = ()
    branch: str = "main"
    upstream: str | None = None
    update_remote: str = "origin"

    @property
    def src_dir(self) -> Path:
        return SRC / self.rel_dir


PROJECTS = (
    ProjectSpec("asupersync", "https://github.com/Dicklesworthstone/asupersync.git", "asupersync"),
    ProjectSpec("frankensqlite", "https://github.com/Dicklesworthstone/frankensqlite.git", "frankensqlite"),
    ProjectSpec("frankensearch", "https://github.com/Dicklesworthstone/frankensearch.git", "frankensearch"),
    ProjectSpec("frankentui", "https://github.com/Dicklesworthstone/frankentui.git", "frankentui"),
    ProjectSpec("sqlmodel_rust", "https://github.com/Dicklesworthstone/sqlmodel_rust.git", "sqlmodel_rust"),
    ProjectSpec("fastmcp_rust", "https://github.com/Dicklesworthstone/fastmcp_rust.git", "fastmcp_rust"),
    ProjectSpec("rich_rust", "https://github.com/Dicklesworthstone/rich_rust.git", "rich_rust"),
    ProjectSpec(
        "franken_agent_detection",
        "https://github.com/Dicklesworthstone/franken_agent_detection.git",
        "franken_agent_detection",
    ),
    ProjectSpec(
        "toon_rust",
        "https://github.com/Dicklesworthstone/toon_rust.git",
        "toon_rust",
        outputs=(OutputSpec("tru", "target/release/tru"),),
        build_cmd=("cargo", "build", "--release"),
        build_requires=("cargo",),
    ),
    ProjectSpec(
        "destructive_command_guard",
        "https://github.com/Dicklesworthstone/destructive_command_guard.git",
        "destructive_command_guard",
        outputs=(OutputSpec("dcg", "target/release/dcg"),),
        build_cmd=("cargo", "build", "--release"),
        build_requires=("cargo",),
    ),
    ProjectSpec(
        "beads_rust",
        "https://github.com/Dicklesworthstone/beads_rust.git",
        "beads_rust",
        outputs=(OutputSpec("br", "target/release/br"),),
        build_cmd=("cargo", "build", "--release"),
        build_requires=("cargo",),
    ),
    ProjectSpec(
        "beads_viewer",
        "https://github.com/raymond-w-ko/beads_viewer.git",
        "beads_viewer",
        outputs=(OutputSpec("bv", "bv"),),
        build_cmd=("make", "build"),
        build_requires=("make",),
        upstream="https://github.com/Dicklesworthstone/beads_viewer.git",
        update_remote="upstream",
    ),
    ProjectSpec(
        "mcp_agent_mail_rust",
        "https://github.com/Dicklesworthstone/mcp_agent_mail_rust.git",
        "mcp_agent_mail_rust",
        outputs=(
            OutputSpec("am", "target/release/am"),
            OutputSpec("mcp-agent-mail", "target/release/mcp-agent-mail"),
        ),
        build_cmd=("cargo", "build", "--release"),
        build_requires=("cargo",),
    ),
    ProjectSpec(
        "fff",
        "https://github.com/raymond-w-ko/fff.git",
        "fff",
        outputs=(OutputSpec("fff-mcp", "target/release/fff-mcp", unlink_existing_symlink=True),),
        build_cmd=("cargo", "build", "--release"),
        build_requires=("cargo",),
        upstream="https://github.com/dmtrKovalenko/fff.git",
        update_remote="upstream",
    ),
)


class CommandError(RuntimeError):
    def __init__(self, cmd: tuple[str, ...], cwd: Path | None, code: int, output: str):
        self.cmd = cmd
        self.cwd = cwd
        self.code = code
        self.output = output
        where = f" (cwd {cwd})" if cwd else ""
        tail = output[-8000:].rstrip()
        super().__init__(f"{shlex.join(cmd)}{where} exited {code}\n{tail}")


def log(message: str) -> None:
    with PRINT_LOCK:
        print(message, flush=True)


def section(message: str) -> None:
    log(f"\033[1;36m>>> {message} <<<\033[0m")


def red(message: str) -> str:
    return f"{RED}{message}{RESET}"


def run(cmd: list[str] | tuple[str, ...], cwd: Path | None = None) -> str:
    argv = tuple(str(part) for part in cmd)
    proc = subprocess.run(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if proc.returncode:
        raise CommandError(argv, cwd, proc.returncode, proc.stdout)
    return proc.stdout.strip()


def require_commands(names: tuple[str, ...] | set[str]) -> None:
    missing = sorted(name for name in set(names) if shutil.which(name) is None)
    if missing:
        raise RuntimeError(f"missing required commands: {', '.join(missing)}")


def ensure_remote(src_dir: Path, name: str, url: str) -> None:
    current = run(("git", "remote", "get-url", name), cwd=src_dir) if remote_exists(src_dir, name) else ""
    if not current:
        run(("git", "remote", "add", name, url), cwd=src_dir)
    elif current != url:
        run(("git", "remote", "set-url", name, url), cwd=src_dir)


def remote_exists(src_dir: Path, name: str) -> bool:
    proc = subprocess.run(
        ("git", "remote", "get-url", name),
        cwd=src_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode == 0


def tracked_clean(src_dir: Path) -> bool:
    return run(("git", "status", "--porcelain", "--untracked-files=no"), cwd=src_dir) == ""


def current_branch(src_dir: Path) -> str:
    return run(("git", "branch", "--show-current"), cwd=src_dir)


def local_branch_exists(src_dir: Path, branch: str) -> bool:
    proc = subprocess.run(
        ("git", "rev-parse", "--verify", f"refs/heads/{branch}"),
        cwd=src_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode == 0


def switch_branch(src_dir: Path, branch: str) -> None:
    if local_branch_exists(src_dir, branch):
        run(("git", "switch", branch), cwd=src_dir)
    else:
        run(("git", "switch", "-c", branch, f"origin/{branch}"), cwd=src_dir)


def ensure_repo(spec: ProjectSpec) -> str:
    SRC.mkdir(parents=True, exist_ok=True)
    cloned = False
    if not spec.src_dir.exists():
        run(("git", "clone", "--branch", spec.branch, spec.repo, str(spec.src_dir)))
        cloned = True

    if not (spec.src_dir / ".git").exists():
        raise RuntimeError(f"{spec.src_dir} exists but is not a git repository")

    ensure_remote(spec.src_dir, "origin", spec.repo)
    if spec.upstream:
        ensure_remote(spec.src_dir, "upstream", spec.upstream)

    run(("git", "fetch", "origin", f"+refs/heads/{spec.branch}:refs/remotes/origin/{spec.branch}"), cwd=spec.src_dir)
    if spec.upstream:
        run(
            ("git", "fetch", "upstream", f"+refs/heads/{spec.branch}:refs/remotes/upstream/{spec.branch}"),
            cwd=spec.src_dir,
        )

    if current_branch(spec.src_dir) != spec.branch:
        if not tracked_clean(spec.src_dir):
            return "fetched; skipped branch switch due tracked changes"
        switch_branch(spec.src_dir, spec.branch)

    if not tracked_clean(spec.src_dir):
        return "fetched; skipped fast-forward due tracked changes"

    run(("git", "merge", "--ff-only", f"{spec.update_remote}/{spec.branch}"), cwd=spec.src_dir)
    return "cloned + updated" if cloned else "updated"


def commit_timestamp(src_dir: Path) -> float:
    return float(run(("git", "log", "-1", "--format=%ct", "HEAD"), cwd=src_dir))


def installed_path(name: str) -> Path:
    return BIN / name


def is_up_to_date(spec: ProjectSpec, skip_existing: bool) -> bool:
    if not spec.outputs:
        return True
    targets = [installed_path(out.name) for out in spec.outputs]
    if skip_existing and all(target.exists() for target in targets):
        return True
    latest = commit_timestamp(spec.src_dir)
    return all(target.exists() and target.stat().st_mtime >= latest for target in targets)


def running_pids(name: str) -> list[int]:
    proc_root = Path("/proc")
    if proc_root.exists():
        pids = []
        for entry in proc_root.iterdir():
            if not entry.name.isdigit() or int(entry.name) == os.getpid():
                continue
            pid = int(entry.name)
            try:
                cmdline = (entry / "cmdline").read_bytes().split(b"\0")
                exe = (entry / "exe").resolve().name if (entry / "exe").exists() else ""
            except (OSError, UnicodeDecodeError):
                continue
            argv0 = Path(cmdline[0].decode(errors="ignore")).name if cmdline and cmdline[0] else ""
            if name in {argv0, exe}:
                pids.append(pid)
        return sorted(set(pids))

    pgrep = shutil.which("pgrep")
    if not pgrep:
        return []
    proc = subprocess.run((pgrep, "-x", name), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return [int(line) for line in proc.stdout.splitlines() if line.strip().isdigit()]


def install_output(spec: ProjectSpec, output: OutputSpec) -> str:
    source = spec.src_dir / output.source
    if not source.exists():
        raise RuntimeError(f"{spec.name}: missing build output {source}")

    BIN.mkdir(parents=True, exist_ok=True)
    target = installed_path(output.name)
    pids = running_pids(output.name) if target.exists() or target.is_symlink() else []
    if pids:
        return f"blocked {output.name}: running pids {', '.join(map(str, pids))}"
    if output.unlink_existing_symlink and target.is_symlink():
        target.unlink()

    fd, tmp_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=target.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    shutil.copy2(source, tmp)
    os.utime(tmp, None)
    tmp.chmod(tmp.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    os.replace(tmp, target)
    return f"installed {output.name}"


def build_project(spec: ProjectSpec, skip_existing: bool) -> str:
    if is_up_to_date(spec, skip_existing):
        return "skipped; up to date"
    require_commands(spec.build_requires)
    section(f"Building {', '.join(out.name for out in spec.outputs)}")
    run(spec.build_cmd, cwd=spec.src_dir)
    return "; ".join(install_output(spec, output) for output in spec.outputs)


def run_parallel(label: str, specs: list[ProjectSpec], fn, workers: int) -> tuple[dict[str, str], dict[str, str]]:
    section(label)
    results: dict[str, str] = {}
    errors: dict[str, str] = {}
    with futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        pending = {pool.submit(fn, spec): spec.name for spec in specs}
        for future in futures.as_completed(pending):
            name = pending[future]
            try:
                results[name] = future.result()
                log(f"{name}: {results[name]}")
            except Exception as exc:
                errors[name] = str(exc)
                log(red(f"{name}: ERROR\n{errors[name]}"))
    return results, errors


def full_setup(args: argparse.Namespace) -> int:
    require_commands(("git",))
    fetch_results, fetch_errors = run_parallel("Fetching repos", list(PROJECTS), ensure_repo, args.fetch_jobs)
    build_specs = [spec for spec in PROJECTS if spec.outputs and spec.name not in fetch_errors]
    build_results, build_errors = run_parallel(
        "Building binaries",
        build_specs,
        lambda spec: build_project(spec, args.skip_existing),
        args.build_jobs,
    )
    setup_error = ""
    try:
        setup_global_agent_configs()
    except Exception as exc:
        setup_error = str(exc)
        log(red(f"agent config: ERROR\n{setup_error}"))

    section("Summary")
    for name, result in {**fetch_results, **build_results}.items():
        log(f"{name}: {result}")
    errors = {**fetch_errors, **build_errors}
    if setup_error:
        errors["agent config"] = setup_error
    if errors:
        log(red("Errors:"))
        for name, error in errors.items():
            log(red(f"- {name}: {error.splitlines()[0]}"))
        return 1
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--skip-existing", action="store_true", help="skip builds when installed outputs exist")
    parser.add_argument("--fetch-jobs", type=int, default=8, help="parallel repo fetch/update jobs")
    parser.add_argument("--build-jobs", type=int, default=min(4, max(1, os.cpu_count() or 1)), help="parallel build jobs")
    parser.add_argument("--repair-codex-config", action="store_true", help="repair ~/.codex/config.toml and exit")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("create-template", help="regenerate the AGENTS template via Claude")
    config = subparsers.add_parser("config", help="write Claude/Codex settings only")
    config.add_argument("target_dir", nargs="?", default=str(HOME))
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        if args.repair_codex_config:
            repair_codex_config()
            return 0
        if args.command == "create-template":
            create_template()
            return 0
        if args.command == "config":
            target_dir = Path(args.target_dir).resolve()
            if target_dir == HOME:
                setup_home_settings()
            else:
                setup_project_settings(target_dir)
            return 0
        return full_setup(args)
    except RuntimeError as exc:
        print(red(f"Error: {exc}"), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
