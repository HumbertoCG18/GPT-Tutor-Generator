from __future__ import annotations

NO_SUBJECT_SENTINEL = "(nenhuma)"


def default_source_label(active_subject_name: str | None) -> str:
    """Texto curto indicando de onde vêm os padrões (modo/OCR) exibidos.
    Matéria ativa → 'Padrões da matéria «<nome>»'; sem matéria → global."""
    name = (active_subject_name or "").strip()
    if not name or name == NO_SUBJECT_SENTINEL:
        return "Padrões globais (Configurações)"
    return f"Padrões da matéria «{name}»"
