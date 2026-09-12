"""Aplica no PRODUTO a correcao do ES2 diagnosticada em 07/09 e reprocessa (tripwire, 0 chamadas).

Cadeia da falha (verificada passo a passo, ver `corrige_curadoria_es2.log` e o tracker):
  1. `.timeline_curation.json` pina o bloco-04 (`8a2e86f0`) na unidade 02 — commit `b06b264` de 10/08, "4 pinos
     gold-backed". O pino contradiz os DOIS golds do user (unidade e subunidade), que dizem unidade 01 para os 6
     materiais desse bloco: e residuo de uma versao antiga do gold, nao uma decisao do professor.
  2. `.glossary_curation.json` (26/08, "proposto-claude a partir de subunit_gt_ES2") poe `service discovery`,
     `name server`, `service registry`, `API gateway`, `gateway` sob 2.7 (unidade 02). O DP posicional casa esses
     tokens com os labels do cronograma ("microservicos no spring discovery", "... api gateway") e da ao bloco-04
     afinidade u02=3 x u01=0.
  3. Os 6 materiais do bloco-04 herdam a unidade 02 (`herdada_do_bloco`) e a subunidade cai em 2.7.
As duas correcoes sao necessarias: so (2) nao muda nada (o pino sobrepoe o DP; medido 21/28 -> 21/28); so (1) devolve
a unidade 02 (a afinidade ainda aponta u02).
Justificativa de (2) independente do gold: o rotulo do professor separa 1.5 "arquitetura orientada a microsservicos" de
2.7 "integracao e IMPLANTACAO"; e o cronograma poe discovery (10/04) e api gateway (17/04) antes da P1 (08/05), com
circuit breaker/conteineres/filas/autenticacao depois.
Medido na copia: unidade 21/28 -> 28/28 · subunidade 21/28 -> 27/28 · fila 12 -> 11 · conf-err 3 -> 1, zero perdas.
Uso: aplica_correcao_es2.py
"""
import json
import os
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
ROOT = GEN.parent / "Engenharia-Software-2-Tutor"
BLOCO4 = "8a2e86f0-fb4a-4487-86ec-07e74c73d88a"
MOVER = ["service discovery", "name server", "service registry", "API gateway", "gateway"]
TIRAR = ["microsserviço de câmbio"]
K27 = "2.7 Estudo de Caso: integração e implantação de microsserviços"
K15 = "1.5 Estudo de caso: arquitetura orientada a microsserviços"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GEN.parent)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (aplica_correcao_es2)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402

cur = ROOT / "course/.glossary_curation.json"
d = json.loads(cur.read_text(encoding="utf-8"))
d[K27]["synonyms"] = [s for s in d[K27]["synonyms"] if s not in MOVER and s not in TIRAR]
d[K15]["synonyms"] = sorted(set(d[K15]["synonyms"]) | set(MOVER))
d["_nota"] = str(d.get("_nota", "")) + (
    " | 2026-09-07: service discovery / name server / service registry / API gateway / gateway movidos de 2.7 para 1.5. "
    "Justificativa do PROFESSOR, nao do gold: 1.5 e 'arquitetura orientada a microsservicos' e 2.7 e 'integracao e "
    "IMPLANTACAO'; o cronograma poe discovery (10/04) e api gateway (17/04) antes da P1 (08/05), e circuit breaker / "
    "conteineres / filas / autenticacao depois. 'microsservico de cambio' tirado de 2.7 por estar tambem em 1.5 "
    "(alias que serve a dois topicos nao discrimina).")
cur.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("glossary_curation corrigido")

tc = ROOT / "course/.timeline_curation.json"
c = json.loads(tc.read_text(encoding="utf-8"))
if (c.get("blocks") or {}).get(BLOCO4, {}).pop("manual_unit_slug", None):
    if not c["blocks"][BLOCO4]:
        c["blocks"].pop(BLOCO4)
    c["_nota"] = ("2026-09-07: pino de unidade do bloco-04 (8a2e86f0, aulas de 10/04 'discovery' e 17/04 'api gateway') "
                  "REMOVIDO. Foi criado em 10/08 (b06b264, '4 pinos gold-backed') e contradiz os dois golds atuais, que "
                  "poem os 6 materiais desse bloco na unidade 01. Sem o pino, o DP posicional decide u01 (conf 0,8). "
                  "Os pinos dos blocos 07/09/10 ficam: concordam com o automatico.")
    tc.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
    print("pino do bloco-04 removido")

ra.reprocess(ROOT, [])
print("reprocess do ES2 feito")
