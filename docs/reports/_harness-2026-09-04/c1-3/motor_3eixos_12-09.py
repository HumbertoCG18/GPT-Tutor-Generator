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


TENTATIVAS = []


def bloqueia_rede():
    """Qualquer chamada de rede vira erro E FICA REGISTRADA.

    12/09 tarde, correcao do astra: "terminou sem excecao -> 0 chamadas" NAO e prova. A camada de vocabulario
    (`pedagogical_regeneration.py:104`) CAPTURA a excecao e deixa a execucao continuar, entao uma tentativa bloqueada
    passa despercebida e o driver imprimia "0 chamadas" como texto fixo. Agora o guard conta, e o numero impresso vem
    do contador.
    """
    def _nao(*a, **k):
        import traceback
        TENTATIVAS.append("".join(traceback.format_stack(limit=8)))
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
    else:  # 'vocab' e 'produto': a copia fica igual ao produto; o que muda e o voter
        if off.exists() and not llm.exists():
            off.rename(llm)


def _fontes_do_professor(sig):
    """Texto normalizado do PLANO DE ENSINO + dos headings do acervo. Usado pelo veto por PROVENIENCIA."""
    import re as _re
    from src.builder.text.normalize import normalize_match_text as _N
    from src.utils.helpers import get_app_data_dir
    root = ORIG / NOMES[sig]
    plano = ""
    try:
        d = json.loads((get_app_data_dir() / "subjects.json").read_text(encoding="utf-8"))
        subs = d if isinstance(d, list) else (d.get("subjects") or list(d.values()))
        for s in subs if isinstance(subs, list) else []:
            nome = str((s or {}).get("name") or "")
            if nome and (nome[:10].lower() in NOMES[sig].lower().replace("-", " ")
                         or NOMES[sig].split("-")[0].lower() in nome.lower()):
                plano = str(s.get("teaching_plan") or "")
                break
    except Exception:
        pass
    H = _re.compile(r"^#{1,3}\s+(.+)$", _re.M)
    heads = []
    for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]:
        rel = str(e.get("base_markdown") or "")
        if not rel:
            continue
        p = root / rel
        if p.exists():
            try:
                heads.extend(H.findall(p.read_text(encoding="utf-8", errors="replace"))[:12])
            except Exception:
                pass
    return _N(plano + " | " + " | ".join(heads))


def taxonomia_sem_llm(sig, veto="texto"):
    """Para 'regua' e 'nu': tira da taxonomia JA COMPILADA os aliases que vieram do vocabulario do LLM.

    Esconder o sidecar nao basta — os sinonimos ja estao FUNDIDOS em `course/.content_taxonomy.json`.

    DOIS MODOS (12/09 noite, item do astra: "definir se a ablacao remove a fonte LLM ou qualquer termo coincidente"):
      veto="texto"  (o do replay): tira TODO alias cujo `_norm` esta no sidecar do LLM.
      veto="fonte"  (novo): tira so os que NAO aparecem em fonte do professor (plano de ensino ou headings do acervo).
    Por que o segundo existe: medido em `proveniencia_alias_12-09.log`, dos 544 aliases vetados nos 7 cursos, **341
    tambem aparecem nos headings** e **35 no plano**; so **197 existem exclusivamente no sidecar do LLM**. E o construtor
    da taxonomia (`content_taxonomy.py:603-646`) doa headings como alias INDEPENDENTEMENTE do LLM — entao o veto por
    texto tira aliases que um curso sem LLM teria de qualquer forma, e o regime "cru" fica mais duro que a realidade.
    """
    from src.builder.core.vocabulary_compile import _norm
    import re as _re
    from src.builder.text.normalize import normalize_match_text as _N
    dst = DEST / NOMES[sig]
    fonte = ORIG / NOMES[sig] / "course/.glossary_curation.llm.json"
    if not fonte.exists():
        return 0
    d = json.loads(fonte.read_text(encoding="utf-8"))
    vet = {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}
    p = dst / "course/.content_taxonomy.json"
    if not p.exists() or not vet:
        return 0
    prof = _fontes_do_professor(sig) if veto == "fonte" else ""

    def vem_do_professor(a):
        if not prof:
            return False
        n = _N(a or "")
        return bool(n) and _re.search(r"(^|\s)" + _re.escape(n) + r"(\s|$)", prof) is not None

    tax = json.loads(p.read_text(encoding="utf-8"))
    n = 0
    for u in tax.get("units", []) or []:
        for t in u.get("topics", []) or []:
            antes = list(t.get("aliases") or [])
            depois = [a for a in antes if _norm(a) not in vet or (veto == "fonte" and vem_do_professor(a))]
            n += len(antes) - len(depois)
            t["aliases"] = depois
    p.write_text(json.dumps(tax, ensure_ascii=False, indent=2), encoding="utf-8")
    return n


def zera_cache_de_codigo(sig):
    """Invalida o `code_curation.json` da copia nas configuracoes sem vocabulario.

    12/09 noite, achado do astra e confirmado por mim: o resumo deterministico de codigo (`determ-v3`) usa
    `code_summarization.course_aliases`, que le a taxonomia E o sidecar do LLM — mas o cache e por hash do TEXTO do
    bundle (`compute_entry_hash`), nao dos aliases. Entao vetar aliases NAO invalida o resumo, e o regime "cru" ficava
    com vocabulario de LLM dentro: medido, **202 conceitos** salvos nos 42 registros dos 7 cursos sao aliases que so
    existem por causa do sidecar (CG 134, ES2 45, IA 9, FR 9, MF 5), e 37 dos 42 registros estao no gold de 251.
    Zerando o arquivo, o reprocess regenera os resumos com a taxonomia JA vetada (`synthesize_all_code_entries` e
    deterministico e declara "0 chamadas").
    """
    p = DEST / NOMES[sig] / "code_curation.json"
    if not p.exists():
        return 0
    d = json.loads(p.read_text(encoding="utf-8"))
    n = len(d.get("entries") or {})
    d["entries"] = {}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", choices=["nu", "regua", "vocab", "produto"], required=True)
    ap.add_argument("--cursos", default="", help="subconjunto, ex.: TCC,SO (default: os 7)")
    ap.add_argument("--so-medir", action="store_true", help="pula sync/ablacao/reprocess e so remede a copia")
    ap.add_argument("--veto", choices=["texto", "fonte"], default="texto",
                    help="texto: veta todo alias do sidecar LLM (o do replay) · fonte: preserva os que tambem vem do "
                         "plano de ensino ou dos headings do acervo")
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
        if a.config != "produto":
            ra._merge_profile_flags = sem_voter
        # 'produto' (12/09 noite, pedido do astra): o 4o braco, com voter LIGADO e reprocessado nas MESMAS condicoes.
        # Sem ele, o delta VOCAB -> PRODUTO era atribuido ao voter comparando com um produto SALVO, nao com um braco
        # contemporaneo. A rede continua bloqueada e contada: se o voter rodar de cache, o contador fica em 0; se
        # precisar chamar, o numero diz quantas chamadas o produto exigiria.

        t0 = time.time()
        for sig in sigs:
            prepara(sig, a.config)
            n = taxonomia_sem_llm(sig, a.veto) if a.config in ("nu", "regua") else 0
            z = zera_cache_de_codigo(sig) if a.config in ("nu", "regua") else 0
            print(f"  [{a.config}] {sig}: copia pronta"
                  f"{f', {n} aliases do LLM vetados na taxonomia' if n else ''}"
                  f"{f', cache de {z} resumos de codigo zerado (sera regenerado sem o vocab)' if z else ''}", flush=True)
        bloqueia_rede()   # so depois do robocopy (que e local, mas o guard e por processo)
        for sig in sigs:
            t1 = time.time()
            ra.reprocess(DEST / NOMES[sig], [])
            print(f"  [{a.config}] {sig}: reprocess {time.time() - t1:.0f}s", flush=True)
        print(f"reprocess x{len(sigs)} em {time.time() - t0:.0f}s · "
              f"TENTATIVAS DE REDE BLOQUEADAS: {len(TENTATIVAS)}", flush=True)
        for i, tb in enumerate(TENTATIVAS[:3], 1):
            print(f"  --- tentativa {i} (stack) ---\n{tb}", flush=True)
        # Marcador: a copia guarda UMA configuracao por vez e a seguinte sobrescreve. Sem isto e facil ler a copia
        # achando que ela esta na configuracao anterior (aconteceu em 12/09 com a lista de erros de unidade).
        (DEST / "_CONFIG_ATUAL.txt").write_text(
            a.config + " (veto=" + a.veto + ")\ncursos: " + ",".join(sigs) + "\n", encoding="utf-8")

    print()
    marc = DEST / "_CONFIG_ATUAL.txt"
    if a.so_medir and marc.exists():
        print(f"(a copia em disco esta na configuracao: {marc.read_text(encoding='utf-8').splitlines()[0]})")
    print(f"=== 3 EIXOS — configuracao '{a.config}' (veto={a.veto}, "
          f"voter {'ON' if a.config == 'produto' else 'OFF'}), copia em {DEST} ===")
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
