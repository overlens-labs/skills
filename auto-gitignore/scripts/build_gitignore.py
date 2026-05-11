#!/usr/bin/env python3
"""Build or update a .gitignore from gitignore.io templates, idempotently.

Usage:
    python build_gitignore.py --techs nextjs,node,windows,git --output path/.gitignore

Behavior:
- Fetches the combined gitignore.io template once via the API.
- If `--output` does not exist: writes `## Manual setup\n\n.temp/**\n\n<template>`.
- If it exists with the `# Created by https://www.toptal.com/developers/gitignore/api/...`
  and `# End of ...` markers: replaces ONLY the block between them. Everything outside
  the markers (the user's manual section, plus any tail content) is preserved byte-for-byte.
- If it exists without markers (legacy): appends the new block at the end, after a
  blank line, leaving the legacy content untouched. The agent should preview this case
  with the user before running.

Optional flag --validate prints to stderr any requested techs that are NOT in the
official gitignore.io list (so the caller can drop them before retrying).

Exit codes:
    0 success, 1 network error, 2 invalid techs (when --validate strict), 3 IO error.
"""
from __future__ import annotations
import argparse
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "https://www.toptal.com/developers/gitignore/api"
CREATED_PREFIX = "# Created by https://www.toptal.com/developers/gitignore/api/"
END_PREFIX     = "# End of https://www.toptal.com/developers/gitignore/api/"
MANUAL_HEADER  = "## Manual setup\n\n.temp/**\n"


def fetch(url: str) -> str:
    # gitignore.io rejects requests without a real-looking User-Agent (returns 403)
    req = urllib.request.Request(url, headers={"User-Agent": "auto-gitignore-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"network error: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_template(techs: list[str]) -> str:
    return fetch(f"{API_BASE}/{','.join(techs)}").rstrip() + "\n"


def fetch_supported() -> set[str]:
    raw = fetch(f"{API_BASE}/list")
    return {t.strip() for t in raw.replace("\n", ",").split(",") if t.strip()}


def _is_pattern_line(line: str) -> bool:
    """A real ignore pattern (not a comment, blank line, or negation comment)."""
    s = line.strip()
    return bool(s) and not s.startswith("#")


def dedupe(content: str) -> tuple[str, int]:
    """Remove pattern lines OUTSIDE the gitignore.io block that also appear INSIDE it.

    Rationale: the gitignore.io block is the regenerable source of truth for
    technology-specific patterns. If a legacy `.gitignore` (e.g., from create-next-app)
    already had `.next/` and we append the gitignore.io block, both would carry that
    line. The legacy copy is redundant — remove it, keep the managed one.

    Patterns are compared by exact stripped string. Comments are never touched (so
    `# next.js` heading orphaned by removed patterns just stays — cosmetic, harmless).
    Returns (new_content, lines_removed).
    """
    lines = content.splitlines()
    start = end = None
    for i, line in enumerate(lines):
        if start is None and line.startswith(CREATED_PREFIX):
            start = i
        elif start is not None and line.startswith(END_PREFIX):
            end = i
            break
    if start is None or end is None:
        return content, 0

    block_patterns = {ln.strip() for ln in lines[start + 1:end] if _is_pattern_line(ln)}
    if not block_patterns:
        return content, 0

    out, removed = [], 0
    for i, line in enumerate(lines):
        if start <= i <= end:
            out.append(line)
            continue
        if _is_pattern_line(line) and line.strip() in block_patterns:
            removed += 1
            continue
        out.append(line)

    # Collapse runs of >=3 blank lines (cosmetic cleanup after removal)
    cleaned, blanks = [], 0
    for ln in out:
        if ln.strip() == "":
            blanks += 1
            if blanks <= 2:
                cleaned.append(ln)
        else:
            blanks = 0
            cleaned.append(ln)
    return "\n".join(cleaned).rstrip() + "\n", removed


def merge(existing: str, new_block: str) -> str:
    """Replace the gitignore.io block in `existing` with `new_block`, or append/init."""
    lines = existing.splitlines(keepends=False)
    start = end = None
    for i, line in enumerate(lines):
        if start is None and line.startswith(CREATED_PREFIX):
            start = i
        elif start is not None and line.startswith(END_PREFIX):
            end = i
            break
    if start is not None and end is not None:
        # Replace inclusive [start..end] with new_block lines
        prefix = "\n".join(lines[:start]).rstrip()
        suffix = "\n".join(lines[end + 1:]).lstrip()
        out = prefix + ("\n\n" if prefix else "") + new_block.rstrip() + "\n"
        if suffix:
            out += "\n" + suffix.rstrip() + "\n"
        return out
    # Legacy file with no markers: append after blank line
    base = existing.rstrip()
    return base + "\n\n" + new_block.rstrip() + "\n"


def build(techs: list[str], output: Path, validate: bool, do_dedupe: bool) -> None:
    if validate:
        supported = fetch_supported()
        missing = [t for t in techs if t not in supported]
        if missing:
            print(f"warning: not in gitignore.io list, dropping: {missing}", file=sys.stderr)
            techs = [t for t in techs if t in supported]
    if not techs:
        print("no valid techs to fetch", file=sys.stderr); sys.exit(2)

    template = fetch_template(techs)

    if output.exists():
        existing = output.read_text(encoding="utf-8")
        merged = merge(existing, template)
    else:
        merged = MANUAL_HEADER + "\n" + template

    removed = 0
    if do_dedupe:
        merged, removed = dedupe(merged)

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(merged, encoding="utf-8")
    except OSError as e:
        print(f"io error: {e}", file=sys.stderr); sys.exit(3)
    extra = f", removed {removed} duplicate pattern(s)" if removed else ""
    print(f"wrote {output} ({len(techs)} techs{extra})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--techs", required=True, help="comma-separated gitignore.io tech names")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--validate", action="store_true",
                    help="cross-check techs against gitignore.io's /list endpoint and drop unknown ones")
    ap.add_argument("--no-dedupe", action="store_true",
                    help="skip the final dedup pass (default: remove pattern lines outside the "
                         "gitignore.io block that also appear inside it — e.g., a legacy .next/ "
                         "left over from create-next-app's .gitignore)")
    args = ap.parse_args()
    techs = [t.strip() for t in args.techs.split(",") if t.strip()]
    build(techs, args.output, args.validate, do_dedupe=not args.no_dedupe)


if __name__ == "__main__":
    main()
