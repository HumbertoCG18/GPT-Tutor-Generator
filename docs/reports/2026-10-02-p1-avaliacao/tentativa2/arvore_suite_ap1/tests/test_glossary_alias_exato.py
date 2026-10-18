# tests/test_glossary_alias_exato.py
"""R8 (2026-08-26): termo do glossario casava topico por CONTENCAO. "3.3 Algoritmos
de escalonamento" contem "escalonamento", entao o termo E seus sinonimos (FCFS,
SJF...) entravam tambem no topico "Escalonamento" — os dois empatavam (SO 51,9 x
51,4) e o primeiro da lista vencia. Mesmo no TCC ("2.3 Variacoes de Maquinas de
Turing" -> alias de "Maquinas de Turing"). Termo numerado casa EXATO pelo nucleo;
contencao so para termo sem numeracao."""
from src.builder import engine

PLAN = """
Unidade 02: Gerência do Processador
3.1 Conceitos básicos
3.2 Escalonamento
3.3 Algoritmos de escalonamento
"""
GLOSSARY = """## 3.2 Escalonamento
**Sinônimos aceitos:** escalonador
**Aparece em:** Unidade 02 — Gerência do Processador

## 3.3 Algoritmos de escalonamento
**Sinônimos aceitos:** FCFS, SJF
**Aparece em:** Unidade 02 — Gerência do Processador

## Conceitos de escalonamento
**Sinônimos aceitos:** teoria
**Aparece em:** Unidade 02 — Gerência do Processador
"""


def _topics():
    tax = engine._build_content_taxonomy(PLAN, "", GLOSSARY)
    return {t["slug"]: t["aliases"] for u in tax["units"] for t in u["topics"]}


def test_termo_numerado_so_entra_no_topico_de_nucleo_exato():
    by = _topics()
    assert "FCFS" in by["algoritmos-de-escalonamento"]
    assert "3.3 Algoritmos de escalonamento" in by["algoritmos-de-escalonamento"]
    assert "FCFS" not in by["escalonamento"]
    assert "3.3 Algoritmos de escalonamento" not in by["escalonamento"]
    assert "escalonador" in by["escalonamento"] and "escalonador" not in by["algoritmos-de-escalonamento"]


def test_termo_sem_numeracao_mantem_contencao():
    by = _topics()
    # "Conceitos de escalonamento" (sem codigo) contem "escalonamento" -> segue como antes
    assert "teoria" in by["escalonamento"]
