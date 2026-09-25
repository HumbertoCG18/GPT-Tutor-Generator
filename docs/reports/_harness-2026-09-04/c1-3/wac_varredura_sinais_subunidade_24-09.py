"""W-AC (24/09): varredura só leitura de sinais de subunidade nunca testados, sobre a base congelada do W-Z2.

Autorização: usuário em 24/09 ("Varredura e depois teto"). 0 src, 0 replay, sem build, rede, LLM ou commit. Cada sinal
prevê no máximo um tópico por material, sem gold; as previsões são congeladas por sha256 ANTES de ler o gold.
Base de decisão: final da captura do W-Z2 (`.frzero/wz2_captura_base_23-09.json`, igual ao src atual exceto 1 unidade
do M1, que não muda subunidade). Tópicos candidatos: os da unidade final, na ordem da taxonomia
(`_iter_content_taxonomy_topics`, o que o seletor vê).

SINAIS (pré-declarados):
- P1 ordem da aula: bloco temporal do material é aula (kind class) da unidade final u; k = posição do bloco entre as
  aulas de u (ordem do cronograma), n = nº de aulas de u, m = nº de tópicos de u; prevê o tópico de índice floor(k*m/n).
- P2 posição na seção do Moodle: materiais com a mesma `moodle_section_index` e a mesma unidade final, ordenados por
  `moodle_module_index`; i = posição, N = tamanho do grupo (>= 2); prevê o tópico de índice floor(i*m/N).
- P4 referência cruzada: o texto do material contém, como frase, o título normalizado de OUTRO material do curso (>= 3
  tokens de >= 3 letras, título único no curso); herda a subunidade final daquele material (decisão do motor, não gold).
  Mais de um referido com subunidades diferentes -> não prevê.
- P5 tópico primário da aula: `primary_topic_slug` do bloco temporal, com `topic_ambiguous` falso, se for tópico da
  unidade final do material.
- P3 (2ª passada só com doadores fortes) não é sinal novo: o teto é recuperar as 4 perdas que a propagação causa hoje
  (W-Z2 §3.5: +11/-4); registrado sem medição.
PORTÃO (o mesmo do tracker): precisão > 50 % nos 86 acertos atuais onde o sinal dispara E saldo potencial > 0 se o sinal
substituísse a decisão quando dispara (ganhos nos erros - perdas nos acertos). Sem parâmetro livre -> sem LOCO.
Uso: python wac_varredura_sinais_subunidade_24-09.py
"""
import collections
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

T0 = time.time()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
sys.path.insert(0, str(DATA))
OUT_JSON = HERE / "wac_varredura_sinais_subunidade_24-09.json"
CAP_WZ2 = DATA / ".frzero/wz2_captura_base_23-09.json"
SINAIS = ("P1", "P2", "P4", "P5")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def prever(sig, root, base, ru):
    manifest = {str(e["id"]): e for e in read(root / "manifest.json")["entries"]}
    blocos = read(root / "course/.timeline_index.json")["blocks"]
    por_id = {str(b.get("id") or ""): b for b in blocos}
    tax = read(root / "course/.content_taxonomy.json")
    topicos = collections.defaultdict(list)
    for t in ru._iter_content_taxonomy_topics(tax) or []:
        topicos[str(t.get("unit_slug") or "")].append(str(t.get("topic_slug") or ""))
    aulas = collections.defaultdict(list)
    for b in blocos:
        if str(b.get("kind") or "") == "class" and b.get("unit_slug"):
            aulas[str(b["unit_slug"])].append(str(b.get("id") or ""))
    final = {eid: r["final"] for eid, r in base.items() if isinstance(r, dict) and r.get("final")}
    prev = {s: {} for s in SINAIS}

    # P1 e P5
    for eid, f in final.items():
        u, bl = f.get("unidade") or "", por_id.get(f.get("bloco") or "")
        tops = topicos.get(u) or []
        if not u or not bl or not tops:
            continue
        if str(bl.get("kind") or "") == "class" and str(bl.get("unit_slug") or "") == u:
            k, n = aulas[u].index(str(bl["id"])), len(aulas[u])
            prev["P1"][eid] = tops[min(len(tops) - 1, k * len(tops) // n)]
        pts = str(bl.get("primary_topic_slug") or "")
        if pts and not bl.get("topic_ambiguous") and pts in tops:
            prev["P5"][eid] = pts

    # P2
    grupos = collections.defaultdict(list)
    for eid, f in final.items():
        e = manifest.get(eid) or {}
        si, mi = e.get("moodle_section_index"), e.get("moodle_module_index")
        if si is None or mi is None or not f.get("unidade"):
            continue
        grupos[(si, f["unidade"])].append((mi, eid))
    for (_si, u), membros in grupos.items():
        tops = topicos.get(u) or []
        if len(membros) < 2 or not tops:
            continue
        for i, (_mi, eid) in enumerate(sorted(membros)):
            prev["P2"][eid] = tops[min(len(tops) - 1, i * len(tops) // len(membros))]

    # P4
    norm = ru.normalize_match_text
    titulos = collections.defaultdict(list)
    for eid, e in manifest.items():
        tn = " ".join(norm(str(e.get("title") or "")).split())
        if len([w for w in tn.split() if len(w) >= 3]) >= 3 and eid in final:
            titulos[tn].append(eid)
    unicos = {tn: ids[0] for tn, ids in titulos.items() if len(ids) == 1}
    for eid in final:
        e = manifest.get(eid)
        if not e:
            continue
        texto = " " + " ".join(norm(ru._entry_markdown_text_for_file_map(root, e) or "").split()) + " "
        alvos = {final[ref].get("sub") or "" for tn, ref in unicos.items() if ref != eid and f" {tn} " in texto}
        alvos.discard("")
        if len(alvos) == 1:
            prev["P4"][eid] = alvos.pop()
    return prev


def main():
    assert not OUT_JSON.exists(), "preservar evidencia existente"
    compare = load("wac_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    wx = load("wac_wx", HERE / "wx_regua_corrigida_22-09.py")
    ru = load("wac_ru", HERE / "replay_unidade_21-09.py")
    wz = load("wac_wz", HERE / "wz_bloco_cobertura_22-09.py")
    nomes = mede.NOMES
    raizes = {s: wz.root_de(s, nomes) for s in nomes}
    cz = read(CAP_WZ2)
    assert cz["sha256_base"].startswith("f941ac33"), "base congelada do W-Z2 inesperada"
    base = cz["base"]
    sha_decl = sha({"doc": __doc__})
    previsoes = {sig: prever(sig, raizes[sig], base[sig], ru) for sig in nomes}
    sha_prev = sha(previsoes)
    print("DECLARACAO", sha_decl[:16], "| CONGELAMENTO previsoes", sha_prev[:16],
          {s: {p: len(v) for p, v in previsoes[s].items()} for s in nomes}, flush=True)

    # ================================================================ GOLD entra aqui
    estado = {sig: {"root": raizes[sig], "saved": {str(e["id"]): e for e in read(raizes[sig] / "manifest.json")["entries"]}}
              for sig in nomes}
    wz.preparar_avaliacao(estado, compare, mede, wx)
    R = {"por_sinal": {}, "por_curso": {}, "exemplos": {}}
    for p in SINAIS:
        c, cc, ex = collections.Counter(), collections.defaultdict(collections.Counter), []
        for sig, v in estado.items():
            gsp = v["golds"][3]
            for row in v["rows"]:
                if row["sub_primario"] == "":
                    continue
                gid, eid = row["entry_id"], v["eid_de"].get(row["entry_id"])
                f = ((base[sig].get(eid) or {}).get("final") or {}) if eid else {}
                acerto = (f.get("sub") or "") in gsp[gid]
                pv = previsoes[sig][p].get(eid) if eid else None
                c["n"] += 1
                c["acertos" if acerto else "erros"] += 1
                if pv is None:
                    continue
                ok = pv in gsp[gid]
                chave = ("acerto" if acerto else "erro") + ("_concorda" if ok else "_discorda")
                c[chave] += 1
                cc[sig][chave] += 1
                if not acerto and ok and len(ex) < 8:
                    ex.append({"curso": sig, "gold_id": gid, "previsto": pv, "base": f.get("sub")})
        dispara_acertos = c["acerto_concorda"] + c["acerto_discorda"]
        precisao = round(c["acerto_concorda"] / dispara_acertos, 3) if dispara_acertos else None
        saldo = c["erro_concorda"] - c["acerto_discorda"]
        R["por_sinal"][p] = {**dict(c), "precisao_nos_acertos": precisao, "saldo_potencial": saldo,
                             "passa_portao": bool(precisao is not None and precisao > 0.5 and saldo > 0)}
        R["por_curso"][p] = {s: dict(v) for s, v in cc.items()}
        R["exemplos"][p] = ex
    R.update({"escopo": __doc__, "sha256_declaracao": sha_decl, "sha256_previsoes": sha_prev,
              "base_wz2": cz["sha256_base"], "p3_teto_sem_medicao": "+4 (perdas atuais da propagação, W-Z2 §3.5)",
              "segundos": round(time.time() - T0, 1)})
    OUT_JSON.write_text(json.dumps(R, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for p in SINAIS:
        x = R["por_sinal"][p]
        print(p, "dispara acertos", x.get("acerto_concorda", 0) + x.get("acerto_discorda", 0), "precisao",
              x["precisao_nos_acertos"], "| erros: aponta gold", x.get("erro_concorda", 0), "outro", x.get("erro_discorda", 0),
              "| saldo potencial", x["saldo_potencial"], "| portao", x["passa_portao"], flush=True)
    print("OK", OUT_JSON.name, hashlib.sha256(OUT_JSON.read_bytes()).hexdigest()[:16], R["segundos"], "s")


if __name__ == "__main__":
    main()
