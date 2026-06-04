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


def extract_entry_learned_terms(entry: dict) -> List[str]:
    """Extract significant tokens from entry dict for subject-local learning."""
    terms: set = set()

    title = str(entry.get("title", "") or "").lower()
    for tok in re.split(r"[^a-z0-9]", title):
        if len(tok) >= 5:
            terms.add(tok)

    for tag in list(entry.get("auto_tags") or []):
        tag_str = str(tag)
        if ":" in tag_str:
            slug = tag_str.split(":", 1)[1]
            if len(slug) >= 4:
                terms.add(slug)

    raw = str(entry.get("raw_target", "") or "").lower()
    stem = Path(raw).stem if raw else ""
    for tok in re.split(r"[^a-z0-9]", stem):
        if len(tok) >= 5:
            terms.add(tok)

    return sorted(terms)[:12]


def record_correction(
    profile: SubjectTagProfile,
    entry: dict,
    *,
    corrected_unit_slug: str,
    corrected_subunit_slug: str = "",
) -> None:
    """Record a user correction into the profile (subject-local only)."""
    if not corrected_unit_slug and not corrected_subunit_slug:
        return

    from datetime import datetime

    entry_id = str(entry.get("id", "") or "")
    learned_terms = extract_entry_learned_terms(entry)

    # Remove previous correction for same entry
    profile.learned_corrections = [
        c for c in profile.learned_corrections if c.entry_id != entry_id
    ]

    profile.learned_corrections.append(
        LearnedCorrection(
            entry_id=entry_id,
            corrected_unit_slug=corrected_unit_slug,
            corrected_subunit_slug=corrected_subunit_slug,
            learned_terms=learned_terms,
            created_at=datetime.utcnow().isoformat(),
        )
    )


def build_learned_unit_boosts(
    profile: Optional[SubjectTagProfile],
    entry: dict,
) -> Dict[str, float]:
    """Return {unit_slug: boost_weight} based on subject-local learned corrections."""
    if not profile or not profile.learned_corrections:
        return {}

    entry_terms = set(extract_entry_learned_terms(entry))
    if not entry_terms:
        return {}

    boosts: Dict[str, float] = {}
    for correction in profile.learned_corrections:
        if not correction.corrected_unit_slug:
            continue
        learned = set(correction.learned_terms or [])
        overlap = entry_terms & learned
        if len(overlap) >= 2 or (len(overlap) == 1 and len(entry_terms) <= 4):
            weight = 1.5 * min(len(overlap), 3)
            slug = correction.corrected_unit_slug
            boosts[slug] = boosts.get(slug, 0.0) + weight

    return boosts


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.85:
        return "alta"
    if confidence >= 0.65:
        return "média"
    if confidence >= 0.45:
        return "baixa"
    return "muito baixa"


def format_unit_explanation_text(
    reasons: List[str],
    confidence: float,
    unit_slug: str = "",
) -> str:
    """Format unit match reasons for a human-readable tooltip."""
    lines: List[str] = []
    for reason in (reasons or []):
        if reason.startswith("winner_score="):
            lines.append(f"pontuação geral: {reason.split('=', 1)[1]}")
        elif reason.startswith("topic_score="):
            lines.append(f"correspondência de tópicos: {reason.split('=', 1)[1]}")
        elif reason.startswith("tag_boost="):
            lines.append(f"boost de tags automáticas: +{reason.split('=', 1)[1]}")
        elif reason == "manual":
            lines.append("atribuição manual pelo usuário")
        elif reason == "ambiguous":
            lines.append("⚠ ambíguo: mais de uma unidade com pontuação similar")

    body = "\n".join(f"- {line}" for line in lines) if lines else "- (sem detalhes disponíveis)"
    header = f"Unidade: {unit_slug}\n" if unit_slug else ""
    return (
        f"{header}Sugerido por:\n{body}\n\n"
        f"Confiança: {_confidence_label(confidence)} ({confidence:.0%})"
    )


def format_subunit_explanation_text(
    reasons: List[str],
    confidence: float,
    unit_slug: str = "",
    subunit_slug: str = "",
) -> str:
    """Format subunit match reasons for a human-readable tooltip."""
    lines: List[str] = []
    for reason in (reasons or []):
        if reason.startswith("winner_score="):
            lines.append(f"pontuação de tópico: {reason.split('=', 1)[1]}")
        elif reason == "manual":
            lines.append("atribuição manual pelo usuário")
        elif reason == "ambiguous":
            lines.append("⚠ ambíguo: mais de um tópico com pontuação similar")
        elif reason.startswith("sem-"):
            lines.append(f"⚠ {reason}")

    if unit_slug:
        lines.append(f"restrito à unidade: {unit_slug}")

    body = "\n".join(f"- {line}" for line in lines) if lines else "- (sem detalhes disponíveis)"
    header = f"Subunidade: {subunit_slug or '(nenhuma)'}\n"
    return (
        f"{header}Sugerido por:\n{body}\n\n"
        f"Confiança: {_confidence_label(confidence)} ({confidence:.0%})"
    )
