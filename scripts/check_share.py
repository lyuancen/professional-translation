#!/usr/bin/env python3
"""Check staged paths before a manual commit; never reads translation content."""

import subprocess
import sys
from pathlib import Path

ALLOWED = {
    ".gitignore", "README.md", "SKILL.md", "agents/openai.yaml",
    "glossary/English 0928.docx", "scripts/glossary.py",
    "scripts/check_share.py", "references/source-guidance.md",
}


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, check=False,
    )
    if result.returncode:
        print("ERROR: run this inside the Git repository", file=sys.stderr)
        return 2
    staged = [part.decode("utf-8", "replace") for part in result.stdout.split(b"\0") if part]
    unexpected = [path for path in staged if path not in ALLOWED]
    if unexpected:
        print("ERROR: unexpected staged paths; remove them before committing:", file=sys.stderr)
        for path in unexpected:
            print(f"  {path}", file=sys.stderr)
        return 1
    print(f"Staged paths checked: {len(staged)}; all are on the share allowlist.")
    print("Review glossary/English 0928.docx manually before publication; this check does not inspect its content.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
