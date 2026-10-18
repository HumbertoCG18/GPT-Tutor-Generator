# tests/test_motor_sibling.py
"""Irmão numerado no card (2026-08-25): entry SEM texto herda o bloco do irmão
com texto que partilha card + radical + número (ES2 `roteiro4.zip` <-
`Roteiro4_circuitbreaker.pdf`). Censo nos 5 cursos: 8 grupos com gold, 8 concordam."""
import json

from src.builder.routing.motor.apply import TEMPORAL_KEYS, apply_anchor_engine


def _repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "course" / ".timeline_index.json").write_text(json.dumps({"blocks": [
        {"id": "bloco-01", "block_uuid": "u-1", "period_start": "2026-03-01",
         "sessions": [{"date": "2026-03-02", "label": "discovery"}]},
        {"id": "bloco-02", "block_uuid": "u-2", "period_start": "2026-03-08",
         "sessions": [{"date": "2026-03-09", "label": "circuit breaker"}]},
    ]}), encoding="utf-8")
    (repo / "course" / ".card_block_map.json").write_text(json.dumps(
        {"Microsserviços": {"source": "manual", "block_ids": ["bloco-01", "bloco-02"]}}),
        encoding="utf-8")
    (repo / "course" / ".lessons_index.json").write_text(json.dumps({"by_date": {}}), encoding="utf-8")
    return repo


def _pdf(pin=None):
    e = {"id": "roteiro4-circuitbreaker", "title": "Roteiro4_circuitbreaker", "category": "material-de-aula",
         "file_type": "pdf", "source_section": "Microsserviços", "computed_block_id": "u-2"}
    if pin:
        e["manual_timeline_block_id"] = pin
    return e


def _zip():
    return {"id": "roteiro4", "title": "roteiro4", "category": "codigo-professor",
            "file_type": "zip", "source_section": "Microsserviços", "computed_block_id": "u-1"}


def _md(e):
    return "circuit breaker resilience" if e["id"] == "roteiro4-circuitbreaker" else ""


def test_zip_sem_texto_herda_bloco_do_irmao_numerado(tmp_path):
    entries = [_pdf(pin="u-2"), _zip()]
    apply_anchor_engine(entries, _repo(tmp_path), "ES2", markdown_fn=_md)
    z = entries[1]
    assert z["temporal_block_id"] == "u-2"
    assert z["temporal_block_method"] == "irmao-card"
    assert z["temporal_block_provider"] == "irmao-card"


def test_sem_irmao_com_texto_nao_herda(tmp_path):
    entries = [_zip()]                       # sozinho: cascata normal decide (janela do card)
    apply_anchor_engine(entries, _repo(tmp_path), "ES2", markdown_fn=_md)
    assert entries[0].get("temporal_block_method") != "irmao-card"


def test_irmao_de_outro_card_nao_conta(tmp_path):
    pdf = _pdf(pin="u-2"); pdf["source_section"] = "Outro card"
    entries = [pdf, _zip()]
    apply_anchor_engine(entries, _repo(tmp_path), "ES2", markdown_fn=_md)
    assert entries[1].get("temporal_block_method") != "irmao-card"


def test_entry_com_texto_decide_sozinha(tmp_path):
    z = _zip()
    entries = [_pdf(pin="u-2"), z]
    apply_anchor_engine(entries, _repo(tmp_path), "ES2", markdown_fn=lambda e: "texto proprio")
    assert z.get("temporal_block_method") != "irmao-card"
