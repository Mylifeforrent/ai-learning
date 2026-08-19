#!/usr/bin/env python3
"""Create a review-ready skill scaffold."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALLOWED_RESOURCES = {"scripts", "references", "assets"}

SKILL_TEMPLATE = """---
name: {skill_name}
description: [State what this skill does and when to use it. Include representative request patterns and boundaries.]
---

# {title}

## Goal
[State the repeated problem this skill solves and the outcome it should stabilize.]

## Workflow
1. Confirm the input and task boundary.
2. Classify the request into the right branch.
3. Use scripts, references, or assets as needed.
4. Execute the smallest viable path.
5. Validate the result.
6. Report outcome, risks, and next steps.

## Decision Tree
- If the request is [type A], run `scripts/...`
- If the request is [type B], read `references/...`
- If the request is [type C], use `assets/...`

## Constraints
- List non-negotiable rules.
- List preservation requirements.
- List actions that require user confirmation.

## Validation
- Required checks:
- Success criteria:
- First failure checks:

## Resources
- `scripts/...`: when to run
- `references/...`: when to read
- `assets/...`: when to use
"""

OPENAI_YAML_TEMPLATE = """interface:
  display_name: \"{display_name}\"
  short_description: \"{short_description}\"
  default_prompt: \"Use ${skill_name} to handle this repeated workflow as a reusable skill.\"
"""

REFERENCE_TEMPLATE = """# Design Notes

## Trigger Examples
- [Add realistic requests that should trigger this skill]

## Non-Trigger Neighbors
- [Add adjacent requests that should not trigger this skill]

## Branch Details
- [Move optional or branch-specific detail here]
"""

SCRIPT_TEMPLATE = """#!/usr/bin/env python3
\"\"\"Starter script for {skill_name}. Replace or remove it.\"\"\"


def main() -> None:
    print(\"Replace this script with real automation.\")


if __name__ == \"__main__\":
    main()
"""

ASSET_TEMPLATE = """# Output Template

Replace this file with a real asset, template, sample, or starter material.
"""


def normalize(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", normalized)


def title_case(skill_name: str) -> str:
    return " ".join(part.capitalize() for part in skill_name.split("-"))


def ensure_short_description(display_name: str) -> str:
    base = f"Create and review {display_name} skills"
    if len(base) <= 64:
        return base
    compact = f"Design and review {display_name}"
    if len(compact) <= 64:
        return compact
    return compact[:64].rstrip()


def parse_resources(raw: str) -> list[str]:
    if not raw:
        return []
    items = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if item not in ALLOWED_RESOURCES:
            raise ValueError(f"Unknown resource '{item}'. Allowed: {', '.join(sorted(ALLOWED_RESOURCES))}")
        if item not in items:
            items.append(item)
    return items


def write_file(path: Path, content: str, executable: bool = False) -> None:
    path.write_text(content)
    if executable:
        path.chmod(0o755)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a review-ready skill scaffold.")
    parser.add_argument("skill_name", help="New skill name")
    parser.add_argument("--path", required=True, help="Parent directory for the new skill")
    parser.add_argument("--resources", default="references", help="Comma-separated resource dirs to create")
    args = parser.parse_args()

    skill_name = normalize(args.skill_name)
    if not skill_name:
        print("[ERROR] Skill name is empty after normalization.")
        return 1
    if len(skill_name) > 64:
        print("[ERROR] Skill name exceeds 64 characters.")
        return 1

    try:
        resources = parse_resources(args.resources)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1

    parent = Path(args.path).resolve()
    skill_dir = parent / skill_name
    if skill_dir.exists():
        print(f"[ERROR] Target already exists: {skill_dir}")
        return 1

    skill_dir.mkdir(parents=True)
    (skill_dir / "agents").mkdir()

    display_name = title_case(skill_name)
    short_description = ensure_short_description(display_name)

    write_file(skill_dir / "SKILL.md", SKILL_TEMPLATE.format(skill_name=skill_name, title=display_name))
    write_file(
        skill_dir / "agents" / "openai.yaml",
        OPENAI_YAML_TEMPLATE.format(
            display_name=display_name,
            short_description=short_description,
            skill_name=skill_name,
        ),
    )

    if "references" in resources:
        (skill_dir / "references").mkdir()
        write_file(skill_dir / "references" / "design-notes.md", REFERENCE_TEMPLATE)
    if "scripts" in resources:
        (skill_dir / "scripts").mkdir()
        write_file(skill_dir / "scripts" / "example.py", SCRIPT_TEMPLATE.format(skill_name=skill_name), executable=True)
    if "assets" in resources:
        (skill_dir / "assets").mkdir()
        write_file(skill_dir / "assets" / "template.md", ASSET_TEMPLATE)

    print(f"[OK] Created {skill_dir}")
    print("[NEXT] Replace template wording before using the skill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
