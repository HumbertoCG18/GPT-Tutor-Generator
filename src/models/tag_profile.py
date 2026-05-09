from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class LearnedCorrection:
    entry_id: str
    corrected_unit_slug: str
    corrected_subunit_slug: str
    learned_terms: List[str]
    created_at: str

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "corrected_unit_slug": self.corrected_unit_slug,
            "corrected_subunit_slug": self.corrected_subunit_slug,
            "learned_terms": list(self.learned_terms),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearnedCorrection":
        return cls(
            entry_id=str(data.get("entry_id", "")),
            corrected_unit_slug=str(data.get("corrected_unit_slug", "")),
            corrected_subunit_slug=str(data.get("corrected_subunit_slug", "")),
            learned_terms=list(data.get("learned_terms") or []),
            created_at=str(data.get("created_at", "")),
        )


@dataclass
class SubjectTagProfile:
    subject_slug: str
    generated_at: str
    learned_corrections: List[LearnedCorrection] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "subject_slug": self.subject_slug,
            "generated_at": self.generated_at,
            "learned_corrections": [c.to_dict() for c in self.learned_corrections],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SubjectTagProfile":
        corrections = [
            LearnedCorrection.from_dict(c)
            for c in (data.get("learned_corrections") or [])
            if isinstance(c, dict)
        ]
        return cls(
            subject_slug=str(data.get("subject_slug", "")),
            generated_at=str(data.get("generated_at", "")),
            learned_corrections=corrections,
        )


def load_tag_profile(course_dir: Path) -> Optional[SubjectTagProfile]:
    path = course_dir / ".tag_profile.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SubjectTagProfile.from_dict(data)
    except Exception:
        return None


def save_tag_profile(course_dir: Path, profile: SubjectTagProfile) -> None:
    path = course_dir / ".tag_profile.json"
    path.write_text(
        json.dumps(profile.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
