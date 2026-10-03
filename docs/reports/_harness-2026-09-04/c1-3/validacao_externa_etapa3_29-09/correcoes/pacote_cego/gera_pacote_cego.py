"""Gerador e auditor do pacote cego de adjudicação, versão `pacote-cego-3` (etapa 3, 29/09).

Correções da v3 sobre a v2 (../../../validacao_externa_etapa2_29-09/correcoes/pacote_cego/gera_pacote_cego.py):
5. **plano:** arquivo e texto do plano passam por `verifica_material`; recusa = pacote não gerado (`PlanoRecusado`);
   a auditoria também verifica `plano/`;
6. **contêineres:** política explícita de membros para ZIP, OOXML e ODF e de anexos em PDF (`verifica_conteiner`);
7. **proveniência primeiro:** com `inventario` + `curso_id` na fonte, recurso -> arquivo sai do registro da aquisição
   (módulo, arquivo, caminho, sha256 conferido); item não adquirido fica visível e não adjudicável. Sem inventário,
   nome + tamanho só ligam dentro da pasta da seção do módulo (candidato só em outra seção = `origem_nao_confirmada`);
   o método de ligação de cada fonte fica no manifesto (`ligacao`); anexos de página são registrados, não entregues.

Correções da v2 sobre a v1 (../../../validacao_externa_29-09/pacote_cego/gera_pacote_cego.py):
1. **sem configurações nem segredos:** arquivos de configuração/credencial recusados por nome, extensão e conteúdo
   (`.env`, `*.ini/.toml/.pem/.key`, `config*.json`, nomes com token/segredo/senha/cookie; textos com chave de API,
   `MOODLE_TOKEN=`, chave privada etc.); URLs sem parâmetros de autenticação;
2. **sem saídas renomeadas:** só extensões da allowlist; binário tem de ter a assinatura (magic bytes) da extensão;
   todo arquivo de texto é varrido por assinaturas do motor; o recusado não é copiado e fica registrado com o motivo;
3. **correspondência Moodle -> arquivo inequívoca:** nome + tamanho; empate entre bytes diferentes só se resolve pela
   pasta da seção do módulo; se ainda sobrar mais de um candidato, a geração FALHA (`AmbiguidadeOrigem`);
4. **procedência completa:** o manifesto lista cada arquivo lido (papel e sha256) e cada arquivo da fonte NÃO usado
   (motivo); a auditoria exige que todo arquivo da fonte esteja em uma das duas listas.
O resto (leitor restrito, rótulos só do plano, allowlist de chaves, regeneração byte a byte) é o da v1.

Uso:
  python gera_pacote_cego.py gerar <fonte.json> <destino>     (recusa destino existente)
  python gera_pacote_cego.py auditar <fonte.json> <pacote>    (saída 0 = aprovado)
`fonte.json`: {"sigla", "nome", "moodle_dir", "plano_arquivo", "plano_texto"[, "inventario", "curso_id"]} (caminhos absolutos).
"""
import csv
import hashlib
import html
import html.parser
import io
import json
import re
import sys
import tempfile
import unicodedata
import urllib.parse
import zipfile
from pathlib import Path

VERSAO = "pacote-cego-3"
AQUI = Path(__file__).resolve().parent
REPO = next(p for p in AQUI.parents if (p / ".git").exists())
INSTRUCOES = REPO / "docs/reports/_harness-2026-09-04/c1-3/validacao_externa_29-09/gold/instrucoes_adjudicador.md"
CAMPOS_GOLD = ["material_id", "status", "unidade", "sub_primaria", "sub_aceita", "observacao"]

# ---------------------------------------------------------------- nunca lido: gerados do produto e saídas do motor
NOME_NEGADO = re.compile(
    r"^(links\.json|manifest\.json(\.bak)?|\.content_taxonomy\.json|\.timeline_index\.json|\.card_block_map\.json|"
    r"\.lessons_index\.json|\.glossary_curation.*\.json|\.moodle_nomes\.json|_ARQUIVOS_DO_CARD\.txt|code_curation\.json|"
    r"material_curation\.json|references_curation\.json|FILE_MAP.*\.md|COURSE_MAP\.md|GLOSSARY\.md|sections\.json|"
    r"labels\.json|site_links\.json|.*captur.*\.json|.*placar.*|.*avaliacao.*\.json)$", re.I)
PARTE_NEGADA = {"manual-review", ".frzero", "site", "__pycache__", "course", "build", "content", "staging"}
RAIZ_NEGADA = re.compile(r".+-Tutor|GPT-Tutor-Generator.*")   # por COMPONENTE do caminho (fullmatch), nunca substring
PERMITIDO_RAW = re.compile(r"(^|/)raw/moodle/(contents\.json|pages/[^/]+\.html?)$")
# ---------------------------------------------------------------- configurações e segredos (recusados, registrados)
NOME_SEGREDO = re.compile(
    r"^(\.env.*|.*\.env|.*\.(ini|cfg|conf|toml|ya?ml|pem|key|p12|pfx|crt|cer|kdbx|sqlite3?|db)|id_(rsa|dsa|ecdsa|ed25519).*|"
    r"\.netrc|\.git-credentials|\.npmrc|\.pypirc|\.gpt_tutor_config\.json|(config|settings|secrets?|credentials?)[\w.-]*\.json)$",
    re.I)   # só nomes de arquivo de configuração/credencial; palavra solta no nome ("Token Ring.pdf") não recusa
PARTE_SEGREDO = {".git", ".ssh", ".aws", ".config", "moddle", ".gnupg"}
PADRAO_SEGREDO = re.compile(
    r"(MOODLE_TOKEN|GEMINI_API_KEY|GOOGLE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|DATALAB_API_KEY|M365_[A-Z_]*|"
    r"[A-Z_]*(PASSWORD|SECRET|TOKEN|API_KEY))\s*[:=]|AIza[0-9A-Za-z_\-]{35}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"[?&](ws)?token=[^&\s\"']{8,}|sesskey=|MoodleSession|ghp_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{20,}|"
    r"\bsk-[0-9A-Za-z]{20,}|xox[baprs]-[0-9A-Za-z-]{10,}")
PARAM_AUTENTICACAO = re.compile(r"^(ws)?token$|^sesskey$|^key$|^sig(nature)?$|^access_token$|^auth", re.I)
# ---------------------------------------------------------------- saídas do motor (assinaturas, em qualquer texto)
PADRAO_PREDICAO = re.compile(
    r"computed_(block|unit|subunit)|temporal_block_id|unit_match|subunit_match|match_confidence|winner_score|"
    r"assignment_run|auto_tags|glossary_curation|propagado-headings|secao-nomeia-subtopico|\bbloco-\d{2}\b", re.I)
# ---------------------------------------------------------------- materiais: extensões permitidas e assinaturas
MAGIC = {"pdf": (b"%PDF",), "docx": (b"PK\x03\x04",), "pptx": (b"PK\x03\x04",), "xlsx": (b"PK\x03\x04",),
         "odt": (b"PK\x03\x04",), "odp": (b"PK\x03\x04",), "ods": (b"PK\x03\x04",), "zip": (b"PK\x03\x04",),
         "doc": (b"\xd0\xcf\x11\xe0",), "ppt": (b"\xd0\xcf\x11\xe0",), "xls": (b"\xd0\xcf\x11\xe0",),
         "png": (b"\x89PNG",), "jpg": (b"\xff\xd8\xff",), "jpeg": (b"\xff\xd8\xff",), "gif": (b"GIF87a", b"GIF89a")}
TEXTO = {"txt", "md", "csv", "html", "htm", "ipynb", "py", "java", "c", "h", "cpp", "js", "ts", "sql"}
MIDIA = {"mp4"}   # assinatura "ftyp" no byte 4
EXT_MATERIAL = set(MAGIC) | TEXTO | MIDIA
# ---------------------------------------------------------------- v3: política de contêineres (membros)
CONTEINER_DOCUMENTO = {"docx", "pptx", "xlsx", "odt", "odp", "ods"}
CONTEINER_ZIP = CONTEINER_DOCUMENTO | {"zip"}
TEXTO_MEMBRO = {"xml", "rels", "json", "svg", "vml"}
EXT_EXECUTAVEL = {"exe", "dll", "bat", "cmd", "ps1", "sh", "vbs", "jar", "msi", "scr", "com", "app", "apk", "so", "dylib",
                  "docm", "pptm", "xlsm", "dotm"}
DESCOMPACTADO_MAX, RAZAO_MAX, MEMBROS_MAX, PROFUNDIDADE_MAX = 500_000_000, 200, 5000, 2

SECAO_OK = ("section", "name", "summary")
MODULO_OK = ("id", "name", "modname", "description", "url", "contents")
CONTEUDO_OK = ("type", "filename", "filepath", "filesize")

CHAVES_OK = {
    "materiais.json": {"versao", "sigla", "materiais", "material_id", "tipo", "adjudicavel", "arquivo", "nome_original",
                       "ocorrencias", "secao", "modulo", "modname", "sha256", "tamanho", "url", "motivo"},
    "moodle_estrutura.json": {"versao", "sigla", "formato", "secoes", "numero", "nome", "resumo", "rotulos", "secao",
                              "texto", "modulos", "modname"},
    "rotulos.json": {"versao", "sigla", "origem", "unidades", "topicos", "id", "slug", "titulo", "unidade", "rotulo", "codigo"},
    "pacote_manifesto.json": {"versao", "sigla", "gerador_sha256", "instrucoes_sha256", "arquivos", "sha256", "origem",
                              "tipo", "fonte", "fonte_sha256", "funcao", "entradas", "fontes_lidas", "papel",
                              "fontes_nao_usadas", "motivo", "python", "ligacao"},
}
GERADOS = ("materiais.json", "moodle_estrutura.json", "rotulos.json", "gold_modelo.csv", "INSTRUCOES.md",
           "declaracao_cegamento.md")


class AcessoNegado(RuntimeError):
    pass


class AmbiguidadeOrigem(RuntimeError):
    pass


class DivergenciaProveniencia(RuntimeError):
    pass


class PlanoRecusado(RuntimeError):
    pass


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


class Leitor:
    """Única porta de leitura. Registra cada arquivo lido (caminho absoluto + sha256)."""

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
        partes = Path(rel).parts
        if set(partes[:-1]) & PARTE_SEGREDO or NOME_SEGREDO.match(p.name):
            raise AcessoNegado(f"configuração ou credencial: {rel}")
        if "raw" in partes:
            if not PERMITIDO_RAW.search(rel):
                raise AcessoNegado(f"arquivo bruto não permitido: {rel}")
        elif set(partes[:-1]) & PARTE_NEGADA or NOME_NEGADO.match(p.name):
            raise AcessoNegado(f"gerado pelo produto ou saída do motor: {rel}")
        return raiz, rel

    def le(self, p):
        self.confere(p)
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


def url_sem_autenticacao(url):
    """Remove parâmetros de autenticação da query; o resto da URL fica como está."""
    partes = urllib.parse.urlsplit(str(url or ""))
    q = [(k, v) for k, v in urllib.parse.parse_qsl(partes.query, keep_blank_values=True) if not PARAM_AUTENTICACAO.match(k)]
    return urllib.parse.urlunsplit(partes._replace(query=urllib.parse.urlencode(q)))


def chave_secao(nome):
    """Forma comparável de nome de seção x nome de pasta (acentos, caixa, pontuação e espaços ignorados)."""
    t = unicodedata.normalize("NFKD", html.unescape(str(nome or ""))).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", t.casefold())


def pasta_da_secao(rel):
    partes = Path(rel).parts
    if partes and partes[0] == "stash":
        partes = partes[1:]
    return partes[0] if len(partes) > 1 else ""


def _varre_texto(texto):
    if PADRAO_PREDICAO.search(texto):
        return "texto com assinatura de saída do motor"
    if PADRAO_SEGREDO.search(texto):
        return "texto com credencial ou segredo"
    return None


def _decodifica(dados):
    try:
        return dados.decode("utf-8")
    except UnicodeDecodeError:
        return dados.decode("latin-1")


def verifica_pdf(dados):
    """Membro embutido em PDF (anexo) = recusa. Busca por bytes: objeto em stream comprimido não é visto (limitação)."""
    return "PDF com arquivo embutido" if b"/EmbeddedFile" in dados else None


def verifica_conteiner(nome, dados, profundidade=0):
    """Política explícita de membros para ZIP, OOXML e ODF. None = aceito; senão o motivo da recusa.

    ZIP simples: cada membro passa por `verifica_material` (mesma allowlist, assinatura e varredura do arquivo solto).
    Documento (docx/pptx/xlsx/odt/odp/ods): XML e texto varridos sem as tags; PDF, imagem e contêiner aninhados passam
    por `verifica_material`; objeto OLE (.bin), macro e executável recusados. Em ambos: caminho inseguro, membro
    cifrado, nome de configuração/credencial, excesso de membros, tamanho ou aninhamento = recusa."""
    ext = Path(nome).suffix.lower().lstrip(".")
    if profundidade >= PROFUNDIDADE_MAX:
        return f"contêiner aninhado além da profundidade {PROFUNDIDADE_MAX}"
    try:
        z = zipfile.ZipFile(io.BytesIO(dados))
        infos = z.infolist()
    except (zipfile.BadZipFile, ValueError, OSError):
        return f"contêiner .{ext} ilegível"
    if len(infos) > MEMBROS_MAX:
        return f"contêiner com mais de {MEMBROS_MAX} membros"
    total = sum(i.file_size for i in infos)
    if total > DESCOMPACTADO_MAX or total > RAZAO_MAX * max(len(dados), 1):
        return "contêiner com tamanho descompactado acima do limite (possível bomba)"
    for i in infos:
        n = i.filename
        partes = [x for x in re.split(r"[\\/]", n) if x]
        if n.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", n) or ".." in partes:
            return f"membro com caminho inseguro: {n[:60]}"
        if i.flag_bits & 0x1:
            return f"membro cifrado: {n[:60]}"
        if i.is_dir():
            continue
        base = partes[-1] if partes else n
        mext = Path(base).suffix.lower().lstrip(".")
        if NOME_SEGREDO.match(base) or set(partes[:-1]) & PARTE_SEGREDO:
            return f"membro de configuração ou credencial: {base[:60]}"
        if mext in EXT_EXECUTAVEL or base.lower() == "vbaproject.bin":
            return f"membro executável ou macro: {base[:60]}"
        if ext in CONTEINER_DOCUMENTO and mext == "bin" and not re.fullmatch(r"printerSettings\d*\.bin", base):
            return f"objeto embutido não examinável: {base[:60]}"
        try:
            conteudo = z.read(i)
        except (zipfile.BadZipFile, RuntimeError, ValueError, OSError, NotImplementedError) as exc:
            return f"membro ilegível: {base[:40]} ({type(exc).__name__})"
        if ext not in CONTEINER_DOCUMENTO or mext in EXT_MATERIAL:
            motivo = verifica_material(base, conteudo, profundidade + 1)
        elif mext in TEXTO_MEMBRO:
            motivo = _varre_texto(re.sub(r"<[^>]+>", "", _decodifica(conteudo)))   # texto de documento vem em runs
        else:
            motivo = None   # fonte, EMF/WMF, mimetype: estrutura do documento, sem texto examinável
        if motivo:
            return f"membro {n[:60]}: {motivo}"
    return None


def verifica_material(nome, dados, profundidade=0):
    """None = aceito; senão, o motivo da recusa (extensão, assinatura, membros de contêiner, saída do motor, segredo)."""
    ext = Path(nome).suffix.lower().lstrip(".")
    if ext not in EXT_MATERIAL:
        return f"extensão fora da allowlist: .{ext or '(nenhuma)'}"
    if ext in MAGIC and not any(dados.startswith(m) for m in MAGIC[ext]):
        return f"assinatura não corresponde a .{ext} (arquivo renomeado?)"
    if ext in MIDIA and dados[4:8] != b"ftyp":
        return f"assinatura não corresponde a .{ext}"
    if ext in CONTEINER_ZIP:
        return verifica_conteiner(nome, dados, profundidade)
    if ext == "pdf":
        return verifica_pdf(dados)
    if ext in TEXTO:
        return _varre_texto(_decodifica(dados))
    return None


def arquivos_locais(leitor, moodle_dir):
    """Todos os arquivos da fonte: os que o leitor aceita (candidatos) e os demais com o motivo (nunca descartados)."""
    locais, nao_usados = [], {}
    for p in sorted(Path(moodle_dir).rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(moodle_dir).as_posix()
        try:
            leitor.confere(p)
        except AcessoNegado as exc:
            nao_usados[rel] = "negado pelo leitor: " + str(exc).split(":", 1)[0]
            continue
        if rel == "raw/moodle/contents.json":
            continue
        locais.append({"caminho": p, "rel": rel, "nome": p.name, "tamanho": p.stat().st_size})
    return locais, nao_usados


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


def carrega_inventario(fonte):
    """Inventário da aquisição do curso: {(modulo_id, arquivo): [registros]} e o sha256 do arquivo; (None, None) sem ele.

    Lido fora do Leitor (documento do protocolo, como as instruções): nunca é copiado para o pacote."""
    if not fonte.get("inventario"):
        return None, None
    dados = Path(fonte["inventario"]).read_bytes()
    inv = json.loads(dados.decode("utf-8"))
    cursos = [c for c in inv.get("cursos") or [] if str(c.get("id")) == str(fonte.get("curso_id"))]
    if inv.get("esquema") not in ("inventario-downloads-1", "inventario-downloads-2") or len(cursos) != 1:
        raise DivergenciaProveniencia(f"inventário sem esquema conhecido ou sem o curso {fonte.get('curso_id')!r}")
    if inv.get("concluido") is False:
        raise DivergenciaProveniencia("inventário parcial (aquisição interrompida)")
    idx = {}
    for r in cursos[0]["arquivos"]:
        idx.setdefault((str(r["modulo_id"]), str(r["arquivo"])), []).append(r)
    return idx, sha_b(dados)


def liga_por_inventario(inv, mod_id, c, por_rel):
    """(arquivo local, None) pela proveniência da aquisição, conferindo caminho e sha256; (None, status) se não adquirido."""
    regs = inv.get((str(mod_id), str(c["filename"])), [])
    if c.get("filepath") and any("filepath" in r for r in regs):
        regs = [r for r in regs if r.get("filepath") == c["filepath"]]
    if len(regs) != 1:
        raise DivergenciaProveniencia(f"módulo {mod_id}, {c['filename']!r}: {len(regs)} registros no inventário")
    r = regs[0]
    if r["status"] != "ok":
        return None, r["status"]
    a = por_rel.get(r.get("caminho")) if r.get("base", "curso") == "curso" else None
    if a is None or a["sha"] != r.get("sha256"):
        raise DivergenciaProveniencia(f"{r.get('caminho')}: ausente na fonte ou sha256 diferente do inventário")
    return a, None


def resolve_origem(c, secao, por_nome):
    """Sem inventário: nome + tamanho, confirmados pela pasta da seção do módulo. Retorna (arquivo, ligação).

    Candidato só em pasta de OUTRA seção nunca é ligado: (None, "origem_nao_confirmada"). Arquivo fora de pasta de
    seção (leiaute sem seções) só vale se não houver candidato em outra seção."""
    cand = por_nome.get((c["filename"], c["filesize"]), [])
    if not cand:
        return None, None
    na_secao = [a for a in cand if chave_secao(pasta_da_secao(a["rel"])) == chave_secao(secao)]
    fora = [a for a in cand if a not in na_secao and pasta_da_secao(a["rel"])]
    alvo, ligacao = (na_secao, "nome_tamanho_secao") if na_secao else ([], None) if fora else (cand, "nome_tamanho_sem_secao")
    if not alvo:
        return None, "origem_nao_confirmada"
    if len({a["sha"] for a in alvo}) > 1:
        raise AmbiguidadeOrigem(f"{c['filename']} ({c['filesize']} bytes) na seção {secao!r}: candidatos "
                                f"{sorted(a['rel'] for a in alvo)}")
    return sorted(alvo, key=lambda a: a["rel"])[0], ligacao


def descobre(leitor, fonte):
    """Materiais, estrutura do Moodle, arquivos não usados (com motivo) e sha256 do inventário, só de fontes permitidas.

    Com inventário da aquisição, recurso -> arquivo sai da proveniência (módulo, arquivo, caminho, sha256); sem ele,
    de nome + tamanho confirmados pela seção. Item não adquirido ou sem origem confirmada fica visível e não adjudicável."""
    moodle = Path(fonte["moodle_dir"])
    locais, nao_usados = arquivos_locais(leitor, moodle)
    for a in locais:
        a["sha"] = sha_b(leitor.le(a["caminho"]))
    por_nome, por_rel = {}, {a["rel"]: a for a in locais}
    for a in locais:
        por_nome.setdefault((a["nome"], a["tamanho"]), []).append(a)
    inv, inv_sha = carrega_inventario(fonte)
    materiais, estrutura = {}, {"formato": None, "secoes": [], "rotulos": [], "modulos": []}
    usados = set()

    def acrescenta(chave, reg, ocorr, ligacao=None):
        m = materiais.setdefault(chave, {**reg, "ocorrencias": [], "ligacoes": set()})
        if ocorr not in m["ocorrencias"]:
            m["ocorrencias"].append(ocorr)
        if ligacao:
            m["ligacoes"].add(ligacao)

    def sem_arquivo(tipo, chave, c, ocorr, motivo=None):
        reg = {"tipo": tipo, "adjudicavel": False, "arquivo": None, "nome_original": c["filename"], "sha256": None,
               "tamanho": c["filesize"], "url": None}
        acrescenta(chave, {**reg, "motivo": motivo} if motivo else reg, ocorr)

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
                arquivos_mod = [c for c in ({k: x.get(k) for k in CONTEUDO_OK} for x in mod["contents"] or [])
                                if c["type"] == "file"]
                if modname == "label":
                    estrutura["rotulos"].append({"secao": nome_sec, "texto": texto_html(mod["description"])})
                elif modname == "url":
                    url = url_sem_autenticacao(mod["url"])
                    acrescenta("url:" + url, {"tipo": "link_externo", "adjudicavel": False, "arquivo": None,
                                              "nome_original": nome_mod, "sha256": None, "tamanho": None, "url": url}, ocorr)
                elif modname == "page":
                    htmls = [c for c in arquivos_mod if str(c["filename"]).lower().endswith((".html", ".htm"))]
                    if inv is None:
                        paginas = sorted((x for x in locais if x["rel"].startswith(f"raw/moodle/pages/{mod['id']}-")),
                                         key=lambda x: x["rel"])
                    else:
                        paginas = []
                        for c in htmls:
                            a, status = liga_por_inventario(inv, mod["id"], c, por_rel)
                            if a is None:
                                sem_arquivo("arquivo_nao_adquirido", f"naoadquirido:{mod['id']}/{c['filename']}", c, ocorr,
                                            "aquisição: " + status)
                            else:
                                paginas.append(a)
                    if len(paginas) > 1:
                        raise AmbiguidadeOrigem(f"página {mod['id']}: {[x['rel'] for x in paginas]}")
                    for a in paginas:
                        usados.add(a["rel"])
                        acrescenta("arq:" + a["sha"], {"tipo": "pagina", "fonte": a, "nome_original": a["nome"]}, ocorr,
                                   "pagina_do_modulo" if inv is None else "inventario_aquisicao")
                    for c in arquivos_mod:   # anexo de página: registrado, não entregue (fora da fonte do pacote)
                        if c not in htmls:
                            sem_arquivo("anexo_de_pagina", f"anexo:{mod['id']}/{c['filename']}", c, ocorr,
                                        "anexo de página não entregue ao adjudicador")
                elif modname in ("resource", "folder", "assign"):
                    for c in arquivos_mod:
                        if inv is not None:
                            a, status = liga_por_inventario(inv, mod["id"], c, por_rel)
                            if a is None:
                                sem_arquivo("arquivo_nao_adquirido", f"naoadquirido:{mod['id']}/{c['filename']}", c, ocorr,
                                            "aquisição: " + status)
                                continue
                            ligacao = "inventario_aquisicao"
                        else:
                            a, ligacao = resolve_origem(c, nome_sec, por_nome)
                            if ligacao == "origem_nao_confirmada":
                                sem_arquivo("origem_nao_confirmada", f"naoconfirmada:{mod['id']}/{c['filename']}", c, ocorr,
                                            "arquivo de mesmo nome e tamanho só na pasta de outra seção; não ligado")
                                continue
                            if a is None:
                                sem_arquivo("arquivo_sem_fonte_local", "semfonte:" + str(c["filename"]), c, ocorr)
                                continue
                        usados.add(a["rel"])
                        acrescenta("arq:" + a["sha"], {"tipo": "arquivo", "fonte": a, "nome_original": c["filename"]}, ocorr,
                                   ligacao)
        for a in locais:   # mesmo nome e bytes de um arquivo usado: cópia redundante, registrada
            if a["rel"] not in usados and ("arq:" + a["sha"]) in materiais:
                nao_usados[a["rel"]] = "cópia idêntica de material já incluído"
                usados.add(a["rel"])
        sobras = [a for a in locais if a["rel"] not in usados]
    else:
        estrutura["formato"] = "pastas"
        sobras = locais
    for a in sobras:   # arquivos locais sem módulo correspondente: seção = pasta de seção (sob stash/, se houver)
        secao = pasta_da_secao(a["rel"])
        if estrutura["formato"] == "pastas" and secao and secao not in [s["nome"] for s in estrutura["secoes"]]:
            estrutura["secoes"].append({"numero": None, "nome": secao, "resumo": ""})
        acrescenta("arq:" + a["sha"], {"tipo": "arquivo", "fonte": a, "nome_original": a["nome"]},
                   {"secao": secao, "modulo": "", "modname": ""}, "sem_modulo")
    escolhidos = {m["fonte"]["rel"] for m in materiais.values() if "fonte" in m}
    for a in locais:   # cópia com os mesmos bytes de um material já incluído: registrada, nunca some
        if a["rel"] not in escolhidos and a["rel"] not in nao_usados:
            nao_usados[a["rel"]] = "cópia idêntica de material já incluído"
    return materiais, estrutura, nao_usados, inv_sha


def json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")


def monta(fonte, destino):
    """Gera o pacote em `destino` (não pode existir). Determinístico: mesma fonte = mesmos bytes."""
    destino = Path(destino)
    if destino.exists():
        raise FileExistsError(f"destino já existe: {destino}")
    moodle = Path(fonte["moodle_dir"])
    plano_arq, plano_txt = Path(fonte["plano_arquivo"]), Path(fonte["plano_texto"])
    leitor = Leitor([moodle, plano_arq, plano_txt])   # instruções = documento do protocolo, lido à parte
    materiais, estrutura, nao_usados, inv_sha = descobre(leitor, fonte)
    for p in (plano_arq, plano_txt):   # o plano é entregue e gera os rótulos: mesma política de cegamento dos materiais
        motivo = verifica_material(p.name, leitor.le(p))
        if motivo:
            raise PlanoRecusado(f"{p.name}: {motivo}; pacote não gerado")
    unidades, topicos = rotulos_do_plano(leitor.le(plano_txt).decode("utf-8"))
    arquivos, lista, fontes_lidas = {}, [], {}
    if inv_sha:
        fontes_lidas["aquisicao:" + Path(fonte["inventario"]).name] = {"sha256": inv_sha, "papel": "inventario_aquisicao"}
    destino.mkdir(parents=True)

    def grava(rel, dados, origem):
        p = destino / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(dados)
        arquivos[rel] = {"sha256": sha_b(dados), "origem": origem}

    for chave in sorted(materiais, key=lambda k: id_material(k)):
        m = materiais[chave]
        mid = id_material(chave)
        reg = {"material_id": mid, "tipo": m["tipo"], "nome_original": m["nome_original"],
               "ocorrencias": sorted(m["ocorrencias"], key=lambda o: (o["secao"], o["modulo"], o["modname"]))}
        if "fonte" in m:
            dados = leitor.le(m["fonte"]["caminho"])
            motivo = verifica_material(m["nome_original"] if m["tipo"] != "pagina" else m["fonte"]["nome"], dados)
            fontes_lidas["moodle:" + m["fonte"]["rel"]] = {"sha256": sha_b(dados), "papel": m["tipo"] if not motivo else "recusado",
                                                          "ligacao": sorted(m["ligacoes"])}
            if motivo:   # recusado: não é copiado, fica visível e não adjudicável
                reg.update(tipo="recusado", adjudicavel=False, arquivo=None, sha256=sha_b(dados), tamanho=len(dados), url=None,
                           motivo=motivo)
            else:
                rel = f"materiais/{mid}__{nome_seguro(m['nome_original'])}"
                grava(rel, dados, {"tipo": "bruto", "fonte": "moodle:" + m["fonte"]["rel"], "fonte_sha256": sha_b(dados)})
                reg.update(adjudicavel=True, arquivo=rel, sha256=sha_b(dados), tamanho=len(dados), url=None)
        else:
            reg.update(adjudicavel=m["adjudicavel"], arquivo=None, sha256=m["sha256"], tamanho=m["tamanho"], url=m["url"])
            if m.get("motivo"):
                reg["motivo"] = m["motivo"]
        lista.append(reg)
    cj = moodle / "raw/moodle/contents.json"
    if cj.is_file():
        fontes_lidas["moodle:raw/moodle/contents.json"] = {"sha256": sha_b(cj.read_bytes()), "papel": "estrutura_moodle"}
    for p, nome, papel in ((plano_arq, "plano/" + nome_seguro(plano_arq.name), "plano"),
                           (plano_txt, "plano/plano_texto" + plano_txt.suffix, "plano_texto")):
        dados = leitor.le(p)
        grava(nome, dados, {"tipo": "bruto", "fonte": "plano:" + p.name, "fonte_sha256": sha_b(dados)})
        fontes_lidas["plano:" + p.name] = {"sha256": sha_b(dados), "papel": papel}
    base = {"versao": VERSAO, "sigla": fonte["sigla"]}

    def ent(*chaves):
        return [{"fonte": k, "sha256": fontes_lidas[k]["sha256"]} for k in sorted(chaves)]

    moodle_ents = [k for k in fontes_lidas if k.startswith(("moodle:", "aquisicao:"))]
    grava("materiais.json", json_bytes({**base, "materiais": lista}),
          {"tipo": "derivado", "funcao": "descobre", "entradas": ent(*moodle_ents)})
    grava("moodle_estrutura.json", json_bytes({**base, **estrutura}),
          {"tipo": "derivado", "funcao": "descobre", "entradas": ent(*[k for k in moodle_ents if k.endswith("contents.json")])})
    grava("rotulos.json", json_bytes({**base, "origem": "content_taxonomy.build_content_taxonomy(texto do plano, '', '', None)",
                                      "unidades": unidades, "topicos": topicos}),
          {"tipo": "derivado", "funcao": "rotulos_do_plano", "entradas": ent("plano:" + plano_txt.name)})
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CAMPOS_GOLD)
    for reg in lista:
        if reg["adjudicavel"]:
            w.writerow([reg["material_id"], "", "", "", "", ""])
    grava("gold_modelo.csv", buf.getvalue().encode("utf-8"),
          {"tipo": "derivado", "funcao": "monta", "entradas": [{"fonte": "materiais.json", "sha256": arquivos["materiais.json"]["sha256"]}]})
    instr = INSTRUCOES.read_bytes()
    grava("INSTRUCOES.md", instr, {"tipo": "bruto", "fonte": "protocolo:" + INSTRUCOES.name, "fonte_sha256": sha_b(instr)})
    decl = instr.decode("utf-8").split("```text", 1)[1].split("```", 1)[0].strip() + "\n"
    grava("declaracao_cegamento.md", decl.encode("utf-8"),
          {"tipo": "derivado", "funcao": "monta", "entradas": [{"fonte": "protocolo:" + INSTRUCOES.name, "sha256": sha_b(instr)}]})
    manifesto = {**base, "gerador_sha256": sha_b(Path(__file__).read_bytes()), "instrucoes_sha256": sha_b(instr),
                 "python": sys.version.split()[0], "arquivos": arquivos, "fontes_lidas": fontes_lidas,
                 "fontes_nao_usadas": [{"fonte": "moodle:" + k, "motivo": v} for k, v in sorted(nao_usados.items())]}
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
    """Auditoria negativa + allowlist positiva + procedência completa + regeneração. Lista vazia = aprovado."""
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
        if rel.startswith(("materiais/", "plano/")) and p.is_file():
            motivo = verifica_material(rel.split("__", 1)[-1], p.read_bytes())
            if motivo:
                prob.append(f"{rel}: {motivo}")
    for nome, ok in CHAVES_OK.items():
        obj = json.loads((pacote / nome).read_text(encoding="utf-8"))
        if nome == "pacote_manifesto.json":   # as chaves de "arquivos" e "fontes_lidas" são caminhos, não campos
            obj = {**obj, "arquivos": list(obj.get("arquivos", {}).values()),
                   "fontes_lidas": list(obj.get("fontes_lidas", {}).values())}
        extras = _chaves(obj, set()) - ok
        if extras:
            prob.append(f"{nome}: chaves fora da allowlist {sorted(extras)}")
    for nome in GERADOS + ("pacote_manifesto.json",):
        if nome == "INSTRUCOES.md":
            continue
        texto = (pacote / nome).read_text(encoding="utf-8")
        for padrao, o_que in ((PADRAO_PREDICAO, "predição/saída do motor"), (PADRAO_SEGREDO, "credencial ou segredo")):
            achado = padrao.search(texto)
            if achado:
                prob.append(f"{nome}: padrão de {o_que}: {achado.group(0)[:20]!r}")
    rot = json.loads((pacote / "rotulos.json").read_text(encoding="utf-8"))
    ids_u = {u["id"] for u in rot["unidades"]}
    if any(t["unidade"] not in ids_u for t in rot["topicos"]):
        prob.append("rotulos.json: tópico de unidade inexistente")
    # procedência completa: todo arquivo da fonte Moodle foi lido OU está nos não usados com motivo
    moodle = Path(fonte["moodle_dir"])
    todos = {"moodle:" + p.relative_to(moodle).as_posix() for p in moodle.rglob("*") if p.is_file()}
    declarados = {k for k in man.get("fontes_lidas", {}) if k.startswith("moodle:")} | \
        {x["fonte"] for x in man.get("fontes_nao_usadas", [])}
    if todos != declarados:
        prob.append(f"procedência incompleta: sem registro {sorted(todos - declarados)[:5]}, registro sem arquivo "
                    f"{sorted(declarados - todos)[:5]}")
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
