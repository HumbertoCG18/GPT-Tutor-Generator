"""Diagnóstico do CRU-05 (opção 2 da revisão do GPT Pro, 01/10): rastro instrumentado de UMA execução do replay integral,
sem gold. Rodar duas vezes (src da base e src do candidato) e comparar com `compara_mecanismo.py`.

Uso: python -B diag_cru05_mecanismo.py --worktree <raiz do src> --referencia <replay_*.json> --saida <json>
- src fixado na worktree (src.__path__), módulos de replay lidos da principal, dados da principal; nada gravado fora de --saida.
- Instrumentação só em memória (wrappers restaurados): wz2.rodar(pontuar=True) já grava unidade bruta, 1ª passada com
  pontuações de todos os tópicos, chamada da 2ª passada e final; aqui se acrescentam tokens de headings por material,
  vocab_unit, aliases acrescentados (origem e doadores), guarda do título e regra da seção.
- Fidelidade: as decisões finais (bloco/unidade/sub) têm de ser idênticas às de --referencia em todos os IDs; senão,
  saída 1 e o rastro é marcado inconclusivo. Gold não é lido.
"""
import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import socket
import sys
import time
from pathlib import Path

PRINCIPAL = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
C13 = PRINCIPAL / "docs/reports/_harness-2026-09-04/c1-3"


def sem_rede(*a, **k):
    raise AssertionError("rede vedada no diagnóstico")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worktree", required=True)
    p.add_argument("--referencia", required=True)
    p.add_argument("--saida", required=True)
    a = p.parse_args()
    t0 = time.time()
    socket.socket.connect = sem_rede
    socket.create_connection = sem_rede
    sys.dont_write_bytecode = True
    wt, saida = Path(a.worktree).resolve(), Path(a.saida).resolve()
    if saida.is_relative_to(PRINCIPAL.resolve()):
        raise SystemExit("--saida dentro da árvore principal")
    sys.path.insert(0, str(wt))
    import src
    src.__path__ = [str(wt / "src")]

    spec = importlib.util.spec_from_file_location("wz2", C13 / "wz2_diagnostico_causal_23-09.py")
    wz2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wz2)
    compare = wz2.load("d_cmp", C13 / "compara_herancas_15-09.py")
    rb = wz2.load("d_rb", C13 / "replay_bloco_21-09.py")
    ru = wz2.load("d_ru", C13 / "replay_unidade_21-09.py")
    wz = wz2.load("d_wz", C13 / "wz_bloco_cobertura_22-09.py")
    RA = ru.RA
    from src.builder.text.normalize import normalize_match_text
    from src.builder.text.stopwords import MOTOR_GENERIC_STEMS as GENERIC

    REG = collections.defaultdict(lambda: {"tokens_headings": {}, "passe1": {}, "vocab_unit": {}, "aliases_novos": {},
                                           "titulo": {}, "secao": {}, "taxonomia_original": {}})
    orig_prop, orig_tit, orig_sec = RA.propagar_vocabulario_por_headings, RA._subtopico_nomeado_no_titulo, RA._secao_nomeia_subtopico

    def tit_wrapper(entry, unit_slug, vencedor, partes, frases_topico):
        res = orig_tit(entry, unit_slug, vencedor, partes, frases_topico)
        REG[wz2.CTX["sig"]]["titulo"][str(entry.get("id"))] = {"unidade": unit_slug, "vencedor": vencedor, "resultado": res}
        return res

    def sec_wrapper(entry, topicos, generic):
        res = orig_sec(entry, topicos, generic)
        REG[wz2.CTX["sig"]]["secao"][str(entry.get("id"))] = {"resultado": res,
                                                              "secao": str(entry.get("source_section") or "")}
        return res

    def prop_wrapper(passe1, content_taxonomy, fn, *, conf_min, min_entries, df_max):
        reg = REG[wz2.CTX["sig"]]
        units = {str(u.get("slug") or ""): u for u in (content_taxonomy or {}).get("units", []) or []}
        reg["taxonomia_original"] = {s: {"titulo": str(u.get("title") or ""),
                                         "topicos": {str(t.get("slug") or ""): [str(t.get("label") or "")] + list(t.get("aliases") or [])
                                                     for t in u.get("topics") or []}} for s, u in units.items()}
        for s, u in units.items():
            parts = [str(u.get("title") or "")] + [f"{t.get('label', '')} {' '.join(t.get('aliases') or [])}" for t in u.get("topics") or []]
            reg["vocab_unit"][s] = sorted(x for x in normalize_match_text(" ".join(parts)).split() if len(x) >= 4)
        toks = {}
        for e, texto, u, m in passe1:
            eid = str(e.get("id"))
            toks[eid] = sorted(RA._tokens_headings(RA.collect_entry_unit_signals(e, texto), GENERIC))
            reg["tokens_headings"][eid] = toks[eid]
            reg["passe1"][eid] = {"unidade": u, "sub": str(getattr(m, "topic_slug", "") or "") if m else "",
                                  "conf": round(float(m.confidence), 6) if m else None, "amb": bool(m.ambiguous) if m else None,
                                  "confiante": bool(m and m.topic_slug and not m.ambiguous and m.confidence >= conf_min)}
        ext = {}

        def fn_wrapper(entry, tax, texto, **kw):
            ext.setdefault("tax", tax)
            return fn(entry, tax, texto, **kw)

        n = orig_prop(passe1, content_taxonomy, fn_wrapper, conf_min=conf_min, min_entries=min_entries, df_max=df_max)
        partes = RA._partes_de_rotulo(units, passe1, df_max)
        conf = [(str(e.get("id")), u, str(m.topic_slug)) for e, _, u, m in passe1
                if m and m.topic_slug and not m.ambiguous and m.confidence >= conf_min]
        for uu in (ext.get("tax") or {}).get("units", []) or []:
            us = str(uu.get("slug") or "")
            orig_al = {str(t.get("slug") or ""): set(t.get("aliases") or []) for t in (units.get(us) or {}).get("topics") or []}
            for t in uu.get("topics") or []:
                ts = str(t.get("slug") or "")
                for al in sorted(set(t.get("aliases") or []) - orig_al.get(ts, set())):
                    parte = al in partes.get((us, ts), set())
                    reg["aliases_novos"][f"{us}|{ts}|{al}"] = {
                        "origem": "parte_de_rotulo" if parte else "propagado",
                        "doadores": [] if parte else sorted(eid for eid, u2, t2 in conf if u2 == us and t2 == ts and al in toks[eid])}
        reg["parametros"] = {"conf_min": conf_min, "min_entries": min_entries, "df_max": df_max, "mudou": n,
                             "taxonomia_estendida_capturada": "tax" in ext}
        return n

    nomes = compare.mede.NOMES
    estado = {}
    for sig in nomes:
        root = wz.root_de(sig, nomes)
        saved, bloco_novo, decisoes, _ = rb.replay(root)
        estado[sig] = {"root": root, "saved": saved, "decisoes": decisoes,
                       "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
    RA.propagar_vocabulario_por_headings, RA._subtopico_nomeado_no_titulo, RA._secao_nomeia_subtopico = prop_wrapper, tit_wrapper, sec_wrapper
    try:
        cap = wz2.rodar("base", estado, ru, compare, pontuar=True)
    finally:
        RA.propagar_vocabulario_por_headings, RA._subtopico_nomeado_no_titulo, RA._secao_nomeia_subtopico = orig_prop, orig_tit, orig_sec

    src_fora = sorted(n for n, m in sys.modules.items() if (n == "src" or n.startswith("src.")) and getattr(m, "__file__", None)
                      and not Path(m.__file__).resolve().is_relative_to(wt))
    ref = json.loads(Path(a.referencia).read_text(encoding="utf-8"))["decisoes"]
    decisoes = {sig: {eid: {k: (r.get("final") or {}).get(k) for k in ("bloco", "unidade", "sub")}
                      for eid, r in cap[sig].items() if "final" in r} for sig in cap}
    div = [[s, e] for s in sorted(set(decisoes) | set(ref)) for e in sorted(set(decisoes.get(s, {})) | set(ref.get(s, {})))
           if decisoes.get(s, {}).get(e) != ref.get(s, {}).get(e)]
    fiel = not div and not src_fora
    res = {"worktree": str(wt), "normalize": str(Path(sys.modules["src.builder.text.normalize"].__file__).resolve()),
           "normalize_sha256": hashlib.sha256(Path(sys.modules["src.builder.text.normalize"].__file__).read_bytes()).hexdigest(),
           "src_fora_da_worktree": src_fora, "referencia": str(Path(a.referencia).resolve()),
           "fidelidade": "integral" if fiel else "DIVERGENTE: rastro inconclusivo", "divergencias": div,
           "captura_wz2": cap, "instrumentacao": REG, "segundos": round(time.time() - t0)}
    saida.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("fidelidade:", res["fidelidade"], "| divergências", len(div), "| src fora", src_fora or "nenhum",
          "| normalize", res["normalize_sha256"][:16], "| segundos", res["segundos"])
    return 0 if fiel else 1


if __name__ == "__main__":
    sys.exit(main())
