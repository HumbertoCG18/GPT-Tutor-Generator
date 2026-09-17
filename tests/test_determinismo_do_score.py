"""O score de bloco nao pode depender do PYTHONHASHSEED.

`entry_vec.keys() & block_vec.keys()` devolve set; a ordem de iteracao de um set
de str muda a cada processo. Somar float nessa ordem dava resultados diferentes
no ultimo ULP entre duas rodadas identicas do reprocess — o bastante pra
`computed_block_confidence` mudar, a `band` flipar na fronteira baixa/media e,
num empate tecnico (TCC aula-06, confianca 0.084), o bloco VENCEDOR trocar.
Medido 2026-08-19: 6 entries do TCC divergiam entre rodadas; com
PYTHONHASHSEED=0, zero. Ver `concept_resolver.overlap_min`.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# pesos variados o bastante pra que a ORDEM da soma mude o resultado em float64
# (o teste abaixo prova isso antes de usar — teste vacuoso nao vale nada)
_TOKENS = {f"token{i:02d}": 0.1 * (i + 1) / 7.0 for i in range(40)}

_SCRIPT = """
import sys
sys.path.insert(0, %r)
from src.builder.routing.concept_resolver import overlap_min
vec = %r
print(repr(overlap_min(vec, dict(vec))))
""" % (str(ROOT), _TOKENS)


def _rodar(seed: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": seed}
    out = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", _SCRIPT],
        capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(ROOT),
    )
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def test_entrada_e_mesmo_sensivel_a_ordem():
    """Guarda contra teste vacuoso: se a soma destes valores fosse invariante a
    ordem, o teste seguinte passaria mesmo com o bug de volta."""
    vals = [_TOKENS[k] for k in _TOKENS]
    assert sum(vals) != sum(reversed(vals))


def test_overlap_independe_do_hashseed():
    saidas = {_rodar(s) for s in ("0", "1", "12345", "99")}
    assert len(saidas) == 1, f"score varia com PYTHONHASHSEED: {saidas}"
