"""Bracos no FR CONSTRUIDO DO ZERO, um mecanismo por vez, motor inteiro (13/09).

Pergunta do usuario: "como podemos aumentar a % da subunidade em um curso construido do 0?". O FR do zero e o unico
curso construido so com as fontes do professor (stash do Moodle pelo caminho da UI, 0 chamadas). Cada braco copia a
base para `.frzero/<braco>`, aplica UM mecanismo por monkeypatch (o codigo do produto nao muda), reprocessa e mede
com `mede_fr_sem_gold.py` (primario incluso).

BRACOS (mecanismo fixado ANTES de medir; nenhum parametro ajustado por material):
  base       nada. Tem que reproduzir o baseline (6/18 primario) antes de qualquer braco valer.
  label      a subunidade le o `moodle_label` com o peso do TITULO (3.8). `entry_signals.py:173` ja coleta; o scorer
             de subunidade (`index.py:1797`) nunca le. So o caminho da subunidade: unidade e bloco nao mudam.
  sem2a      desliga a 2a passada inteira (`resolver_apply.propagar_vocabulario_por_headings` vira no-op). E GROSSO:
             leva junto a regra do titulo e a da secao. Mede o custo/beneficio da passada como bloco.
  sempartes  so tira as partes do rotulo composto (`_partes_de_rotulo` -> {}), fonte da rota `rotulo-decomposto`.
  sempropag  so tira a propagacao de tokens de heading (`_tokens_headings` -> set()); partes, titulo e secao continuam.
             Medido 13/09: FR do zero 6 -> 8/18 primario, mas nos 7 cursos saldo ZERO (5 ganhos, 5 perdas) — handoff §34.

GUARDAS: tripwire no Gemini e em `socket.connect`, contados; `TUTOR_NO_VOCAB_COMPILE=1`; voter desligado; perfil do FR
forcado (o sandbox nao esta no subjects.json). n = 18: diferenca de 1-2 materiais e ruido, e o log diz isso.

Uso: python -B docs/reports/_harness-2026-09-04/c1-3/braco_frzero_13-09.py --braco base
"""
import argparse
import collections
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.utils.helpers  # noqa: F401,E402  (.env)
from src.builder.runtime import gemini_client  # noqa: E402
import reprocess_assignments as ra  # noqa: E402

BASE = GEN / ".frzero" / "base"
CALLS = collections.Counter()


def _bloqueado(*a, **k):
    CALLS["gemini"] += 1
    raise RuntimeError("Gemini bloqueado (tripwire)")


def _rede(*a, **k):
    CALLS["socket"] += 1
    raise RuntimeError("REDE BLOQUEADA (tripwire)")


def aplica_braco(braco):
    from src.builder import engine as eng
    import src.builder.routing.resolver_apply as rap
    if braco == "label":
        orig = eng._auto_map_entry_subtopic

        def com_label(entry, taxonomy, markdown_text, **kw):
            ml = " ".join(str(entry.get("moodle_label") or "").split())
            if ml:
                CALLS["label_injetado"] += 1
                entry = dict(entry)
                entry["title"] = f"{entry.get('title') or ''} {ml}".strip()
            return orig(entry, taxonomy, markdown_text, **kw)
        eng._auto_map_entry_subtopic = com_label
    elif braco == "sem2a":
        def nada(*a, **k):
            CALLS["2a_desligada"] += 1
            return 0
        rap.propagar_vocabulario_por_headings = nada
    elif braco == "sempartes":
        def sem_partes(*a, **k):
            CALLS["partes_desligadas"] += 1
            return {}
        rap._partes_de_rotulo = sem_partes
    elif braco == "sempropag":
        # So a propagacao de TOKENS DE HEADING (a 1a fonte de alias da 2a passada) sai: sem tokens, `owners` fica vazio e
        # `extra` so recebe as partes do rotulo. Titulo e secao continuam. Mecanismo marcado como fragil antes do FR do zero
        # (handoff §3e: `propagado-headings` 51,4% de precisao) — nao escolhido olhando estes 18.
        def sem_tokens(*a, **k):
            CALLS["propagacao_desligada"] += 1
            return set()
        rap._tokens_headings = sem_tokens


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--braco", choices=["base", "label", "sem2a", "sempartes", "sempropag"], required=True)
    a = ap.parse_args(argv)

    dst = GEN / ".frzero" / a.braco
    if a.braco != "base":
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(BASE, dst)
    else:
        dst = GEN / ".frzero" / "base-reprocessada"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(BASE, dst)

    gemini_client.get_gemini_client = lambda config=None: None
    gemini_client.GeminiClient.__init__ = _bloqueado
    _merge = ra._merge_profile_flags

    def sem_voter(options, profile):
        _merge(options, profile)
        options["use_llm_voter"] = False
    ra._merge_profile_flags = sem_voter

    from src.models.core import SubjectStore
    store = SubjectStore()
    sp = next(store.get(n) for n in store.names() if getattr(store.get(n), "slug", "") == "fundamentos-de-redes-de-computadores")
    store.find_by_repo_root = lambda root: sp

    aplica_braco(a.braco)
    socket.socket.connect = _rede
    socket.create_connection = _rede

    t0 = time.time()
    ra.reprocess(dst, [], store=store)
    print(f"[{a.braco}] reprocess {time.time() - t0:.0f}s · contadores: {dict(CALLS) or '{}'}")
    if a.braco != "base" and not any(k in CALLS for k in ("label_injetado", "2a_desligada", "partes_desligadas", "propagacao_desligada")):
        print(f"[{a.braco}] ATENCAO: o monkeypatch NAO foi exercido — o braco mediria a base. Resultado invalido.")
    print("n = 18 no primario: diferenca de 1-2 materiais e ruido.\n")
    r = subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("mede_fr_sem_gold.py")), str(dst)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout)
    if r.returncode:
        print("ERRO no medidor:", r.stderr[-2000:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
