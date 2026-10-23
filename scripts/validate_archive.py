#!/usr/bin/env python3
"""Check the Markdown archive's format and obvious publication mistakes.

This deliberately small heuristic is not a personal-data or secret detector.
"""
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


CORE_DIRECTORIES = ("identity", "workflow", "memory", "skills", "archive")
REQUIRED_TEMPLATES = frozenset({
    "identity/profile.md", "identity/goals.md",
    "workflow/preferences.md", "workflow/tools.md", "workflow/priorities.md",
    "memory/experiences.md", "memory/decisions.md", "memory/preferences.md",
    "skills/inventory.md", "skills/learning-plan.md",
    "archive/index.md", "archive/project-template.md",
})
MAX_FILE_BYTES = 256 * 1024
TAG = re.compile(r"^# AI-(?:READONLY|WRITABLE):\s*\S")
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----"),
)
IGNORED_PARTS = {".git", "__pycache__", ".venv", "exports"}


def has_obvious_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def validate_paths(root: Path, relative_paths: list[str]) -> list[str]:
    """Return all failures, without modifying the archive."""
    root = root.resolve()
    errors: list[str] = []
    markdown_by_directory = {directory: [] for directory in CORE_DIRECTORIES}
    for relative in sorted(relative_paths):
        parts = PurePosixPath(relative).parts
        if not parts or any(part in IGNORED_PARTS for part in parts):
            continue
        if PurePosixPath(relative).is_absolute() or ".." in parts:
            errors.append(f"{relative}: unsafe repository path")
            continue
        path = root.joinpath(*parts)
        if any(root.joinpath(*parts[:index]).is_symlink() for index in range(1, len(parts) + 1)):
            errors.append(f"{relative}: symbolic links are not allowed")
            continue
        if not path.is_file():
            errors.append(f"{relative}: tracked file is missing")
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            errors.append(f"{relative}: exceeds {MAX_FILE_BYTES} bytes")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            if path.suffix == ".md":
                errors.append(f"{relative}: Markdown must be UTF-8")
            continue
        if has_obvious_secret(content):
            errors.append(f"{relative}: resembles an API credential or private key; inspect before publishing")
        if path.suffix != ".md":
            continue
        first_line = content.splitlines()[0] if content else ""
        if not TAG.match(first_line):
            errors.append(f"{relative}: first line must be '# AI-READONLY: title' or '# AI-WRITABLE: title'")
        if parts[0] in markdown_by_directory:
            markdown_by_directory[parts[0]].append(relative)
    for directory, markdown_paths in markdown_by_directory.items():
        if not markdown_paths:
            errors.append(f"{directory}/: must contain at least one Markdown file")
    for relative in sorted(REQUIRED_TEMPLATES - set(relative_paths)):
        errors.append(f"{relative}: required initial template is missing")
    return errors


def git_output(root: Path, args: list[str]) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=True)
    return result.stdout


def archive_paths(root: Path) -> list[str]:
    # Use tracked files in a repository, including only intended published files.
    # Before initialization, support checking a newly generated local scaffold.
    if (root / ".git").exists():
        return [value for value in git_output(root, ["ls-files", "-z"]).split("\0") if value]
    return [path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() or path.is_symlink()]


def check_deletions(root: Path, base: str) -> list[str]:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", base):
        return ["--base must be a full 40-character commit SHA"]
    removed = git_output(root, ["diff", "--name-only", "--diff-filter=D", "-z", base, "HEAD", "--"])
    return [f"{path}: deleting an initial core template is blocked; archive its contents instead"
            for path in removed.split("\0") if path in REQUIRED_TEMPLATES]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--base", help="Optional PR base commit SHA; disallow deletion of initial core templates")
    args = parser.parse_args(argv)
    try:
        errors = validate_paths(args.root, archive_paths(args.root))
        if args.base:
            errors.extend(check_deletions(args.root, args.base))
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Archive validation could not finish: {error}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Archive validation passed: structure, AI tags, size, symlinks, and obvious credential patterns.")
    print("This is a format/heuristic check, not verification of personal facts or publication consent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
