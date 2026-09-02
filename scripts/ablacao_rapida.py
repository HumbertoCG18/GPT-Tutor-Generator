"""Ablacao "motor nu" RAPIDA: em COPIA dos repos-tutor, em paralelo, sem tocar os originais.

    python scripts/ablacao_rapida.py                 # nu: zera curadoria nas copias, reprocessa os 5, mede
    python scripts/ablacao_rapida.py --curado        # gate: reprocessa as copias SEM ablacao e exige 0 campos vs original
    python scripts/ablacao_rapida.py --repos MF,TCC  # subconjunto
    python scripts/ablacao_rapida.py --jobs 2        # menos paralelismo (API do LLM reclamando)
    python scripts/ablacao_rapida.py --fresh         # apaga as copias antes (senao: sync incremental)

Por que copia: os derivados (.timeline_index etc.) sao ignorados pelo git; restaurar in-place exigia
git checkout + reprocess de novo (ciclo duplo, ~12 min). Na copia nao ha o que restaurar.
Por que o cache de votos da copia persiste: cada ablacao re-votaria as janelas nuas (custo + ruido).
Perfil da disciplina: casado pelo repo ORIGINAL (env TUTOR_REPOS_ORIG, ver reprocess_assignments).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

GEN = Path(__file__).resolve().parents[1]
ORIG = GEN.parent
REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
COPY_DIR = Path(os.environ.get("TUTOR_REPOS_COPY") or (GEN / ".ablacao"))
# raw/, staging/ e content/images ficam: sem eles image_curation muda em todos os repos e o MF perde entries (gate 2026-08-26).
EXCLUDE_DIRS = (".git", "build", "__pycache__", ".deeptutor")
KEEP_IN_COPY = ("material_curation.json",)  # cache de votos nu acumula entre rodadas


def sync(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    cmd = ["robocopy", str(src), str(dst), "/E", "/XD", *EXCLUDE_DIRS, "/XF", "*.bak", "/XJD", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:1", "/W:1"]
    for f in KEEP_IN_COPY:
        if (dst / f).exists():
            cmd += ["/XF", f]
    rc = subprocess.run(cmd, capture_output=True, text=True).returncode
    if rc >= 8:
        raise SystemExit(f"robocopy falhou ({rc}) em {src.name}")


def ablate(repo: Path, keep_llm_vocab: bool = False) -> int:
    """Zera curadoria MANUAL na copia. keep_llm_vocab (motor_puro --com-vocab): o vocabulario
    compilado por LLM (`.glossary_curation.llm.json`, produto, nao curadoria) fica; senao e
    escondido (`.off`) para a regua "puro" medir SEM vocabulario, e restaurado no modo com."""
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8")); n = 0
    for e in m["entries"]:
        for k in ("manual_timeline_block_id", "manual_unit_slug", "manual_subunit_slug"):
            if e.get(k):
                e[k] = ""; n += 1
    (repo / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    cp = repo / "course/.timeline_curation.json"
    if cp.exists():
        cur = json.loads(cp.read_text(encoding="utf-8"))
        cp.write_text(json.dumps({"version": cur.get("version", 1), "blocks": {}}, ensure_ascii=False, indent=2), encoding="utf-8")
    cb = repo / "course/.card_block_map.json"
    if cb.exists():
        d = json.loads(cb.read_text(encoding="utf-8"))
        d = {k: v for k, v in d.items() if not (isinstance(v, dict) and v.get("source") == "manual")}
        cb.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    sc = repo / "course/.glossary_curation.json"
    if sc.exists():
        sc.unlink()
    llm = repo / "course/.glossary_curation.llm.json"; off = llm.with_name(llm.name + ".off")
    if keep_llm_vocab and off.exists():
        if llm.exists():
            off.unlink()          # sync ja trouxe o do original: o .off e orfao
        else:
            off.rename(llm)
    elif not keep_llm_vocab and llm.exists():
        if off.exists():
            off.unlink()
        llm.rename(off)
    return n


def reprocess_parallel(repos: list[Path], jobs: int) -> None:
    env = {**os.environ, "TUTOR_REPOS_ORIG": str(ORIG), "PYTHONIOENCODING": "utf-8", "TUTOR_NO_VOCAB_COMPILE": "1"}
    pending = list(repos); running: list[tuple[Path, subprocess.Popen]] = []
    while pending or running:
        while pending and len(running) < jobs:
            r = pending.pop(0)
            p = subprocess.Popen([sys.executable, str(GEN / "scripts/reprocess_assignments.py"), str(r)],
                                 cwd=str(GEN), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            running.append((r, p))
        for r, p in list(running):
            if p.poll() is not None:
                out = p.stdout.read() if p.stdout else ""
                ok = [l for l in out.splitlines() if l.startswith("[ok]")]
                bad = [l for l in out.splitlines() if "Traceback" in l or "Error" in l]
                print(f"  {r.name}: {'; '.join(ok) or 'sem [ok]'}{'  !! ' + bad[-1] if bad else ''}", flush=True)
                running.remove((r, p))
        time.sleep(0.5)


def diff_fields(a_path: Path, b_path: Path) -> list[tuple[str, str]]:
    a = {e["id"]: e for e in json.loads(a_path.read_text(encoding="utf-8"))["entries"]}
    b = {e["id"]: e for e in json.loads(b_path.read_text(encoding="utf-8"))["entries"]}
    out = [(k, f) for k in a for f in a[k] if f != "updated_at" and a[k].get(f) != b.get(k, {}).get(f)]
    out += [(k, "ENTRY_SUMIU") for k in b if k not in a] + [(k, "ENTRY_NOVA") for k in a if k not in b]
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--curado", action="store_true", help="gate: sem ablacao; copia reprocessada deve == original")
    ap.add_argument("--repos", default="MF,SO,IA,ES2,TCC")
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--no-sync", action="store_true", help="reusa as copias como estao (ex.: so re-medir)")
    args = ap.parse_args(argv)
    sigs = [s.strip() for s in args.repos.split(",") if s.strip()]
    if args.fresh and COPY_DIR.exists():
        shutil.rmtree(COPY_DIR)
    t0 = time.time()
    repos = []
    for sig in sigs:
        src, dst = ORIG / REPO[sig], COPY_DIR / REPO[sig]
        if not args.no_sync:
            sync(src, dst)
        if not args.curado and not args.no_sync:
            n = ablate(dst)
            print(f"  [nu] {sig}: {n} pinos zerados; curadoria, cards manuais e sidecar removidos")
        repos.append(dst)
    print(f"sync+ablacao: {time.time() - t0:.0f}s", flush=True)
    t1 = time.time()
    reprocess_parallel(repos, args.jobs)
    print(f"reprocess x{len(repos)} (jobs={args.jobs}): {time.time() - t1:.0f}s", flush=True)
    env = {**os.environ, "TUTOR_REPOS_DIR": str(COPY_DIR), "PYTHONIOENCODING": "utf-8"}
    if args.curado:
        total = 0
        for sig in sigs:
            d = diff_fields(COPY_DIR / REPO[sig] / "manifest.json", ORIG / REPO[sig] / "manifest.json")
            total += len(d)
            print(f"  gate {sig}: {len(d)} campos diferentes vs original {sorted(set(f for _, f in d))[:6]}")
        print("GATE:", "OK — copia == original" if total == 0 else f"FALHOU — {total} campos")
        return 0 if total == 0 else 1
    ev = subprocess.run([sys.executable, str(GEN / "scripts/eval_eixos.py")], cwd=str(GEN), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("\n".join(l for l in ev.stdout.splitlines() if l.startswith("TOTAL") or l.startswith("curso") or l[:3].strip() in sigs))
    er = subprocess.run([sys.executable, str(GEN / "scripts/erros_motor_nu.py")], cwd=str(GEN), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(er.stdout)
    print(f"total: {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
