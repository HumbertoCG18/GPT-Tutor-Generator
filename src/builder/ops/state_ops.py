from __future__ import annotations

import re


def derive_active_unit_slug_from_state(root_dir) -> str:
    state = root_dir / "student" / "STUDENT_STATE.md"
    if not state.exists():
        return ""
    text = state.read_text(encoding="utf-8")
    match = re.search(r"active:\s*\n(?:.*\n)*?\s*unit:\s*(\S+)", text)
    return match.group(1).strip() if match else ""


def ensure_unit_battery_directories(
    root_dir,
    subject_profile,
    *,
    parse_units_from_teaching_plan_fn,
    slugify_fn,
) -> None:
    teaching_plan = getattr(subject_profile, "teaching_plan", "") or ""
    if not teaching_plan:
        return
    batteries_root = root_dir / "student" / "batteries"
    for title, _topics in parse_units_from_teaching_plan_fn(teaching_plan):
        slug = slugify_fn(title)
        if slug:
            (batteries_root / slug).mkdir(parents=True, exist_ok=True)
