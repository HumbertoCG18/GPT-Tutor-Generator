"""Gold externo (`gold-externo-1`): leitura estrita, validação, ligação com as entries e tradução para a régua do
avaliador (contrato da rodada VOCAB_LIMPO). Só stdlib; nunca lê saída do motor.

Régua: lista de linhas {"gold_id", "eid", "bloco", "unidade", "sub_primaria", "sub_aceita"} por curso; None = eixo não
avaliado; {""} = o vazio é a resposta certa; eid None = material ausente (conta como erro). Bloco é sempre None (não é
rotulado nos cursos novos).
"""
import csv
import io
import re

CAMPOS = ["material_id", "status", "unidade", "sub_primaria", "sub_aceita", "observacao"]
STATUS = ("avaliado", "meta", "excluido")
ID_MATERIAL = re.compile(r"^m[0-9a-f]{12}$")
CAMPOS_ENTRY_PERMITIDOS = ("id", "sha256")   # únicos campos de entry usados na ligação


class GoldInvalido(ValueError):
    pass


def le_csv(dados):
    """Bytes UTF-8 sem BOM, LF, cabeçalho exato. Devolve a lista de linhas (dicts com as 6 colunas)."""
    if dados.startswith(b"\xef\xbb\xbf"):
        raise GoldInvalido("BOM não permitido")
    if b"\r" in dados:
        raise GoldInvalido("fim de linha CRLF não permitido (LF)")
    texto = dados.decode("utf-8")
    leitor = csv.reader(io.StringIO(texto, newline=""))
    linhas = list(leitor)
    if not linhas or linhas[0] != CAMPOS:
        raise GoldInvalido(f"cabeçalho != {CAMPOS}")
    out = []
    for i, ln in enumerate(linhas[1:], 2):
        if len(ln) != len(CAMPOS):
            raise GoldInvalido(f"linha {i}: {len(ln)} colunas")
        out.append(dict(zip(CAMPOS, ln)))
    return out


def _ids(celula):
    return [] if celula in ("", "-") else celula.split("|")


def valida(linhas, adjudicaveis, rotulos):
    """Todas as regras do schema. `adjudicaveis`: material_ids do pacote; `rotulos`: conteúdo de rotulos.json."""
    prob = []
    unidades = {u["id"] for u in rotulos["unidades"]}
    topico_unidade = {t["id"]: t["unidade"] for t in rotulos["topicos"]}
    vistos = [ln["material_id"] for ln in linhas]
    if len(set(vistos)) != len(vistos):
        prob.append("material_id repetido")
    if set(vistos) != set(adjudicaveis):
        prob.append(f"material_id diferente dos adjudicáveis: faltam {sorted(set(adjudicaveis) - set(vistos))[:3]}, "
                    f"sobram {sorted(set(vistos) - set(adjudicaveis))[:3]}")
    for ln in linhas:
        mid, st = ln["material_id"], ln["status"]
        onde = f"{mid}"
        if not ID_MATERIAL.match(mid):
            prob.append(f"{onde}: material_id inválido")
        if st not in STATUS:
            prob.append(f"{onde}: status inválido {st!r}")
            continue
        for campo in ("unidade", "sub_primaria", "sub_aceita"):
            v = ln[campo]
            if v != v.strip() or any(x != x.strip() or not x for x in _ids(v)) or len(set(_ids(v))) != len(_ids(v)):
                prob.append(f"{onde}: {campo} com espaço, vazio interno ou repetição")
        if st == "excluido":
            if any(ln[c] for c in ("unidade", "sub_primaria", "sub_aceita")):
                prob.append(f"{onde}: excluido exige unidade e subunidade vazias")
            continue
        if not ln["unidade"]:
            prob.append(f"{onde}: unidade obrigatória")
        us = _ids(ln["unidade"])
        prob += [f"{onde}: unidade desconhecida {u}" for u in us if u not in unidades]
        if st == "meta":
            if ln["sub_primaria"] or ln["sub_aceita"]:
                prob.append(f"{onde}: meta exige subunidade vazia")
            continue
        if not ln["sub_primaria"] or not ln["sub_aceita"]:
            prob.append(f"{onde}: sub_primaria e sub_aceita obrigatórias")
            continue
        pri, ace = _ids(ln["sub_primaria"]), _ids(ln["sub_aceita"])
        if (ln["sub_primaria"] == "-") != (ln["sub_aceita"] == "-"):
            prob.append(f"{onde}: '-' em só uma das subunidades")
        if ln["unidade"] == "-" and ln["sub_primaria"] != "-":
            prob.append(f"{onde}: unidade '-' exige subunidade '-'")
        prob += [f"{onde}: tópico desconhecido {t}" for t in pri + ace if t not in topico_unidade]
        prob += [f"{onde}: tópico {t} fora das unidades da linha" for t in pri + ace
                 if t in topico_unidade and topico_unidade[t] not in us]
        if not set(pri) <= set(ace):
            prob.append(f"{onde}: sub_primaria não contida em sub_aceita")
    return prob


def mapa_por_hash(materiais, entradas):
    """material_id -> lista ordenada de eids com os mesmos bytes brutos. `entradas`: [{"id", "sha256"}] (só esses campos)."""
    for e in entradas:
        if set(e) != set(CAMPOS_ENTRY_PERMITIDOS):
            raise GoldInvalido(f"entry com campos além de {CAMPOS_ENTRY_PERMITIDOS}: {sorted(e)}")
    por_sha = {}
    for e in entradas:
        por_sha.setdefault(e["sha256"], []).append(str(e["id"]))
    return {m["material_id"]: sorted(por_sha.get(m["sha256"], [])) for m in materiais if m["adjudicavel"]}


def regua(linhas, rotulos, mapa):
    """Tradução para a régua. Linha replicada para cada entry com os mesmos bytes (gold_id = material@eid); sem entry =
    uma linha com eid None (material ausente). `excluido` não gera linha."""
    slug_u = {u["id"]: u["slug"] for u in rotulos["unidades"]}
    slug_t = {t["id"]: t["slug"] for t in rotulos["topicos"]}

    def conj(celula, slugs):
        return {""} if celula == "-" else {slugs[x] for x in celula.split("|")}

    out, resumo = [], {"linhas_gold": len(linhas), "excluidos": 0, "ausentes": 0, "replicados": 0}
    for ln in linhas:
        if ln["status"] == "excluido":
            resumo["excluidos"] += 1
            continue
        uni = conj(ln["unidade"], slug_u)
        pri = conj(ln["sub_primaria"], slug_t) if ln["status"] == "avaliado" else None
        ace = conj(ln["sub_aceita"], slug_t) if ln["status"] == "avaliado" else None
        eids = mapa.get(ln["material_id"]) or []
        if not eids:
            resumo["ausentes"] += 1
        if len(eids) > 1:
            resumo["replicados"] += len(eids) - 1
        for eid in eids or [None]:
            gid = ln["material_id"] if len(eids) <= 1 else f"{ln['material_id']}@{eid}"
            out.append({"gold_id": gid, "eid": eid, "bloco": None, "unidade": set(uni),
                        "sub_primaria": None if pri is None else set(pri), "sub_aceita": None if ace is None else set(ace)})
    return out, resumo


def denominadores(linhas_regua):
    return {"bloco": 0, "unidade": sum(1 for r in linhas_regua if r["unidade"] is not None),
            "sub_primaria": sum(1 for r in linhas_regua if r["sub_primaria"] is not None)}
