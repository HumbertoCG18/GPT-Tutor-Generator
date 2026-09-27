"""W-AD3 (25/09): avaliador SEPARADO da Fase 1 do regime VOCAB. Definições: adendo v2 (bloco NORMATIVO) §§6–7.

Não importa gold nem módulos de avaliação no import. A régua entra EXPLICITAMENTE em `avalia(...)`; o carregador da régua
histórica (`carrega_regua_historica`) só roda com `--autorizo-gold` e depois de validar capturas e congelamento — NÃO
autorizado nesta etapa. Testes: test_wad3.py, só com dados sintéticos.

Estrutura da régua (por curso): lista de linhas {"gold_id", "eid" (ou None = material ausente, conta como erro),
"bloco": str|None, "unidade": set|None, "sub_primaria": set|None, "sub_aceita": set|None}. None = eixo não avaliado na
linha (fora do denominador); {""} = o vazio é a resposta correta (contrato histórico).
"""
import collections
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import comum as K  # noqa: E402

EIXOS = ("bloco", "unidade", "sub_primaria", "sub_aceita")
CORTES = {"maior_que_zero": lambda s: s > 0, "maior_ou_igual_0_05": lambda s: s >= 0.05}
NA = "não aplicável"


# ------------------------------------------------------------------------------------------- validação
def valida_conjunto(capturas, congelamento, bracos=K.BRACOS):
    """Problemas que impedem avaliar. Lista vazia = conjunto válido."""
    prob = []
    if set(capturas) != set(bracos):
        prob.append(f"braços divergentes: faltam {sorted(set(bracos) - set(capturas))}, extras {sorted(set(capturas) - set(bracos))}")
    inv = congelamento["normativo"]["inventario"]
    if sum(len(v) for v in inv.values()) != K.INVENTARIO_ESPERADO:
        prob.append("inventário congelado != 350")
    for b, cap in capturas.items():
        for p in K.valida_captura(cap, congelamento=congelamento, braco=b, modo="capturar", inventario=inv):
            prob.append(f"{b}: {p}")
    ids = {cap.get("congelamento_comum") for cap in capturas.values()}
    if len(ids) > 1:
        prob.append("mistura de congelamentos entre capturas")
    bloq = (congelamento.get("controles") or {}).get("bloqueados") or []
    if bloq:
        prob.append(f"controles bloqueados (sem permutação válida): {bloq}")
    return prob


def valida_regua(regua, inventario):
    prob, tot = [], collections.Counter()
    if set(regua) != set(inventario):
        prob.append(f"régua com cursos {sorted(set(regua) ^ set(inventario))} divergentes")
    for sig, linhas in regua.items():
        vistos = collections.Counter(r["gold_id"] for r in linhas)
        dup = [g for g, n in vistos.items() if n > 1]
        if dup:
            prob.append(f"{sig}: gold_id duplicado {dup[:5]}")
        for r in linhas:
            if r["eid"] is not None and r["eid"] not in set(inventario.get(sig, [])):
                prob.append(f"{sig}/{r['gold_id']}: eid {r['eid']!r} fora do inventário (captura não pode ser corrompida)")
            tot["bloco"] += r["bloco"] is not None
            tot["unidade"] += r["unidade"] is not None
            tot["sub_primaria"] += r["sub_primaria"] is not None
            if (r["sub_primaria"] is None) != (r["sub_aceita"] is None):
                prob.append(f"{sig}/{r['gold_id']}: primária e aceita inconsistentes")
    for eixo, n in K.DENOMINADORES.items():
        if tot[eixo] != n:
            prob.append(f"denominador de {eixo} = {tot[eixo]} != {n}")
    return prob


# ------------------------------------------------------------------------------------------- acerto e estados
def registro(cap, sig, eid):
    """None só para material legitimamente ausente (eid None). eid presente sem registro = captura corrompida."""
    if eid is None:
        return None
    try:
        return cap["decisoes"][sig][eid]
    except KeyError:
        raise K.ErroIntegridade(f"{sig}/{eid}: registro ausente na captura") from None


def predicao(rec, eixo):
    if rec is None:
        return None
    return rec["final"]["sub" if eixo.startswith("sub") else eixo]


def acerta(eixo, linha, rec):
    gold = linha[eixo]
    if gold is None:
        raise ValueError("eixo não avaliado nesta linha")
    p = predicao(rec, eixo)
    if p is None:
        return False   # material ausente: erro, nunca abstenção correta
    return p == gold if eixo == "bloco" else p in gold


def estado_selecao(rec):
    """Estado da 1ª passada, sem converter ambiguidade/baixa confiança em vazio."""
    if rec is None:
        return "material_ausente"
    if not rec["chamado"]:
        return "nao_chamado"
    p1 = rec["p1"]
    pts = p1["pontuacoes"]
    if not pts:
        return "chamado_sem_topicos_elegiveis"
    maximo = max(x["score"] for x in pts)
    if maximo == 0:
        return "candidatos_score_zero"
    if sum(1 for x in pts if x["score"] == maximo) > 1:
        return "empate"
    if p1["ambigua"] and p1["vencedor"]["topico"]:
        return "ambigua_com_slug"
    if not p1["vencedor"]["topico"]:
        return "abstencao_1a"
    return "decidido"


def score_do_gold(rec, gold):
    """Maior score de um tópico-gold NA unidade efetivamente fornecida (com unidade vazia, todas as unidades)."""
    if rec is None or not rec["chamado"]:
        return None
    u = rec["p1"]["unidade_fornecida"]
    vals = [x["score"] for x in rec["p1"]["pontuacoes"] if x["topico"] in gold and (not u or x["unidade"] == u)]
    return max(vals) if vals else None


def existe_e_elegivel(tax, gold, unidade):
    topicos = [(str(u.get("slug") or ""), str(t.get("slug") or "")) for u in tax.get("units") or [] for t in u.get("topics") or []]
    existe = any(t in gold for _u, t in topicos)
    elegivel = any(t in gold and (not unidade or u == unidade) for u, t in topicos)
    return existe, elegivel


# ------------------------------------------------------------------------------------------- métricas
def fracao(num, den):
    return {"num": num, "den": den, "valor": (num / den) if den else NA}


def placar(cap, regua):
    out = {}
    for sig, linhas in regua.items():
        c = {e: [0, 0] for e in EIXOS}
        for r in linhas:
            rec = registro(cap, sig, r["eid"])
            for e in EIXOS:
                if r[e] is not None:
                    c[e][1] += 1
                    c[e][0] += acerta(e, r, rec)
        out[sig] = {e: {"acertos": a, "n": n} for e, (a, n) in c.items()}
    out["TOTAL"] = {e: {"acertos": sum(out[s][e]["acertos"] for s in regua), "n": sum(out[s][e]["n"] for s in regua)} for e in EIXOS}
    return out


def transicoes(antes, depois, regua, eixo):
    """Partição por (certo antes, certo depois, vazio antes, vazio depois, mudou) e categorias derivadas dela."""
    cel = collections.Counter()
    for sig, linhas in regua.items():
        for r in linhas:
            if r[eixo] is None:
                continue
            ra, rd = registro(antes, sig, r["eid"]), registro(depois, sig, r["eid"])
            pa, pd = predicao(ra, eixo), predicao(rd, eixo)
            ca, cd = acerta(eixo, r, ra), acerta(eixo, r, rd)
            va, vd = (pa in (None, "")), (pd in (None, ""))
            cel[(int(ca), int(cd), int(va), int(vd), int(pa != pd))] += 1
    d = collections.Counter()
    for (ca, cd, va, vd, m), n in cel.items():
        if not ca and cd:
            d["correcao"] += n
        if ca and not cd:
            d["perda"] += n
        if not ca and not cd and m:
            d["erro_para_outro_erro"] += n
        if ca and cd and m:
            d["correta_para_outra_correta"] += n
        if va and not vd and cd:
            d["abstencao_para_certa"] += n
        if va and not vd and not cd:
            d["abstencao_para_errada"] += n
        if not va and vd:
            d["decisao_para_vazio"] += n
    alteradas = sum(n for k, n in cel.items() if k[4])
    certas_alteradas = sum(n for k, n in cel.items() if k[4] and k[1])
    nao_vazias = sum(n for k, n in cel.items() if k[4] and not k[3])
    certas_nao_vazias = sum(n for k, n in cel.items() if k[4] and not k[3] and k[1])
    return {"celulas": {"c{}{}_v{}{}_m{}".format(*k): n for k, n in sorted(cel.items())}, "derivadas": dict(d),
            "precisao_alteradas": fracao(certas_alteradas, alteradas),
            "precisao_alteradas_nao_vazias": fracao(certas_nao_vazias, nao_vazias)}


def geracao_selecao(cru, braco, regua, tax_cru, tax_braco):
    """Escada (a)-(e) e grupos de candidato por corte; seleção no subconjunto comum."""
    escada = {b: collections.Counter() for b in ("CRU", "BRACO")}
    grupos = {c: collections.Counter() for c in CORTES}
    sel = {c: {"CRU": {"p1": [0, 0], "final": [0, 0]}, "BRACO": {"p1": [0, 0], "final": [0, 0]}} for c in CORTES}
    estados = {b: collections.Counter() for b in ("CRU", "BRACO")}
    for sig, linhas in regua.items():
        for r in linhas:
            g = r["sub_primaria"]
            if g is None:
                continue
            recs = {"CRU": registro(cru, sig, r["eid"]), "BRACO": registro(braco, sig, r["eid"])}
            taxs = {"CRU": tax_cru[sig], "BRACO": tax_braco[sig]}
            cand = {}
            for b, rec in recs.items():
                estados[b][estado_selecao(rec)] += 1
                if g == {""}:
                    escada[b]["gold_vazio"] += 1
                    continue
                u = rec["p1"]["unidade_fornecida"] if rec and rec["chamado"] else (rec["final"]["unidade"] if rec else "")
                existe, eleg = existe_e_elegivel(taxs[b], g, u)
                s = score_do_gold(rec, g)
                escada[b]["a_existe"] += existe
                escada[b]["a_elegivel"] += eleg
                escada[b]["b_score_pos"] += bool(s is not None and s > 0)
                escada[b]["c_score_ge_0_05"] += bool(s is not None and s >= 0.05)
                escada[b]["d_escolhido_1a"] += bool(rec and rec["chamado"] and rec["p1"]["vencedor"]["topico"] in g)
                escada[b]["e_final_correta"] += acerta("sub_primaria", r, rec)
                cand[b] = {c: bool(s is not None and f(s)) for c, f in CORTES.items()}
            if g == {""}:
                continue
            for c in CORTES:
                a, b = cand["CRU"][c], cand["BRACO"][c]
                grupos[c]["ambos" if a and b else "so_cru" if a else "so_braco" if b else "nenhum"] += 1
                if a and b:
                    for lado, rec in recs.items():
                        sel[c][lado]["p1"][1] += 1
                        sel[c][lado]["p1"][0] += bool(rec["p1"]["vencedor"]["topico"] in g)
                        sel[c][lado]["final"][1] += 1
                        sel[c][lado]["final"][0] += acerta("sub_primaria", r, rec)
    return {"escada": {b: dict(v) for b, v in escada.items()}, "grupos": {c: dict(v) for c, v in grupos.items()},
            "selecao_subconjunto_comum": {c: {lado: {k: fracao(*v) for k, v in m.items()} for lado, m in s.items()}
                                          for c, s in sel.items()},
            "estados_1a": {b: dict(v) for b, v in estados.items()}}


def meta(pl, regua):
    """>90 % estrito por contagem exata (acertos*10 > 9*n), só nos eixos avaliados de cada curso."""
    out = {}
    for sig in regua:
        out[sig] = {e: (pl[sig][e]["acertos"] * 10 > 9 * pl[sig][e]["n"]) if pl[sig][e]["n"] else NA
                    for e in ("bloco", "unidade", "sub_primaria")}
    return out


def avalia(capturas, congelamento, regua, taxonomias):
    """Avaliação completa. Recusa conjunto inválido antes de pontuar."""
    prob = valida_conjunto(capturas, congelamento) + valida_regua(regua, congelamento["normativo"]["inventario"])
    if prob:
        raise K.ErroIntegridade("avaliação recusada: " + "; ".join(prob[:8]))
    pl = {b: placar(capturas[b], regua) for b in K.BRACOS}
    comp = {b: {e: transicoes(capturas["CRU"], capturas[b], regua, e) for e in EIXOS} for b in K.BRACOS if b != "CRU"}
    gen = {b: geracao_selecao(capturas["CRU"], capturas[b], regua, taxonomias["CRU"], taxonomias[b]) for b in K.BRACOS if b != "CRU"}
    return {"placar": pl, "comparacoes": comp, "geracao_selecao": gen, "meta": {b: meta(pl[b], regua) for b in K.BRACOS},
            "veredictos": veredictos(pl, comp, regua)}


def veredictos(pl, comp, regua):
    sp = {b: pl[b]["TOTAL"]["sub_primaria"]["acertos"] for b in pl}
    controles = ("CRU", "CTRL_MAIOR", "CTRL_ALEAT_1", "CTRL_ALEAT_2", "CTRL_ALEAT_3")
    a = all(sp["VOCAB_LLM"] > sp[c] for c in controles)
    t = comp["VOCAB_LLM"]
    perdas = {e: t[e]["derivadas"].get("perda", 0) for e in EIXOS}
    regride = {e: [s for s in regua if pl["VOCAB_LLM"][s][e]["acertos"] < pl["CRU"][s][e]["acertos"]] for e in EIXOS}
    b_ok = (sp["VOCAB_LLM"] > sp["CRU"] and not any(perdas.values()) and not any(regride.values()))
    if b_ok:
        b = "sem violação do contrato na Fase 1 condicionada à timeline congelada (não comprova integração completa)"
    elif a:
        b = "sinal exploratório observado; candidato reprovado para integração"
    else:
        b = "sem sinal exploratório"
    c = {s: meta(pl["VOCAB_LLM"], regua)[s] for s in regua}
    return {"A_sinal_exploratorio": a, "A_detalhe": {c_: sp[c_] for c_ in ("VOCAB_LLM", *controles)},
            "B_integracao": b, "B_perdas": perdas, "B_cursos_que_regridem": regride, "C_meta_VOCAB_LLM": c}


# ------------------------------------------------------------------------------------------- régua histórica (bloqueada)
def regua_de_estado(estado):
    """Converte a saída de wz.preparar_avaliacao ({sig: {"rows", "eid_de", "golds": (gb, gu, gs, gsp)}}) na estrutura da
    régua. Semântica idêntica à de W-AA/W-AB: um eixo entra na linha quando a coluna correspondente não é vazia; gold
    ausente para uma linha avaliada é erro de integridade (não vira acerto nem abstenção)."""
    regua = {}
    for sig, v in estado.items():
        gb, gu, gs, gsp = v["golds"]
        linhas = []
        try:
            for row in v["rows"]:
                gid = row["entry_id"]
                sub = row["sub_primario"] != ""
                linhas.append({"gold_id": gid, "eid": v["eid_de"].get(gid),
                               "bloco": gb[gid] if row["bloco"] != "" else None,
                               "unidade": set(gu[gid]) if row["unidade"] != "" else None,
                               "sub_primaria": set(gsp[gid]) if sub else None,
                               "sub_aceita": set(gs[gid]) if sub else None})
        except KeyError as exc:
            raise K.ErroIntegridade(f"{sig}: gold ausente para linha avaliada ({exc})") from None
        regua[sig] = linhas
    return regua


def carrega_taxonomias(congelamento, snap_dir):
    """Snapshots de taxonomia por braço/curso, conferidos contra o congelamento."""
    out = {}
    for b in K.BRACOS:
        out[b] = {}
        for sig in K.NOMES:
            p = Path(snap_dir) / b / sig / "taxonomia.json"
            if K.sha_arq(p) != congelamento["insumos"][b][sig]["taxonomia_arquivo_sha"]:
                raise K.ErroIntegridade(f"snapshot de taxonomia {b}/{sig} não confere")
            out[b][sig] = K.carrega_json_estrito(p)
    return out


def carrega_regua_historica(autorizado=False):
    """Única porta para o gold real. Import tardio dos módulos históricos; só com autorização explícita."""
    if autorizado is not True:
        raise PermissionError("leitura do gold não autorizada nesta etapa")
    import importlib.util
    c13 = HERE.parent

    def load(nome, arq):
        spec = importlib.util.spec_from_file_location(nome, c13 / arq)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    compare = load("wad3av_cmp", "compara_herancas_15-09.py")
    wx = load("wad3av_wx", "wx_regua_corrigida_22-09.py")
    wz = load("wad3av_wz", "wz_bloco_cobertura_22-09.py")
    nomes = compare.mede.NOMES
    estado = {s: {"root": wz.root_de(s, nomes),
                  "saved": {str(e["id"]): e for e in K.carrega_json_estrito(wz.root_de(s, nomes) / "manifest.json")["entries"]}}
              for s in nomes}
    wz.preparar_avaliacao(estado, compare, compare.mede, wx)
    return regua_de_estado(estado)


def main():
    """Uso futuro: python avaliador.py --autorizo-gold <dir_capturas> <congelamento.json> <dir_snapshots> <saida.json>.
    Ordem obrigatória: capturas e congelamento validados ANTES de qualquer leitura de gold."""
    if "--autorizo-gold" not in sys.argv:
        print("avaliação real não autorizada nesta etapa (adendo v2 §9)", flush=True)
        sys.exit(2)
    args = [a for a in sys.argv[1:] if a != "--autorizo-gold"]
    if len(args) != 4:
        print(main.__doc__, flush=True)
        sys.exit(2)
    caps_dir, cong_path, snap_dir, saida = map(Path, args)
    cong = K.carrega_json_estrito(cong_path)
    if K.id_congelamento(cong["normativo"]) != cong["id_comum"]:
        raise K.ErroIntegridade("congelamento adulterado")
    capturas = {}
    for b in K.BRACOS:
        p = caps_dir / f"capturar_{b}_{cong['id_comum'][:16]}_{cong['insumos_braco'][b][:16]}.json"
        capturas[b] = K.carrega_json_estrito(p)
    prob = valida_conjunto(capturas, cong)
    if prob:
        raise K.ErroIntegridade("capturas inválidas: " + "; ".join(prob[:8]))
    taxonomias = carrega_taxonomias(cong, snap_dir)
    regua = carrega_regua_historica(autorizado=True)   # só depois das validações acima
    K.grava_atomico(saida, K.canon(avalia(capturas, cong, regua, taxonomias)))


if __name__ == "__main__":
    main()
