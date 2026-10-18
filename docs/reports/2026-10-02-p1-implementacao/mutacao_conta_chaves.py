"""Mutação em memória (sem tocar arquivo): `_divisores_de_frase` conta CHAVES em vez de tópicos. Os testes do reforço têm
de falhar. Uso: python -B mutacao_conta_chaves.py (cwd = raiz da worktree)."""
import sys

import pytest

sys.path.insert(0, ".")
from src.builder.timeline import index as IX  # noqa: E402


def conta_chaves(topicos):
    chaves = [list(IX._frases_do_topico(IX._collapse_ws(str(t.get("topic_label", "") or "")),
                                        [str(a) for a in (t.get("aliases", []) or []) if IX._collapse_ws(str(a))],
                                        IX._collapse_ws(str(t.get("topic_slug", "") or "")))) for t in topicos]
    todas = [q for ks in chaves for q in ks]
    return {k: sum(1 for q in todas if IX._matches_normalized_phrase(q, k)) for k in dict.fromkeys(todas)}


IX._divisores_de_frase = conta_chaves
rc = pytest.main(["tests/test_p1_frases_compartilhadas.py", "-q", "-p", "no:cacheprovider",
                  "-k", "varias_chaves or divisores_contam"])
print("exit pytest sob mutação:", rc, "(esperado != 0)")
sys.exit(0 if rc != 0 else 1)
