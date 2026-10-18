"""A2 (2026-08-27): genericos de UNIDADE calculados por curso (df sobre as unidades do plano), sem lista do MF."""
import os

from src.builder.text.stopwords import (
    TIMELINE_UNIT_NEUTRAL_TOKENS,
    UNIT_STRUCTURAL_TOKENS,
    resolve_unit_generic_tokens,
    unit_generic_tokens_from_units,
)

MF = [("Unidade 01 — Lógica e Verificação Formal", [("Lógica proposicional", 0), ("Verificação de programas", 0)]),
      ("Unidade 02 — Verificação de Programas", [("Lógica de Hoare", 0), ("Verificação formal", 0)]),
      ("Unidade 03 — Verificação de Modelos", [("Lógica temporal", 0), ("Model checking formal", 0)])]
CG = [("Unidade 01 — Introdução ao Processamento Gráfico", [("Origens", 0), ("Algoritmos de rasterização", 0)]),
      ("Unidade 02 — Fundamentos Matemáticos", [("Vetores", 0), ("Algoritmos de detecção de colisão", 0)]),
      ("Unidade 03 — Processamento de Imagens", [("Filtros", 0), ("Algoritmos de segmentação", 0)]),
      ("Unidade 04 — Visualização 2D", [("Recorte", 0), ("Mapeamento", 0)]),
      ("Unidade 05 — Curvas", [("Bézier", 0)])]


def test_df_reproduz_a_lista_do_mf_onde_ela_acerta():
    g = unit_generic_tokens_from_units(MF)
    assert {"logica", "verificacao", "formal"} <= g
    assert "hoare" not in g and "temporal" not in g  # topico raro fica ("programas" esta em 2/3 aqui: generico, correto)


def test_df_nao_mata_topico_raro_de_outra_cadeira():
    g = unit_generic_tokens_from_units(CG)
    assert "fundamentos" not in g and "curvas" not in g
    assert "algoritmos" in g  # 3/5 unidades
    assert UNIT_STRUCTURAL_TOKENS <= g


def test_lista_do_mf_mata_fundamentos_na_cg():
    assert "fundamentos" in TIMELINE_UNIT_NEUTRAL_TOKENS  # o defeito que A2 remove


def test_modos(monkeypatch):
    base = {"xyz"}
    monkeypatch.delenv("UNIT_GENERIC_MODE", raising=False)
    assert resolve_unit_generic_tokens(CG, base) == unit_generic_tokens_from_units(CG)  # default = df
    assert resolve_unit_generic_tokens(CG, base, mode="lista") is None      # lista: cada consumidor usa a sua constante
    assert resolve_unit_generic_tokens(CG, base, mode="df") == unit_generic_tokens_from_units(CG)
    assert resolve_unit_generic_tokens(CG, base, mode="ambos") == frozenset(base | set(unit_generic_tokens_from_units(CG)))
    monkeypatch.setenv("UNIT_GENERIC_MODE", "lista")
    assert resolve_unit_generic_tokens(CG, base) is None


def test_sem_unidades_devolve_so_estruturais():
    assert unit_generic_tokens_from_units([]) == UNIT_STRUCTURAL_TOKENS


def test_nome_do_curso_e_generico_no_modo_df():
    g = resolve_unit_generic_tokens(CG, set(), mode="df", course_name="Computação Gráfica")
    assert {"computacao", "grafica"} <= g
