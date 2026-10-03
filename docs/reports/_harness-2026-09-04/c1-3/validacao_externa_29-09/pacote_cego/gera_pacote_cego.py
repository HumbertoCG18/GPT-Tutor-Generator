"""Gerador e auditor do pacote cego de adjudicação (validação externa do regime VOCAB, versão `pacote-cego-1`, 29/09).

Constrói o pacote SÓ de fontes brutas permitidas: o download do Moodle (arquivos publicados, páginas HTML e o
`raw/moodle/contents.json` da API, restrito a campos permitidos) e o plano de ensino (arquivo original + texto). Todo
acesso passa por `Leitor`, que recusa arquivos gerados pelo produto e saídas do motor (manifest, taxonomia, timeline,
sidecars, `links.json`, `manual-review/` etc.) e qualquer caminho fora das raízes declaradas.

O único derivado computado por código do produto é `rotulos.json`: `content_taxonomy.build_content_taxonomy` chamado
com o texto do plano e NADA mais (sem glossário, headings, materiais ou mapa do curso); os aliases saem vazios e são
exigidos vazios. Nenhum replay, captura, score, confiança ou motivo é calculado ou lido.

Uso:
  python gera_pacote_cego.py gerar <fonte.json> <destino>     (recusa destino existente)
  python gera_pacote_cego.py auditar <fonte.json> <pacote>    (saída 0 = aprovado)
`fonte.json`: {"sigla", "nome", "moodle_dir", "plano_arquivo", "plano_texto"} (caminhos absolutos).
"""
import csv
import hashlib
import html
import html.parser
import io
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

VERSAO = "pacote-cego-1"
AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[5]
INSTRUCOES = AQUI.parent / "gold" / "instrucoes_adjudicador.md"
CAMPOS_GOLD = ["material_id", "status", "unidade", "sub_primaria", "sub_aceita", "observacao"]

# ---------------------------------------------------------------- o que nunca pode ser lido nem copiado
NOME_NEGADO = re.compile(
    r"^(links\.json|manifest\.json(\.bak)?|\.content_taxonomy\.json|\.timeline_index\.json|\.card_block_map\.json|"
    r"\.lessons_index\.json|\.glossary_curation.*\.json|\.moodle_nomes\.json|_ARQUIVOS_DO_CARD\.txt|code_curation\.json|"
    r"material_curation\.json|references_curation\.json|FILE_MAP.*\.md|COURSE_MAP\.md|GLOSSARY\.md|sections\.json|"
    r"labels\.json|site_links\.json|.*captur.*\.json|.*placar.*|.*avaliacao.*\.json)$", re.I)
PARTE_NEGADA = {"manual-review", ".frzero", "site", "__pycache__", "course", "build", "content", "staging"}
RAIZ_NEGADA = re.compile(r".+-Tutor|GPT-Tutor-Generator.*")   # por COMPONENTE do caminho (fullmatch), nunca substring
# permitido explicitamente dentro de raw/moodle: só a resposta crua da API e as páginas
PERMITIDO_RAW = re.compile(r"(^|/)raw/moodle/(contents\.json|pages/[^/]+\.html?)$")

# campos da API do Moodle que podem entrar no pacote (autor, usuário, licença e afins ficam fora)
SECAO_OK = ("section", "name", "summary")
MODULO_OK = ("id", "name", "modname", "description", "url", "contents")
CONTEUDO_OK = ("type", "filename", "filepath", "filesize", "fileurl")

# chaves permitidas em cada JSON do pacote (allowlist positiva)
CHAVES_OK = {
    "materiais.json": {"versao", "sigla", "materiais", "material_id", "tipo", "adjudicavel", "arquivo", "nome_original",
                       "ocorrencias", "secao", "modulo", "modname", "sha256", "tamanho", "url"},
    "moodle_estrutura.json": {"versao", "sigla", "formato", "secoes", "numero", "nome", "resumo", "rotulos", "secao",
                              "texto", "modulos", "modname"},
    "rotulos.json": {"versao", "sigla", "origem", "unidades", "topicos", "id", "slug", "titulo", "unidade", "rotulo", "codigo"},
    "pacote_manifesto.json": {"versao", "sigla", "gerador_sha256", "instrucoes_sha256", "arquivos", "sha256", "origem",
                              "tipo", "fonte", "fonte_sha256", "funcao", "entradas"},
}
# padrões de predição/saída do motor que não podem aparecer em nenhum arquivo gerado (nomes ou valores)
PADRAO_PREDICAO = re.compile(
    r"computed_(block|unit|subunit)|temporal_block_id|unit_match|subunit_match|match_confidence|winner_score|"
    r"assignment_run|auto_tags|glossary_curation|propagado-headings|secao-nomeia-subtopico|\bbloco-\d{2}\b", re.I)
# Nomes genéricos (score, confidence, reasons, captura, placar) podem aparecer no texto do professor ("captura de
# pacotes"); como NOME DE CAMPO eles já são barrados pela allowlist de chaves.
GERADOS = ("materiais.json", "moodle_estrutura.json", "rotulos.json", "gold_modelo.csv", "INSTRUCOES.md",
           "declaracao_cegamento.md")


class AcessoNegado(RuntimeError):
    pass


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


class Leitor:
    """Única porta de leitura. Registra cada arquivo lido (caminho relativo à raiz permitida + sha256)."""

    def __init__(self, raizes):
        self.raizes = [Path(r).resolve() for r in raizes]
        self.lidos = {}

    def rel(self, p):
        p = Path(p).resolve()
        for r in self.raizes:
            if p == r or r in p.parents:
                return r, p.relative_to(r).as_posix() if p != r else p.name
        raise AcessoNegado(f"fora das raízes permitidas: {p}")

    def confere(self, p):
        p = Path(p).resolve()
        raiz, rel = self.rel(p)
        if any(RAIZ_NEGADA.fullmatch(parte) for parte in p.parts):
            raise AcessoNegado(f"repositório de tutor ou do gerador: {p}")
        partes = set(Path(rel).parts[:-1])
        if "raw" in Path(rel).parts:
            if not PERMITIDO_RAW.search(rel):
                raise AcessoNegado(f"arquivo bruto não permitido: {rel}")
        elif partes & PARTE_NEGADA or NOME_NEGADO.match(p.name):
            raise AcessoNegado(f"gerado pelo produto ou saída do motor: {rel}")
        return raiz, rel

    def le(self, p):
        raiz, rel = self.confere(p)
        dados = Path(p).read_bytes()
        self.lidos[str(Path(p).resolve())] = sha_b(dados)
        return dados


class _Texto(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.partes = []

    def handle_data(self, d):
        self.partes.append(d)


def texto_html(s):
    t = _Texto()
    t.feed(str(s or ""))
    return re.sub(r"\s+", " ", html.unescape(" ".join(t.partes))).strip()


def nome_seguro(nome):
    return re.sub(r"[^\w.\- ]+", "_", nome, flags=re.UNICODE).strip()[:120] or "arquivo"


def id_material(chave):
    return "m" + sha_b(chave.encode("utf-8"))[:12]


def arquivos_locais(leitor, moodle_dir):
    """Arquivos de material do download (fora os negados), por nome, com tamanho e sha256."""
    out = []
    for p in sorted(Path(moodle_dir).rglob("*")):
        if not p.is_file():
            continue
        try:
            leitor.confere(p)
        except AcessoNegado:
            continue
        rel = p.relative_to(moodle_dir).as_posix()
        if rel == "raw/moodle/contents.json":
            continue
        out.append({"caminho": p, "rel": rel, "nome": p.name, "tamanho": p.stat().st_size})
    return out


def rotulos_do_plano(texto_plano):
    """Espaço de rótulos congelado: build_content_taxonomy SÓ com o texto do plano (código do produto, sem materiais)."""
    _rt = Path.read_text

    def sem_env(self, *a, **k):
        if self.name == ".env":
            raise PermissionError(".env bloqueado")
        return _rt(self, *a, **k)

    Path.read_text = sem_env
    try:
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        from src.builder.extraction import content_taxonomy as CT
        from src.builder.extraction.teaching_plan import _normalize_unit_slug, _parse_units_from_teaching_plan, _topic_text
        tax = CT.build_content_taxonomy(teaching_plan=texto_plano, course_map_md="", glossary_md="", strong_headings=None,
                                        semantic_profile=None, parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
                                        topic_text=_topic_text, normalize_unit_slug=_normalize_unit_slug)
    finally:
        Path.read_text = _rt
    unidades, topicos = [], []
    for i, u in enumerate(tax.get("units") or [], 1):
        uid = f"U{i:02d}"
        unidades.append({"id": uid, "slug": u["slug"], "titulo": u["title"]})
        for j, t in enumerate(u.get("topics") or [], 1):
            if t.get("aliases"):
                raise RuntimeError(f"alias em tópico derivado só do plano: {t['slug']}")
            topicos.append({"id": f"{uid}.T{j:02d}", "unidade": uid, "slug": t["slug"], "rotulo": t["label"],
                            "codigo": t.get("code") or ""})
    if not unidades:
        raise RuntimeError("plano sem unidades extraíveis: pacote não pode ser gerado")
    return unidades, topicos


def descobre(leitor, fonte):
    """Materiais e estrutura do Moodle, só de fontes brutas permitidas."""
    moodle = Path(fonte["moodle_dir"])
    locais = arquivos_locais(leitor, moodle)
    por_nome = {}
    for a in locais:
        por_nome.setdefault((a["nome"], a["tamanho"]), []).append(a)
    materiais, estrutura = {}, {"formato": None, "secoes": [], "rotulos": [], "modulos": []}
    usados = set()

    def acrescenta(chave, reg, ocorr):
        m = materiais.setdefault(chave, {**reg, "ocorrencias": []})
        if ocorr not in m["ocorrencias"]:
            m["ocorrencias"].append(ocorr)

    cj = moodle / "raw/moodle/contents.json"
    if cj.is_file():
        estrutura["formato"] = "api"
        for sec_api in json.loads(leitor.le(cj).decode("utf-8")):
            sec = {k: sec_api.get(k) for k in SECAO_OK}
            num, nome_sec = sec["section"], str(sec["name"] or "")
            estrutura["secoes"].append({"numero": num, "nome": nome_sec, "resumo": texto_html(sec["summary"])})
            for mod_api in sec_api.get("modules") or []:
                mod = {k: mod_api.get(k) for k in MODULO_OK}
                modname, nome_mod = str(mod["modname"]), str(mod["name"] or "")
                estrutura["modulos"].append({"secao": nome_sec, "nome": nome_mod, "modname": modname})
                ocorr = {"secao": nome_sec, "modulo": nome_mod, "modname": modname}
                if modname == "label":
                    estrutura["rotulos"].append({"secao": nome_sec, "texto": texto_html(mod["description"])})
                elif modname == "url":
                    url = str(mod["url"] or "")
                    acrescenta("url:" + url, {"tipo": "link_externo", "adjudicavel": False, "arquivo": None,
                                              "nome_original": nome_mod, "sha256": None, "tamanho": None, "url": url}, ocorr)
                elif modname == "page":
                    for a in [x for x in locais if x["rel"].startswith(f"raw/moodle/pages/{mod['id']}-")][:1]:
                        usados.add(a["rel"])
                        acrescenta("arq:" + sha_b(leitor.le(a["caminho"])), {"tipo": "pagina", "adjudicavel": True, "fonte": a,
                                                                            "nome_original": a["nome"]}, ocorr)
                elif modname in ("resource", "folder", "assign"):
                    for c in mod["contents"] or []:
                        c = {k: c.get(k) for k in CONTEUDO_OK}
                        if c["type"] != "file":
                            continue
                        cand = por_nome.get((c["filename"], c["filesize"]), [])
                        if not cand:
                            acrescenta("semfonte:" + str(c["filename"]), {"tipo": "arquivo_sem_fonte_local", "adjudicavel": False,
                                                                         "arquivo": None, "nome_original": c["filename"],
                                                                         "sha256": None, "tamanho": c["filesize"], "url": None}, ocorr)
                            continue
                        for a in cand:
                            usados.add(a["rel"])
                            acrescenta("arq:" + sha_b(leitor.le(a["caminho"])), {"tipo": "arquivo", "adjudicavel": True, "fonte": a,
                                                                                "nome_original": c["filename"]}, ocorr)
        sobras = [a for a in locais if a["rel"] not in usados]
    else:
        estrutura["formato"] = "pastas"
        sobras = locais
    for a in sobras:   # arquivos locais sem módulo correspondente: seção = pasta de primeiro nível
        secao = a["rel"].split("/", 1)[0] if "/" in a["rel"] else ""
        if estrutura["formato"] == "pastas" and secao and secao not in [s["nome"] for s in estrutura["secoes"]]:
            estrutura["secoes"].append({"numero": None, "nome": secao, "resumo": ""})
        acrescenta("arq:" + sha_b(leitor.le(a["caminho"])), {"tipo": "arquivo", "adjudicavel": True, "fonte": a,
                                                            "nome_original": a["nome"]},
                   {"secao": secao, "modulo": "", "modname": ""})
    return materiais, estrutura


def json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")


def monta(fonte, destino):
    """Gera o pacote em `destino` (não pode existir). Determinístico: mesma fonte = mesmos bytes."""
    destino = Path(destino)
    if destino.exists():
        raise FileExistsError(f"destino já existe: {destino}")
    plano_arq, plano_txt = Path(fonte["plano_arquivo"]), Path(fonte["plano_texto"])
    leitor = Leitor([fonte["moodle_dir"], plano_arq, plano_txt])   # instruções = documento do protocolo, lido à parte
    materiais, estrutura = descobre(leitor, fonte)
    unidades, topicos = rotulos_do_plano(leitor.le(plano_txt).decode("utf-8"))
    arquivos, lista = {}, []
    destino.mkdir(parents=True)

    def grava(rel, dados, origem):
        p = destino / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(dados)
        arquivos[rel] = {"sha256": sha_b(dados), "origem": origem}

    for chave in sorted(materiais, key=lambda k: id_material(k)):
        m = materiais[chave]
        mid = id_material(chave)
        reg = {"material_id": mid, "tipo": m["tipo"], "adjudicavel": m["adjudicavel"], "nome_original": m["nome_original"],
               "ocorrencias": sorted(m["ocorrencias"], key=lambda o: (o["secao"], o["modulo"], o["modname"]))}
        if "fonte" in m:
            dados = leitor.le(m["fonte"]["caminho"])
            rel = f"materiais/{mid}__{nome_seguro(m['nome_original'])}"
            grava(rel, dados, {"tipo": "bruto", "fonte": "moodle:" + m["fonte"]["rel"], "fonte_sha256": sha_b(dados)})
            reg.update(arquivo=rel, sha256=sha_b(dados), tamanho=len(dados), url=None)
        else:
            reg.update(arquivo=None, sha256=m["sha256"], tamanho=m["tamanho"], url=m["url"])
        lista.append(reg)
    for p, nome in ((plano_arq, "plano/" + nome_seguro(plano_arq.name)), (plano_txt, "plano/plano_texto" + plano_txt.suffix)):
        dados = leitor.le(p)
        grava(nome, dados, {"tipo": "bruto", "fonte": "plano:" + p.name, "fonte_sha256": sha_b(dados)})
    base = {"versao": VERSAO, "sigla": fonte["sigla"]}
    derivado = lambda funcao, *ent: {"tipo": "derivado", "funcao": funcao, "entradas": sorted(ent)}
    grava("materiais.json", json_bytes({**base, "materiais": lista}), derivado("descobre", "moodle"))
    grava("moodle_estrutura.json", json_bytes({**base, **estrutura}), derivado("descobre", "moodle:raw/moodle/contents.json"))
    grava("rotulos.json", json_bytes({**base, "origem": "content_taxonomy.build_content_taxonomy(texto do plano, '', '', None)",
                                      "unidades": unidades, "topicos": topicos}), derivado("rotulos_do_plano", "plano:" + plano_txt.name))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CAMPOS_GOLD)
    for reg in lista:
        if reg["adjudicavel"]:
            w.writerow([reg["material_id"], "", "", "", "", ""])
    grava("gold_modelo.csv", buf.getvalue().encode("utf-8"), derivado("monta", "materiais.json"))
    grava("INSTRUCOES.md", INSTRUCOES.read_bytes(), {"tipo": "bruto", "fonte": "protocolo:" + INSTRUCOES.name,
                                                    "fonte_sha256": sha_b(INSTRUCOES.read_bytes())})
    decl = INSTRUCOES.read_text(encoding="utf-8").split("```text", 1)[1].split("```", 1)[0].strip() + "\n"
    grava("declaracao_cegamento.md", decl.encode("utf-8"), derivado("monta", "protocolo:" + INSTRUCOES.name))
    manifesto = {**base, "gerador_sha256": sha_b(Path(__file__).read_bytes()), "instrucoes_sha256": sha_b(INSTRUCOES.read_bytes()),
                 "arquivos": arquivos}
    (destino / "pacote_manifesto.json").write_bytes(json_bytes(manifesto))
    return manifesto


def _chaves(o, out):
    if isinstance(o, dict):
        for k, v in o.items():
            out.add(k)
            _chaves(v, out)
    elif isinstance(o, list):
        for x in o:
            _chaves(x, out)
    return out


def audita(fonte, pacote):
    """Auditoria negativa + allowlist positiva + procedência. Devolve a lista de problemas (vazia = aprovado)."""
    pacote, prob = Path(pacote), []
    man = json.loads((pacote / "pacote_manifesto.json").read_text(encoding="utf-8"))
    no_disco = {p.relative_to(pacote).as_posix() for p in pacote.rglob("*") if p.is_file()} - {"pacote_manifesto.json"}
    if no_disco != set(man["arquivos"]):
        prob.append(f"arquivos fora do manifesto ou faltando: {sorted(no_disco ^ set(man['arquivos']))[:5]}")
    for rel, info in man["arquivos"].items():
        p = pacote / rel
        if p.is_file() and sha_b(p.read_bytes()) != info["sha256"]:
            prob.append(f"{rel}: sha256 != manifesto")
        if info["origem"]["tipo"] == "bruto" and info["origem"]["fonte_sha256"] != info["sha256"]:
            prob.append(f"{rel}: cópia bruta difere da fonte declarada")
        if not (rel.startswith(("materiais/", "plano/")) or rel in GERADOS):
            prob.append(f"{rel}: arquivo fora do leiaute permitido")
    for nome, ok in CHAVES_OK.items():
        obj = json.loads((pacote / nome).read_text(encoding="utf-8"))
        if nome == "pacote_manifesto.json":   # as chaves de "arquivos" são caminhos, não campos
            obj = {**obj, "arquivos": list(obj.get("arquivos", {}).values())}
        extras = _chaves(obj, set()) - ok
        if extras:
            prob.append(f"{nome}: chaves fora da allowlist {sorted(extras)}")
    for nome in GERADOS + ("pacote_manifesto.json",):
        if nome == "INSTRUCOES.md":
            continue
        achado = PADRAO_PREDICAO.search((pacote / nome).read_text(encoding="utf-8"))
        if achado:
            prob.append(f"{nome}: padrão de predição/saída do motor: {achado.group(0)!r}")
    rot = json.loads((pacote / "rotulos.json").read_text(encoding="utf-8"))
    ids_u = {u["id"] for u in rot["unidades"]}
    if any(t["unidade"] not in ids_u for t in rot["topicos"]):
        prob.append("rotulos.json: tópico de unidade inexistente")
    # procedência: regenerar numa pasta temporária a partir da MESMA fonte e exigir bytes idênticos em tudo
    with tempfile.TemporaryDirectory() as tmp:
        try:
            ref = monta(fonte, Path(tmp) / "ref")
        except Exception as exc:   # noqa: BLE001
            prob.append(f"regeneração falhou: {type(exc).__name__}: {exc}")
        else:
            if ref["arquivos"] != man["arquivos"]:
                dif = sorted(k for k in set(ref["arquivos"]) | set(man["arquivos"]) if ref["arquivos"].get(k) != man["arquivos"].get(k))
                prob.append(f"regeneração a partir da fonte difere: {dif[:5]}")
            if (Path(tmp) / "ref/pacote_manifesto.json").read_bytes() != (pacote / "pacote_manifesto.json").read_bytes():
                prob.append("pacote_manifesto.json difere da regeneração")
    return prob


def main():
    acao, fonte_json, alvo = sys.argv[1:4]
    fonte = json.loads(Path(fonte_json).read_text(encoding="utf-8"))
    if acao == "gerar":
        m = monta(fonte, alvo)
        print(f"pacote gerado: {len(m['arquivos'])} arquivos")
        prob = audita(fonte, alvo)
    elif acao == "auditar":
        prob = audita(fonte, alvo)
    else:
        sys.exit("ação desconhecida")
    print("AUDITORIA", "APROVADA" if not prob else "REPROVADA", *prob, sep="\n")
    sys.exit(1 if prob else 0)


if __name__ == "__main__":
    main()
