"""OS TRES EIXOS COM O MOTOR COMPLETO, por configuracao (12/09 noite, pedido do usuario).

Ate agora o regime "cru" so tinha numero de SUBUNIDADE: o replay recalcula `computed_subunit_slug` e HERDA
`computed_unit_slug` / `temporal_block_id` do manifest do produto. Entao unidade e bloco no cru nunca foram medidos.
Aqui o motor roda INTEIRO (`reprocess_assignments.reprocess`) em copia, uma configuracao por vez, e os 3 eixos sao
medidos na copia.

CONFIGURACOES
  nu          sem curadoria manual (pinos, timeline, card_block_map, glossario manual) e SEM o sidecar do vocab LLM
  regua       SEM o sidecar do vocab LLM, mas COM a curadoria humana  (= o que a regua chama de "cru")
  vocab       COM o sidecar do vocab LLM e com a curadoria humana     (isola o efeito do voter, que fica OFF nas tres)
  (o PRODUTO em disco e a 4a configuracao e ja esta medido: voter ligado)

GUARDAS
  - Copia em `.motor3eixos/`, NUNCA em `.ablacao/` (que e a regua congelada) nem nos tutores-produto.
  - `use_llm_voter=False` nas tres, como o `motor_puro.py` faz.
  - REDE BLOQUEADA no processo: qualquer tentativa de chamada levanta RuntimeError em vez de gastar credito.
  - `TUTOR_NO_VOCAB_COMPILE=1` nas configuracoes sem vocab.

Uso:
    python -B docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py --config nu --cursos TCC   # piloto
    python -B docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py --config regua             # os 7
    python -B docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py --so-medir --config nu     # so remede
"""
import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
ORIG = GEN.parent
DEST = GEN / ".motor3eixos"
os.chdir(GEN)
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(ORIG)

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}


def bloqueia_rede():
    """Qualquer chamada de rede vira erro. E a prova de que a medicao nao gastou credito."""
    def _nao(*a, **k):
        raise RuntimeError("REDE BLOQUEADA: a medicao dos 3 eixos nao pode chamar API")
    socket.socket.connect = _nao
    socket.create_connection = _nao


def prepara(sig, config):
    import ablacao_rapida as ab
    src, dst = ORIG / NOMES[sig], DEST / NOMES[sig]
    ab.sync(src, dst)
    if config == "nu":
        ab.ablate(dst, keep_llm_vocab=False)
        return
    # 'regua' e 'vocab' mantem a curadoria humana: so mexem no sidecar do LLM.
    llm = dst / "course/.glossary_curation.llm.json"
    off = llm.with_name(llm.name + ".off")
    if config == "regua":
        if llm.exists():
            if off.exists():
                off.unlink()
            llm.rename(off)
    else:  # vocab
        if off.exists() and not llm.exists():
            off.rename(llm)


def taxonomia_sem_llm(sig):
    """Para 'regua' e 'nu': tira da taxonomia JA COMPILADA os aliases que vieram do sidecar do LLM.

    Esconder o sidecar nao basta — os sinonimos ja estao FUNDIDOS em `course/.content_taxonomy.json` e no GLOSSARY.md.
    E o mesmo veto do `sem_llm` do replay, so que persistido na copia antes do reprocess.
    """
    from src.builder.core.vocabulary_compile import _norm
    dst = DEST / NOMES[sig]
    fonte = ORIG / NOMES[sig] / "course/.glossary_curation.llm.json"
    if not fonte.exists():
        return 0
    d = json.loads(fonte.read_text(encoding="utf-8"))
    vet = {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}
    p = dst / "course/.content_taxonomy.json"
    if not p.exists() or not vet:
        return 0
    tax = json.loads(p.read_text(encoding="utf-8"))
    n = 0
    for u in tax.get("units", []) or []:
        for t in u.get("topics", []) or []:
            antes = list(t.get("aliases") or [])
            depois = [a for a in antes if _norm(a) not in vet]
            n += len(antes) - len(depois)
            t["aliases"] = depois
    p.write_text(json.dumps(tax, ensure_ascii=False, indent=2), encoding="utf-8")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", choices=["nu", "regua", "vocab"], required=True)
    ap.add_argument("--cursos", default="", help="subconjunto, ex.: TCC,SO (default: os 7)")
    ap.add_argument("--so-medir", action="store_true", help="pula sync/ablacao/reprocess e so remede a copia")
    a = ap.parse_args(argv)
    sigs = [s.strip() for s in a.cursos.split(",") if s.strip()] or list(NOMES)

    if a.config in ("nu", "regua"):
        os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
    else:
        os.environ.pop("TUTOR_NO_VOCAB_COMPILE", None)

    if not a.so_medir:
        import reprocess_assignments as ra
        _merge = ra._merge_profile_flags

        def sem_voter(options, profile):
            _merge(options, profile)
            options["use_llm_voter"] = False       # igual ao motor_puro.py
        ra._merge_profile_flags = sem_voter

        t0 = time.time()
        for sig in sigs:
            prepara(sig, a.config)
            n = taxonomia_sem_llm(sig) if a.config in ("nu", "regua") else 0
            print(f"  [{a.config}] {sig}: copia pronta{f', {n} aliases do LLM vetados na taxonomia' if n else ''}", flush=True)
        bloqueia_rede()   # so depois do robocopy (que e local, mas o guard e por processo)
        for sig in sigs:
            t1 = time.time()
            ra.reprocess(DEST / NOMES[sig], [])
            print(f"  [{a.config}] {sig}: reprocess {time.time() - t1:.0f}s", flush=True)
        print(f"reprocess x{len(sigs)} em {time.time() - t0:.0f}s (rede bloqueada: 0 chamadas)", flush=True)

    print()
    print(f"=== 3 EIXOS — configuracao '{a.config}' (voter OFF), copia em {DEST} ===")
    os.environ["TUTOR_REPOS_DIR"] = str(DEST)
    import subprocess
    r = subprocess.run([sys.executable, "-B", str(GEN / "docs/reports/_harness-2026-09-04/c1-3/mede_3eixos_12-09.py"),
                        "--raiz", str(DEST), "--cursos", ",".join(sigs)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout)
    if r.returncode:
        print("ERRO no medidor:", r.stderr[-3000:])
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
