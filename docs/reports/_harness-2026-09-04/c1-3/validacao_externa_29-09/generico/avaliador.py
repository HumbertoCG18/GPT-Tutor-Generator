"""Harness genérico (validação externa, 29/09): avaliador da rodada VOCAB_LIMPO (../../vocab_limpo_26-09/avaliador.py)
com SÓ: nomes de braço trocados pelos papéis da configuração (K.CRU, K.CANDIDATO, K.CTRL_MAIOR, K.CTRL_ALEAT); cursos com
régua de unidade (UNI) vindos da configuração; um segundo carregador de régua para o gold externo (`gold_externo.py`),
escolhido pela configuração; e, quando a configuração pede (cursos novos, bloco sem gold), a invariância de bloco por ID
entre CRU e candidato como condição adicional de B. Métricas, transições, geração/seleção, meta e contrato idênticos.

Original: avaliador SEPARADO da Fase 1 do regime VOCAB. Definições: adendo v3 (bloco NORMATIVO) §§6–8.

Não importa gold nem módulos históricos de avaliação (nem no import, nem depois). A régua real é lida por CÓPIAS LOCAIS
identificadas dos carregadores históricos (HISTORICO), a partir dos caminhos EXPLÍCITOS do congelamento; cada arquivo só é
interpretado depois de conferido contra o blob git congelado, e os bytes interpretados são os bytes conferidos.
`carrega_regua_historica` só roda com `--autorizo-gold`, depois de validar código do avaliador, congelamento e capturas —
NÃO autorizado nesta etapa. Testes: test_wad4.py e test_defeitos_v4.py, só com dados sintéticos.

Estrutura da régua (por curso): lista de linhas {"gold_id", "eid" (None = material ausente, conta como erro),
"bloco": str|None, "unidade": set|None, "sub_primaria": set|None, "sub_aceita": set|None}. None = eixo não avaliado na
linha (fora do denominador); {""} = o vazio é a resposta correta (contrato histórico).
"""
import collections
import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[5]   # o genérico fica um nível abaixo de c1-3
sys.path.insert(0, str(HERE))
import comum as K  # noqa: E402
import gold_externo as GE  # noqa: E402  (só stdlib)

EIXOS = ("bloco", "unidade", "sub_primaria", "sub_aceita")
OFICIAIS = ("bloco", "unidade", "sub_primaria")   # sub_aceita é auxiliar: relatada, nunca veta nem aprova
CORTES = {"maior_que_zero": lambda s: s > 0, "maior_ou_igual_0_05": lambda s: s >= 0.05}
NA = "não aplicável"
UNI = K.R.UNI   # cursos com régua de unidade (configuração da rodada)
CAMPOS_LINHA = {"gold_id", "eid", "bloco", "unidade", "sub_primaria", "sub_aceita"}
# Origem de cada cópia local. Blobs do código histórico: congelamento.normativo.avaliacao.codigo_historico_blob.
HISTORICO = {
    "linhas_csv": "c1-3/wx_regua_corrigida_22-09.py:csv_rows (lê dos bytes conferidos, não do caminho)",
    "rotulos_bloco": "scripts/eval_ground_truth.py:load_labels_csv (+ id com blocos conflitantes = erro)",
    "regua_unidade": "c1-3/wx_regua_corrigida_22-09.py:regua_unidade (cópia de scripts/eval_entry_unit.carrega_regua_unidade)",
    "golds_sub": "c1-3/wx_regua_corrigida_22-09.py:golds_de (parte de subunidade)",
    "golds_de": "c1-3/wx_regua_corrigida_22-09.py:golds_de (resolução p(nome) substituída por caminhos explícitos)",
    "origem": "c1-3/compara_herancas_15-09.py:source e indexed",
    "mapeia_eids": "c1-3/wz_bloco_cobertura_22-09.py:preparar_avaliacao (hits[0] substituído por unicidade obrigatória)",
    "regua_de_estado": "c1-3/wz_bloco_cobertura_22-09.py:avaliar (critério de entrada de cada eixo)",
}


# ------------------------------------------------------------------------------------------- validação
def valida_conjunto(capturas, congelamento, bracos=K.BRACOS):
    """Problemas que impedem avaliar. Lista vazia = conjunto válido."""
    prob = [f"congelamento: {p}" for p in K.valida_congelamento(congelamento)]
    if set(capturas) != set(bracos):
        prob.append(f"braços divergentes: faltam {sorted(set(bracos) - set(capturas))}, extras {sorted(set(capturas) - set(bracos))}")
    inv = congelamento["normativo"]["inventario"]
    if sum(len(v) for v in inv.values()) != K.INVENTARIO_ESPERADO:
        prob.append(f"inventário congelado != {K.INVENTARIO_ESPERADO}")
    for b in sorted(set(capturas) & set(bracos)):
        prob += [f"{b}: {p}" for p in K.valida_captura(capturas[b], congelamento=congelamento, braco=b, modo="capturar")]
    if len({cap.get("congelamento_comum") for cap in capturas.values()}) > 1:
        prob.append("mistura de congelamentos entre capturas")
    bloq = (congelamento.get("controles") or {}).get("bloqueados") or []
    if bloq:
        prob.append(f"controles bloqueados (sem permutação válida): {bloq}")
    return prob


def _conjunto_de_textos(v):
    return isinstance(v, (set, frozenset)) and bool(v) and all(isinstance(x, str) for x in v)


def valida_regua(regua, inventario):
    """Cursos, identidade das linhas, tipos, primária ⊆ aceita e denominadores POR CURSO e totais."""
    prob, tot = [], collections.Counter()
    if set(regua) != set(inventario):
        prob.append(f"régua com cursos divergentes: ausentes {sorted(set(inventario) - set(regua))}, "
                    f"extras {sorted(set(regua) - set(inventario))}")
    for sig, linhas in regua.items():
        ids, por_eixo = set(inventario.get(sig, [])), collections.Counter()
        dup = sorted(g for g, n in collections.Counter(r.get("gold_id") for r in linhas).items() if n > 1)
        if dup:
            prob.append(f"{sig}: gold_id duplicado {dup[:5]}")
        mesmo = sorted(e for e, n in collections.Counter(r.get("eid") for r in linhas if r.get("eid") is not None).items() if n > 1)
        if mesmo:
            prob.append(f"{sig}: mesmo eid para mais de um gold_id {mesmo[:5]}")
        for r in linhas:
            onde = f"{sig}/{r.get('gold_id')}"
            if set(r) != CAMPOS_LINHA:
                prob.append(f"{onde}: campos da linha divergentes")
                continue
            if r["eid"] is not None and r["eid"] not in ids:
                prob.append(f"{onde}: eid {r['eid']!r} fora do inventário (captura não pode ser corrompida)")
            if not (r["bloco"] is None or isinstance(r["bloco"], str)):
                prob.append(f"{onde}: bloco não é texto")
            for e in ("unidade", "sub_primaria", "sub_aceita"):
                if r[e] is not None and not _conjunto_de_textos(r[e]):
                    prob.append(f"{onde}: {e} não é conjunto não vazio de textos")
            if (r["sub_primaria"] is None) != (r["sub_aceita"] is None):
                prob.append(f"{onde}: primária e aceita inconsistentes")
            elif _conjunto_de_textos(r["sub_primaria"]) and _conjunto_de_textos(r["sub_aceita"]) \
                    and not r["sub_primaria"] <= r["sub_aceita"]:
                prob.append(f"{onde}: primária fora da aceita")
            for e in OFICIAIS:
                por_eixo[e] += r[e] is not None
        esperado = K.DENOM_POR_CURSO.get(sig)
        if esperado is None:
            prob.append(f"{sig}: curso sem denominador declarado")
        else:
            prob += [f"{sig}: denominador de {e} = {por_eixo[e]} != {esperado[e]}" for e in OFICIAIS if por_eixo[e] != esperado[e]]
        tot.update(por_eixo)
    prob += [f"denominador total de {e} = {tot[e]} != {n}" for e, n in K.DENOMINADORES.items() if tot[e] != n]
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


def geracao_do_material(rec, gold, tax):
    """Escada de geração de UM material. Ausente ou não chamado: elegibilidade e escolha NÃO se aplicam (nada de unidade
    final como premissa fictícia). A existência do rótulo na taxonomia independe da chamada."""
    pares = [(str(u.get("slug") or ""), str(t.get("slug") or "")) for u in tax.get("units") or [] for t in u.get("topics") or []]
    ocorr = [p for p in pares if p[1] in gold]
    g = {"estado_1a": estado_selecao(rec), "rotulo_existe_na_taxonomia": bool(ocorr), "ocorrencias_na_taxonomia": len(ocorr),
         "elegivel": NA, "score_pos": NA, "score_ge_0_05": NA, "escolhido_1a": NA}
    if rec is None or not rec["chamado"]:
        return g
    u = rec["p1"]["unidade_fornecida"]
    s = score_do_gold(rec, gold)
    g.update(elegivel=any(not u or uu == u for uu, _t in ocorr), score_pos=s is not None and s > 0,
             score_ge_0_05=s is not None and s >= 0.05, escolhido_1a=rec["p1"]["vencedor"]["topico"] in gold)
    return g


# ------------------------------------------------------------------------------------------- métricas (por ID → agregados)
def fracao(num, den):
    return {"num": num, "den": den, "valor": (num / den) if den else NA}


def registros_por_id(cap, regua):
    """Um registro por (linha, eixo avaliado): a origem de todo agregado."""
    out = []
    for sig, linhas in regua.items():
        for r in linhas:
            rec = registro(cap, sig, r["eid"])
            out += [{"curso": sig, "gold_id": r["gold_id"], "eid": r["eid"], "eixo": e, "predicao": predicao(rec, e),
                     "certo": acerta(e, r, rec)} for e in EIXOS if r[e] is not None]
    return out


def placar_de(regs, regua):
    out = {sig: {e: {"acertos": 0, "n": 0} for e in EIXOS} for sig in regua}
    for x in regs:
        c = out[x["curso"]][x["eixo"]]
        c["n"] += 1
        c["acertos"] += int(x["certo"])
    out["TOTAL"] = {e: {"acertos": sum(out[s][e]["acertos"] for s in regua), "n": sum(out[s][e]["n"] for s in regua)} for e in EIXOS}
    return out


def placar(cap, regua):
    return placar_de(registros_por_id(cap, regua), regua)


def transicoes(antes, depois, regua, eixo):
    """Registro por ID (certo/vazio antes e depois, mudou) → células → categorias derivadas e precisões."""
    regs = []
    for sig, linhas in regua.items():
        for r in linhas:
            if r[eixo] is None:
                continue
            ra, rd = registro(antes, sig, r["eid"]), registro(depois, sig, r["eid"])
            pa, pd = predicao(ra, eixo), predicao(rd, eixo)
            regs.append({"curso": sig, "gold_id": r["gold_id"], "eid": r["eid"], "antes": pa, "depois": pd,
                         "certo_antes": acerta(eixo, r, ra), "certo_depois": acerta(eixo, r, rd),
                         "vazio_antes": pa in (None, ""), "vazio_depois": pd in (None, ""), "mudou": pa != pd})
    cel = collections.Counter((int(x["certo_antes"]), int(x["certo_depois"]), int(x["vazio_antes"]), int(x["vazio_depois"]),
                               int(x["mudou"])) for x in regs)
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
    return {"registros": regs, "celulas": {"c{}{}_v{}{}_m{}".format(*k): n for k, n in sorted(cel.items())},
            "derivadas": dict(d), "precisao_alteradas": fracao(certas_alteradas, alteradas),
            "precisao_alteradas_nao_vazias": fracao(certas_nao_vazias, nao_vazias)}


def confere_transicoes(tr, pl_antes, pl_depois, eixo):
    """Somas: células = registros = n do eixo; correções − perdas = diferença de acertos."""
    prob, n = [], sum(tr["celulas"].values())
    if n != len(tr["registros"]) or n != pl_antes["TOTAL"][eixo]["n"] or n != pl_depois["TOTAL"][eixo]["n"]:
        prob.append(f"{eixo}: células ({n}) != registros ({len(tr['registros'])}) ou n do placar")
    saldo = tr["derivadas"].get("correcao", 0) - tr["derivadas"].get("perda", 0)
    if saldo != pl_depois["TOTAL"][eixo]["acertos"] - pl_antes["TOTAL"][eixo]["acertos"]:
        prob.append(f"{eixo}: correções − perdas ({saldo}) != diferença de acertos do placar")
    return prob


def confere_referencia_cru(pl_cru):
    """O CRU recapturado, com a régua desta leitura, precisa reproduzir a referência publicada POR CURSO e eixo oficial."""
    return [f"{sig}/{e}: CRU {(pl_cru.get(sig) or {}).get(e, {}).get('acertos')} != referência {ref[e]}"
            for sig, ref in K.REFERENCIA_CRU.items() for e in OFICIAIS
            if (pl_cru.get(sig) or {}).get(e, {}).get("acertos") != ref[e]]


def geracao_selecao(cru, braco, regua, tax_cru, tax_braco):
    """Escada (a)-(e) por material, com denominadores próprios (b-d só entre chamados), grupos de candidato por corte e
    seleção no subconjunto comum."""
    escada = {b: collections.Counter() for b in ("CRU", "BRACO")}
    grupos = {c: collections.Counter() for c in CORTES}
    sel = {c: {"CRU": {"p1": [0, 0], "final": [0, 0]}, "BRACO": {"p1": [0, 0], "final": [0, 0]}} for c in CORTES}
    estados = {b: collections.Counter() for b in ("CRU", "BRACO")}
    materiais = []
    for sig, linhas in regua.items():
        for r in linhas:
            g = r["sub_primaria"]
            if g is None:
                continue
            recs = {"CRU": registro(cru, sig, r["eid"]), "BRACO": registro(braco, sig, r["eid"])}
            taxs = {"CRU": tax_cru[sig], "BRACO": tax_braco[sig]}
            cand, por_lado = {}, {}
            for b, rec in recs.items():
                estados[b][estado_selecao(rec)] += 1
                if g == {""}:
                    escada[b]["gold_vazio"] += 1
                    continue
                ger = geracao_do_material(rec, g, taxs[b])
                por_lado[b] = ger
                escada[b]["n_avaliadas"] += 1
                escada[b]["a_existe"] += ger["rotulo_existe_na_taxonomia"]
                if ger["elegivel"] != NA:
                    escada[b]["chamados"] += 1
                    escada[b]["a_elegivel"] += ger["elegivel"]
                    escada[b]["b_score_pos"] += ger["score_pos"]
                    escada[b]["c_score_ge_0_05"] += ger["score_ge_0_05"]
                    escada[b]["d_escolhido_1a"] += ger["escolhido_1a"]
                escada[b]["e_final_correta"] += acerta("sub_primaria", r, rec)
                s = score_do_gold(rec, g)
                cand[b] = {c: bool(s is not None and f(s)) for c, f in CORTES.items()}
            if g == {""}:
                continue
            materiais.append({"curso": sig, "gold_id": r["gold_id"], "eid": r["eid"], **por_lado})
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
            "estados_1a": {b: dict(v) for b, v in estados.items()}, "materiais": materiais}


def meta(pl, regua):
    """>90 % estrito por contagem exata (acertos*10 > 9*n), só nos eixos avaliados de cada curso."""
    out = {}
    for sig in regua:
        out[sig] = {e: (pl[sig][e]["acertos"] * 10 > 9 * pl[sig][e]["n"]) if pl[sig][e]["n"] else NA for e in OFICIAIS}
    return out


def veredictos(pl, comp, regua):
    """A: sinal exploratório. B: contrato de integração nos TRÊS eixos oficiais; sub_aceita só relatada. C: meta."""
    sp = {b: pl[b]["TOTAL"]["sub_primaria"]["acertos"] for b in pl}
    controles = (K.CRU, K.CTRL_MAIOR, *K.CTRL_ALEAT)
    a = all(sp[K.CANDIDATO] > sp[c] for c in controles)
    t = comp[K.CANDIDATO]
    perdas = {e: t[e]["derivadas"].get("perda", 0) for e in OFICIAIS}
    regride = {e: [s for s in regua if pl[K.CANDIDATO][s][e]["acertos"] < pl[K.CRU][s][e]["acertos"]] for e in OFICIAIS}
    if sp[K.CANDIDATO] > sp[K.CRU] and not any(perdas.values()) and not any(regride.values()):
        b = "sem violação do contrato na Fase 1 condicionada à timeline congelada (não comprova integração completa)"
    elif a:
        b = "sinal exploratório observado; candidato reprovado para integração"
    else:
        b = "sem sinal exploratório"
    return {"A_sinal_exploratorio": a, "A_detalhe": {c_: sp[c_] for c_ in (K.CANDIDATO, *controles)},
            "B_integracao": b, "B_perdas": perdas, "B_cursos_que_regridem": regride,
            "B_perdas_sub_aceita_auxiliar": t["sub_aceita"]["derivadas"].get("perda", 0),
            "B_cursos_que_regridem_sub_aceita_auxiliar": [s for s in regua if pl[K.CANDIDATO][s]["sub_aceita"]["acertos"]
                                                          < pl[K.CRU][s]["sub_aceita"]["acertos"]],
            f"C_meta_{K.CANDIDATO}": meta(pl[K.CANDIDATO], regua)}


def mudancas_bloco(cru, candidato):
    """IDs (curso/eid) cuja predição de bloco difere entre CRU e candidato, em TODOS os materiais das capturas."""
    return sorted(f"{s}/{e}" for s, v in cru["decisoes"].items() for e, d in v.items()
                  if d["final"]["bloco"] != candidato["decisoes"][s][e]["final"]["bloco"])


def veredictos_rodada(pl, comp, regua, capturas):
    """Veredictos da rodada anterior, idênticos; com `invariancia_bloco` na configuração (cursos novos, bloco sem gold),
    acrescenta a invariância de bloco por ID e o B da rodada (`B_rodada`), que exige B sem violação E nenhuma mudança."""
    v = veredictos(pl, comp, regua)
    if K.R.CFG["regua"]["invariancia_bloco"]:
        mud = mudancas_bloco(capturas[K.CRU], capturas[K.CANDIDATO])
        v["B_mudancas_bloco_por_id"] = mud
        v["B_rodada"] = v["B_integracao"].startswith("sem violação") and not mud
    return v


def proveniencia(capturas, congelamento, taxonomias, regua_prov):
    return {"capturas_conteudo_sha": {b: c["conteudo_sha"] for b, c in capturas.items()},
            "congelamento_id_comum": congelamento["id_comum"], "insumos_braco": congelamento["insumos_braco"],
            "protocolo_sha": congelamento["normativo"].get("protocolo_sha"),
            "avaliador_sha": K.sha_arq(HERE / "avaliador.py"), "comum_sha": K.sha_arq(HERE / "comum.py"),
            "taxonomias_sha": {b: {s: K.sha_json(t) for s, t in v.items()} for b, v in taxonomias.items()},
            "regua": regua_prov, "copias_locais": HISTORICO}


def avalia(capturas, congelamento, regua, taxonomias, regua_prov=None):
    """Avaliação completa. Recusa conjunto inválido, régua fora do contrato e CRU que não reproduz a referência."""
    prob = valida_conjunto(capturas, congelamento) + valida_regua(regua, congelamento["normativo"]["inventario"])
    if prob:
        raise K.ErroIntegridade("avaliação recusada: " + "; ".join(prob[:8]))
    regs = {b: registros_por_id(capturas[b], regua) for b in K.BRACOS}
    pl = {b: placar_de(regs[b], regua) for b in K.BRACOS}
    ref = confere_referencia_cru(pl[K.CRU])
    if ref:
        raise K.ErroIntegridade("avaliação recusada: CRU não reproduz a referência por curso: " + "; ".join(ref[:8]))
    comp = {b: {e: transicoes(capturas[K.CRU], capturas[b], regua, e) for e in EIXOS} for b in K.BRACOS if b != K.CRU}
    somas = [p for b, v in comp.items() for e, tr in v.items() for p in confere_transicoes(tr, pl[K.CRU], pl[b], e)]
    if somas:
        raise K.ErroIntegridade("agregados não conferem com os registros por ID: " + "; ".join(somas[:8]))
    gen = {b: geracao_selecao(capturas[K.CRU], capturas[b], regua, taxonomias[K.CRU], taxonomias[b]) for b in K.BRACOS if b != K.CRU}
    return {"placar": pl, "registros": regs, "comparacoes": comp, "geracao_selecao": gen,
            "meta": {b: meta(pl[b], regua) for b in K.BRACOS}, "veredictos": veredictos_rodada(pl, comp, regua, capturas),
            "proveniencia": proveniencia(capturas, congelamento, taxonomias, regua_prov)}


# ------------------------------------------------------------------------------------------- cópias locais dos carregadores
def linhas_csv(dados):
    return list(csv.DictReader(io.StringIO(dados.decode("utf-8-sig"), newline="")))


def rotulos_bloco(dados):
    labels = {}
    for row in linhas_csv(dados):
        eid = str(row.get("id", "")).strip()
        true_block = str(row.get("true_block_id", "")).strip()
        if str(row.get("scorable", "yes") or "yes").strip().lower() == "no":
            continue
        if eid and true_block:
            if labels.get(eid, true_block) != true_block:
                raise K.ErroIntegridade(f"ground_truth: id {eid} com blocos conflitantes")
            labels[eid] = true_block
    return labels


def regua_unidade(gold_units, ground_truth, material_gt):
    truth = {}
    if gold_units is not None and ground_truth is not None:
        by_uuid = {(r.get("block_uuid") or "").strip(): (r.get("true_unit") or "").strip()
                   for r in linhas_csv(gold_units) if (r.get("true_unit") or "").strip()}
        for r in linhas_csv(ground_truth):
            if (r.get("scorable") or "").strip().lower() != "yes":
                continue
            unit = by_uuid.get((r.get("true_block_uuid") or "").strip())
            if unit:
                truth[r["id"]] = (unit,)
    if material_gt is None:
        return truth
    for r in linhas_csv(material_gt):
        if (r.get("scorable") or "yes").strip().lower() != "yes":
            continue
        units = [u.strip() for u in str(r.get("gold_units") or "").split("|") if u.strip()]
        if units:
            truth[str(r.get("entry_id") or "").strip()] = tuple(units)
    return truth


def golds_sub(dados):
    gs, gsp = {}, {}
    for r in linhas_csv(dados):
        if r["scorable"] == "yes":
            gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) \
                if r["gold_subunit"] else {""}
            gsp[r["entry_id"]] = {r["gold_subunit"]}
    return gs, gsp


def golds_de(sig, ler):
    """(gb, gu, gs, gsp). `ler(papel, sig)` devolve os bytes conferidos ou None quando o papel não existe no curso."""
    gt = ler("ground_truth", sig)
    gb = rotulos_bloco(gt) if gt is not None else {}
    gu = regua_unidade(ler("gold_units", sig), gt, ler("material_gt", sig)) if sig in UNI else {}
    sp = ler("subunit_gt", sig)
    gs, gsp = golds_sub(sp) if sp is not None else ({}, {})
    return gb, gu, gs, gsp


def origem(entry):
    value = str(entry.get("source_path") or "")
    if not value or value.startswith(("http://", "https://")):
        return value
    return str(Path(value).resolve()).casefold()


def mapeia_eids(rows, mapping, ref, saved):
    """{gold_id: eid|None} e o conjunto 'ponte'. Origem com mais de uma entrada no manifest salvo = erro (sem hits[0])."""
    index = collections.defaultdict(list)
    for e in saved.values():
        index[origem(e)].append(e)
    eid_de, ponte = {}, set()
    for row in rows:
        gid = row["entry_id"]
        if gid in eid_de:
            raise K.ErroIntegridade(f"gold_id repetido nas linhas da herança: {gid}")
        old = ref.get(mapping.get(gid) or "")
        hits = index.get(origem(old), []) if old else []
        if len(hits) > 1:
            raise K.ErroIntegridade(f"{gid}: origem ambígua ({len(hits)} entradas do manifest salvo com a mesma origem)")
        eid = str(hits[0]["id"]) if hits else None
        if eid is None and gid in saved:
            eid = gid
            ponte.add(gid)
        eid_de[gid] = eid
    return eid_de, ponte


def regua_de_estado(estado):
    """{sig: {"rows", "eid_de", "golds": (gb, gu, gs, gsp)}} → régua. Um eixo entra na linha quando a coluna não é vazia
    (contrato de W-AA/W-AB). Linha sem decisão de mapeamento ou gold ausente para eixo avaliado = erro de integridade."""
    regua = {}
    for sig, v in estado.items():
        gb, gu, gs, gsp = v["golds"]
        linhas = []
        for row in v["rows"]:
            gid = row.get("entry_id")
            if gid not in v["eid_de"]:
                raise K.ErroIntegridade(f"{sig}/{gid}: linha sem decisão de mapeamento em eid_de")
            try:
                sub = row["sub_primario"] != ""
                linhas.append({"gold_id": gid, "eid": v["eid_de"][gid],
                               "bloco": gb[gid] if row["bloco"] != "" else None,
                               "unidade": set(gu[gid]) if row["unidade"] != "" else None,
                               "sub_primaria": set(gsp[gid]) if sub else None,
                               "sub_aceita": set(gs[gid]) if sub else None})
            except KeyError as exc:
                raise K.ErroIntegridade(f"{sig}/{gid}: gold ou coluna ausente para linha avaliada ({exc})") from None
        regua[sig] = linhas
    return regua


def _json_bytes(dados):
    return json.loads(dados.decode("utf-8"), object_pairs_hook=K._sem_duplicata)


def carrega_regua_historica(congelamento=None, entradas=None, *, autorizado=False):
    """Única porta para o gold real; só com autorização explícita. Todo insumo vem do congelamento: arquivos de régua pelo
    blob git, manifests de referência pelo sha256, manifests salvos pela árvore de entradas congelada."""
    if autorizado is not True:
        raise PermissionError("leitura do gold não autorizada nesta etapa")
    desc = congelamento["normativo"]["avaliacao"]
    if desc["pendencias"]:
        raise K.ErroIntegridade(f"descritor da régua com pendências: {desc['pendencias'][:3]}")
    conferidos = {}

    def ler(papel, sig):
        item = desc["arquivos"].get(papel, {}).get(sig)
        if item is None:
            return None
        dados = (DATA / item["caminho"]).read_bytes()
        if K.blob_git(dados) != item["blob_git"]:
            raise K.ErroIntegridade(f"{item['caminho']}: bytes != blob congelado")
        conferidos[item["caminho"]] = item["blob_git"]
        return dados

    def json_conferido(caminho, sha):
        dados = (DATA / caminho).read_bytes()
        if K.sha_bytes(dados) != sha:
            raise K.ErroIntegridade(f"{caminho}: sha256 != congelado")
        return _json_bytes(dados)

    estado, mapeamento = {}, {}
    for sig in K.NOMES:
        m = desc["manifestos_referencia"][sig]
        ref = {str(e["id"]): e for e in json_conferido(m["caminho"], m["sha256"])["entries"]}
        raiz = congelamento["normativo"]["entradas_comuns"][sig]["raiz"]
        saved = {str(e["id"]): e for e in json_conferido(f"{raiz}/manifest.json", entradas[sig]["manifest.json"])["entries"]}
        mapping = {}
        for e in _json_bytes(ler("herancas_json", sig))["entries"]:
            if mapping.get(e["entry_id"], e["new_id"]) != e["new_id"]:
                raise K.ErroIntegridade(f"{sig}: herança com destinos conflitantes para {e['entry_id']}")
            mapping[e["entry_id"]] = e["new_id"]
        rows = linhas_csv(ler("herancas_csv", sig))
        eid_de, ponte = mapeia_eids(rows, mapping, ref, saved)
        estado[sig] = {"rows": rows, "eid_de": eid_de, "golds": golds_de(sig, ler)}
        mapeamento[sig] = {"ponte": sorted(ponte), "ausentes": sorted(g for g, e in eid_de.items() if e is None)}
    regua = regua_de_estado(estado)
    return regua, {"arquivos_conferidos": conferidos, "mapeamento": mapeamento, "regua_efetiva_sha": K.sha_json(regua)}


def carrega_gold_externo(congelamento=None, entradas=None, *, autorizado=False):
    """Porta do gold externo; só com autorização. Gold, rótulos e mapa material->entry vêm do descritor do congelamento,
    cada um conferido contra o blob git congelado; os bytes interpretados são os bytes conferidos."""
    if autorizado is not True:
        raise PermissionError("leitura do gold não autorizada nesta etapa")
    desc = congelamento["normativo"]["avaliacao"]
    if desc["pendencias"]:
        raise K.ErroIntegridade(f"descritor da régua com pendências: {desc['pendencias'][:3]}")
    conferidos, regua, resumo = {}, {}, {}

    def ler(papel, sig):
        item = desc["arquivos"][papel][sig]
        dados = (DATA / item["caminho"]).read_bytes()
        if K.blob_git(dados) != item["blob_git"]:
            raise K.ErroIntegridade(f"{item['caminho']}: bytes != blob congelado")
        conferidos[item["caminho"]] = item["blob_git"]
        return dados

    for sig in K.NOMES:
        rot = _json_bytes(ler("rotulos", sig))
        mapa_doc = _json_bytes(ler("mapa", sig))
        linhas = GE.le_csv(ler("gold", sig))
        prob = GE.valida(linhas, sorted(mapa_doc["mapa"]), rot)
        if prob:
            raise K.ErroIntegridade(f"{sig}: gold inválido: {prob[:3]}")
        regua[sig], resumo[sig] = GE.regua(linhas, rot, mapa_doc["mapa"])
    return regua, {"arquivos_conferidos": conferidos, "mapeamento": resumo, "regua_efetiva_sha": K.sha_json(regua)}


def carrega_regua(congelamento=None, entradas=None, *, autorizado=False):
    """Escolhe o carregador pela configuração congelada da rodada (régua histórica ou gold externo)."""
    if K.R.CFG["regua"]["tipo"] == "gold_externo":
        return carrega_gold_externo(congelamento, entradas, autorizado=autorizado)
    return carrega_regua_historica(congelamento, entradas, autorizado=autorizado)


def carrega_taxonomias(congelamento, snap_dir):
    """Snapshots de taxonomia por braço/curso, conferidos contra o congelamento (bytes conferidos = bytes lidos)."""
    out = {}
    for b in K.BRACOS:
        out[b] = {}
        for sig in K.NOMES:
            dados = (Path(snap_dir) / b / sig / "taxonomia.json").read_bytes()
            if K.sha_bytes(dados) != congelamento["insumos"][b][sig]["taxonomia_arquivo_sha"]:
                raise K.ErroIntegridade(f"snapshot de taxonomia {b}/{sig} não confere")
            out[b][sig] = _json_bytes(dados)
    return out


def main():
    """Uso futuro: python avaliador.py --autorizo-gold <dir_capturas> <congelamento.json> <dir_snapshots> <saida.json>.
    Ordem obrigatória: código do avaliador, congelamento, entradas e capturas validados ANTES de qualquer leitura de gold."""
    if "--autorizo-gold" not in sys.argv:
        print("avaliação real não autorizada nesta etapa (adendo v3 §9)", flush=True)
        sys.exit(2)
    args = [a for a in sys.argv[1:] if a != "--autorizo-gold"]
    if len(args) != 4:
        print(main.__doc__, flush=True)
        sys.exit(2)
    caps_dir, cong_path, snap_dir, saida = map(Path, args)
    cong = K.carrega_json_estrito(cong_path)
    prob = K.valida_congelamento(cong)
    prob += K.verifica_codigo({n: cong["normativo"]["codigo"].get(n) for n in ("avaliador.py", "comum.py")},
                              {"avaliador.py": HERE / "avaliador.py", "comum.py": HERE / "comum.py"})
    entradas = K.carrega_json_estrito(cong_path.parent / "congelamento_entradas.json")
    if K.sha_json(entradas) != cong["normativo"]["entradas_arquivo_sha"]:
        prob.append("congelamento de entradas divergente")
    if prob:
        raise K.ErroIntegridade("pré-avaliação recusada: " + "; ".join(prob[:8]))
    capturas = {b: K.carrega_json_estrito(caps_dir / f"capturar_{b}_{cong['id_comum'][:16]}_{cong['insumos_braco'][b][:16]}.json")
                for b in K.BRACOS}
    prob = valida_conjunto(capturas, cong)
    if prob:
        raise K.ErroIntegridade("capturas inválidas: " + "; ".join(prob[:8]))
    taxonomias = carrega_taxonomias(cong, snap_dir)
    regua, prov = carrega_regua(cong, entradas, autorizado=True)   # só depois das validações acima
    K.grava_atomico(saida, K.canon(avalia(capturas, cong, regua, taxonomias, prov)))


if __name__ == "__main__":
    main()
