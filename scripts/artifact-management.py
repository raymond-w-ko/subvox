#!/usr/bin/env python3
"""List GitHub Actions artifacts; delete only from an explicitly named repository."""

import argparse
import json
import re
import subprocess
import sys


def api(endpoint, *, paginate=False, delete=False):
    command = ["gh", "api", endpoint]
    if paginate:
        command.extend(["--paginate", "--slurp"])
    if delete:
        command.extend(["--method", "DELETE"])
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return None if delete else json.loads(result.stdout)


def owned_repositories():
    owner = api("/user")["login"]
    pages = api("/user/repos?affiliation=owner&per_page=100", paginate=True)
    return sorted({
        repo["full_name"]
        for page in pages
        for repo in page
        if repo["owner"]["login"].casefold() == owner.casefold()
    })


def fetch_artifacts(repo):
    pages = api(f"/repos/{repo}/actions/artifacts?per_page=100", paginate=True)
    artifacts = [artifact for page in pages for artifact in page["artifacts"]]
    # Validate the entire snapshot before issuing any DELETE request.
    for artifact in artifacts:
        if type(artifact["id"]) is not int or artifact["id"] <= 0:
            raise ValueError(f"Invalid artifact ID in {repo}")
        if not isinstance(artifact["name"], str):
            raise ValueError(f"Invalid artifact name in {repo}")
    return artifacts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repo", nargs="?", metavar="OWNER/REPO",
        help="repository to list; defaults to all repositories owned by the authenticated user",
    )
    parser.add_argument(
        "--delete", action="store_true",
        help="permanently delete all listed artifacts; requires OWNER/REPO",
    )
    args = parser.parse_args(argv)
    if args.delete and not args.repo:
        parser.error("--delete requires an explicit OWNER/REPO")
    if args.repo and (
        not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", args.repo)
        or args.repo.split("/")[1] in {".", ".."}
    ):
        parser.error("repository must be OWNER/REPO")

    try:
        repos = [args.repo] if args.repo else owned_repositories()
        if not repos:
            print("No owned repositories found.")
        for repo in repos:
            artifacts = fetch_artifacts(repo)
            print(f"\n{repo}: {len(artifacts)} artifact(s)", flush=True)
            for artifact in artifacts:
                print(f"  {artifact['id']}\t{json.dumps(artifact['name'])}", flush=True)
            if args.delete:
                for artifact in artifacts:
                    api(f"/repos/{repo}/actions/artifacts/{artifact['id']}", delete=True)
                    print(f"Deleted {repo}: {artifact['id']}", flush=True)
        if not args.delete:
            print("\nListing only. Delete one repository with --delete OWNER/REPO.")
    except subprocess.CalledProcessError as error:
        print(f"gh api failed: {error.stderr.strip()}", file=sys.stderr)
        if args.delete:
            print("Stopped. Earlier successful deletions are not rolled back.", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
