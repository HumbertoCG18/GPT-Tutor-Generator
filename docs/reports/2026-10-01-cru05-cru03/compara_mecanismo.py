"""Compara os rastros base × candidato do diagnóstico do CRU-05 (sem gold): primeira divergência por material.

Uso: python -B compara_mecanismo.py <diag_rastro_base.json> <diag_rastro_candidato.json> <saida.json>
Ordem dos estágios = ordem do código (resolver_apply.apply_*/propagar_vocabulario_por_headings).
"""
import json
import sys
from pathlib import Path

ESTAGIOS = ("tokens_headings", "unidade_bruta", "sub_1a", "confiante_1a", "titulo", "aliases_da_unidade",
            "sub_2a_chamada", "secao", "final", "final_motivos")


def carrega(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    assert d["fidelidade"] == "integral", f"{p}: rastro inconclusivo ({d['fidelidade']})"
    return d


def visao(d, sig, eid):
    cap = d["captura_wz2"].get(sig, {}).get(eid, {})
    ins = d["instrumentacao"].get(sig, {})
    p1 = ins.get("passe1", {}).get(eid, {})
    unidade = p1.get("unidade") or (cap.get("final") or {}).get("unidade") or ""
    s1 = dict(cap.get("sub_1a") or {})
    pont = sorted(s1.pop("pontuacoes", []) or [], key=lambda x: -x[2])[:5]
    return {
        "tokens_headings": ins.get("tokens_headings", {}).get(eid),
        "unidade_bruta": {k: v for k, v in (cap.get("unidade_bruta") or {}).items() if k != "reasons"},
        "sub_1a": {**s1, "top5_exato": pont},
        "confiante_1a": p1.get("confiante"),
        "titulo": ins.get("titulo", {}).get(eid),
        "aliases_da_unidade": sorted(k for k in ins.get("aliases_novos", {}) if k.startswith(f"{unidade}|")),
        "sub_2a_chamada": cap.get("sub_2a_chamada"),
        "secao": ins.get("secao", {}).get(eid),
        "final": {k: (cap.get("final") or {}).get(k) for k in ("bloco", "unidade", "sub")},
        "final_motivos": {k: (cap.get("final") or {}).get(k) for k in ("sub_reasons", "sub_conf", "unit_reasons")},
    }


def main():
    b, c = carrega(sys.argv[1]), carrega(sys.argv[2])
    out = {"normalize": {"base": b["normalize_sha256"], "candidato": c["normalize_sha256"]}, "materiais": {}, "cursos": {}}
    contagem = {e: 0 for e in ESTAGIOS}
    for sig in sorted(b["captura_wz2"]):
        ib, ic = b["instrumentacao"].get(sig, {}), c["instrumentacao"].get(sig, {})
        ab, ac = ib.get("aliases_novos", {}), ic.get("aliases_novos", {})
        out["cursos"][sig] = {
            "aliases_so_base": {k: ab[k] for k in sorted(set(ab) - set(ac))},
            "aliases_so_candidato": {k: ac[k] for k in sorted(set(ac) - set(ab))},
            "vocab_unit_mudou": {u: {"so_base": sorted(set(ib["vocab_unit"][u]) - set(ic["vocab_unit"].get(u, []))),
                                     "so_candidato": sorted(set(ic["vocab_unit"].get(u, [])) - set(ib["vocab_unit"][u]))}
                                 for u in ib.get("vocab_unit", {})
                                 if set(ib["vocab_unit"][u]) != set(ic["vocab_unit"].get(u, []))},
            "mudou_2a": [ib.get("parametros", {}).get("mudou"), ic.get("parametros", {}).get("mudou")]}
        for eid in sorted(eid for eid in b["captura_wz2"][sig] if not eid.startswith("__")):
            vb, vc = visao(b, sig, eid), visao(c, sig, eid)
            dif = [e for e in ESTAGIOS if vb[e] != vc[e]]
            if not dif:
                continue
            contagem[dif[0]] += 1
            out["materiais"][f"{sig}|{eid}"] = {"primeira_divergencia": dif[0], "estagios_divergentes": dif,
                                                "base": {e: vb[e] for e in dif}, "candidato": {e: vc[e] for e in dif}}
    out["primeira_divergencia_contagem"] = contagem
    out["mudam_no_final"] = sorted(k for k, v in out["materiais"].items() if "final" in v["estagios_divergentes"])
    Path(sys.argv[3]).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("materiais com alguma divergência:", len(out["materiais"]), "| primeira divergência:", contagem)
    print("mudam no final:", out["mudam_no_final"])
    for k in out["mudam_no_final"]:
        print(" ", k, "->", out["materiais"][k]["primeira_divergencia"], out["materiais"][k]["estagios_divergentes"])


if __name__ == "__main__":
    main()
