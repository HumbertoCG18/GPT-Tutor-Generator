"""Regime VOCAB — recompilação limpa (VOCAB_LIMPO), 26/09. Pré-registro: docs/reports/2026-09-26-regime-vocab-recompilacao-limpa.md.

Subcomandos (sempre no ambiente controlado, via roda_controlado.py; nunca lê régua/gold — travas instaladas):
  --staging    área isolada por curso a partir dos insumos congelados da Fase 1 + unidades do CRU (sem rede)
  --ensaio     executa o compilador ATUAL com cliente falso (sem rede) em cópias do staging, 2x: inventário exato das
               chamadas (bundle de cada unidade) e prova de determinismo
  --congelar   congelamento da recompilação (código, SDK, modelo, config da chamada, staging, inventário, protocolo)
  --compilar   ÚNICA geração oficial (rede só para o host do Gemini); grava request/response brutos por chamada
  --sanidade   verificações sem gold do sidecar gerado + comparação descritiva com o VOCAB_LLM histórico

O compilador é chamado como o produto o chama (`pedagogical_regeneration._run_vocabulary_compile_layer`):
`compile_course_vocabulary(root, entries, load_internal_content_taxonomy(root), client)`, sem mudar uma linha de src/.
A instrumentação do cliente é transparente: envolve `generate_content` do SDK, confere a request contra o inventário
congelado ANTES de enviar e grava request/response; a lógica de retry/parsing continua a do `GeminiClient`.
"""
import collections
import copy
import datetime
import json
import os
import platform
import shutil
import socket
import sys
import time
from importlib import metadata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DATA = AQUI.parents[4]
W5 = AQUI.parent / "wad5_25-09"
sys.path.insert(0, str(W5))      # comum.py congelado da Fase 1 (só leitura; hash aprovado 04a535b6…)
sys.path.insert(1, str(DATA))    # src/ (import tardio, depois das travas)
import comum as K  # noqa: E402

BASE = DATA / ".frzero/vocab_limpo_26-09"
STAGING, ENSAIO, CHAMADAS = BASE / "staging", BASE / "ensaio", BASE / "chamadas"
CONG5 = DATA / ".frzero/wad5_25-09/congelamento.json"
ENTR5 = DATA / ".frzero/wad5_25-09/congelamento_entradas.json"
MANCAP5 = W5 / "manifesto_capturas_v5.json"
PROTOCOLO = DATA / "docs/reports/2026-09-26-regime-vocab-recompilacao-limpa.md"
CONG_LIMPO = BASE / "congelamento_recompilacao.json"
INVENTARIO = BASE / "inventario_chamadas.json"
STAGING_MAN = BASE / "staging_manifesto.json"
CONFIG_USUARIO = Path.home() / ".gpt_tutor_config.json"
HOSTS_PERMITIDOS = frozenset({"generativelanguage.googleapis.com"})
MD_CHAVES = ("approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown")
LLM_VOCAB, MANUAL_VOCAB = ".glossary_curation.llm.json", ".glossary_curation.json"
ID5 = "3fe5d1ff97258644b3148860cbe235aa3e16acfac91e9a291ea3c3e63a8e355d"
CODIGO_SCRIPTS = {"limpo.py": AQUI / "limpo.py", "roda_controlado.py": AQUI / "roda_controlado.py", "comum.py (W5)": W5 / "comum.py"}


def exige(cond, msg):
    if not cond:
        raise K.ErroIntegridade(msg)


def rel(p):
    return Path(p).resolve().relative_to(DATA).as_posix()


def agora():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")


def travas_base(papel):
    """Travas do processo: código só leitura; gold proibido; .env e a config do usuário negados (a chave é lida ANTES
    de instalar, só em --compilar); tutores vivos proibidos."""
    t = K.Travas(papel)
    raizes = [DATA / "src", AQUI, W5, Path(sys.base_prefix), Path(sys.prefix)]
    import site
    raizes += [Path(p) for p in site.getsitepackages()]
    t.permite("codigo", *raizes, somente_leitura=True)
    t.nega(DATA / ".env", "arquivo .env da raiz (segredos e configuração)")
    t.nega(CONFIG_USUARIO, "config do usuário (contém a chave da API)")
    for nome in K.NOMES.values():
        t.proibe(DATA.parent / nome, "tutor vivo")
    t.proibe(AQUI.parent / "wad5_avaliacao_26-09", "resultados da avaliação da Fase 1 (por ID)")
    t.proibe(DATA / ".frzero/wad5_avaliacao_26-09", "espelho da régua da Fase 1")
    t.proibe(DATA / "docs/reports/pendencias.md", "tracker (contém IDs das perdas da Fase 1)")
    return t


def carrega_fase1():
    """Congelamento W-AD5, entradas e captura CRU, conferidos contra os hashes aprovados."""
    cong = K.carrega_json_estrito(CONG5)
    exige(cong["id_comum"] == ID5 and not K.valida_congelamento(cong), "congelamento da Fase 1 divergente")
    entradas = K.carrega_json_estrito(ENTR5)
    exige(K.sha_json(entradas) == cong["normativo"]["entradas_arquivo_sha"], "entradas da Fase 1 divergentes")
    man = K.carrega_json_estrito(MANCAP5)
    c = man["capturas"]["CRU"]
    exige(K.sha_arq(DATA / c["arquivo"]) == c["sha256"], "captura CRU da Fase 1 divergente do manifesto")
    cru = K.carrega_json_estrito(DATA / c["arquivo"])
    exige(not K.valida_historica(cru, cong, braco="CRU"), "captura CRU da Fase 1 não valida")
    return cong, entradas, cru, c


# ------------------------------------------------------------------------------------------- staging
def staging():
    t = travas_base("staging")
    cong0 = K.carrega_json_estrito(CONG5)
    raizes = {s: DATA / e["raiz"] for s, e in cong0["normativo"]["entradas_comuns"].items()}
    t.permite("comum", *raizes.values(), somente_leitura=True)
    t.permite("referencia", CONG5, ENTR5, MANCAP5, DATA / ".frzero/wad5_25-09/capturas", somente_leitura=True)
    t.permite("saida", BASE)
    t.instala()
    exige(not STAGING.exists(), "staging já existe: não sobrescrevo")
    cong, entradas, cru, c = carrega_fase1()
    for s, root in raizes.items():
        t.congela(root, entradas[s])
    registro = {"fonte": {"congelamento_fase1": ID5, "captura_cru": {"arquivo": c["arquivo"], "sha256": c["sha256"]}},
                "cursos": {}}
    for s, nome in K.NOMES.items():
        root, dest = raizes[s], STAGING / nome
        man = K.carrega_json_estrito(root / "manifest.json")
        tax_bytes = (root / "course/.content_taxonomy.json").read_bytes()
        exige(K.sha_bytes(tax_bytes) == entradas[s]["course/.content_taxonomy.json"], f"{s}: taxonomia != congelada")
        exige(K.sha_json(json.loads(tax_bytes.decode("utf-8"))) == cong["insumos"]["CRU"][s]["taxonomia_sha"],
              f"{s}: taxonomia != snapshot CRU")
        dec = cru["decisoes"][s]
        entries = man["entries"]
        exige(sorted(str(e["id"]) for e in entries) == sorted(dec), f"{s}: entries != inventário do CRU")
        novas, mudou = [], 0
        for e in entries:
            e2 = copy.deepcopy(e)
            u = dec[str(e["id"])]["final"]["unidade"]
            mudou += str(e2.get("computed_unit_slug") or "") != u
            e2["computed_unit_slug"] = u
            novas.append(e2)
        copiados = {}
        for e in entries:
            for k in MD_CHAVES:
                r = e.get(k)
                if r and str(r).lower().endswith(".md") and (root / r).is_file():
                    rp = Path(r).as_posix()
                    exige(rp in entradas[s], f"{s}: markdown fora do congelamento: {rp}")
                    if rp not in copiados:
                        b = (root / rp).read_bytes()
                        exige(K.sha_bytes(b) == entradas[s][rp], f"{s}: markdown divergente: {rp}")
                        (dest / rp).parent.mkdir(parents=True, exist_ok=True)
                        (dest / rp).write_bytes(b)
                        copiados[rp] = entradas[s][rp]
        (dest / "course").mkdir(parents=True, exist_ok=True)
        (dest / "course/.content_taxonomy.json").write_bytes(tax_bytes)
        K.grava_atomico(dest / "manifest_staging.json", {"entries": novas})
        registro["cursos"][s] = {"staging": rel(dest), "entries": len(novas), "unidade_substituida_pelo_cru": mudou,
                                 "markdown_copiados": len(copiados), "taxonomia_sha256": K.sha_bytes(tax_bytes),
                                 "arvore": K.arvore(dest)}
        print(f"  {s}: {len(novas)} entries, unidade trocada pela do CRU em {mudou}, {len(copiados)} markdown", flush=True)
    registro["arvore_sha"] = K.sha_json({s: v["arvore"] for s, v in registro["cursos"].items()})
    K.grava_atomico(STAGING_MAN, registro)
    t.rehash_leituras()
    print("STAGING OK", registro["arvore_sha"], flush=True)
    K.encerra(t, ok=True, codigo_falha=1)


# ------------------------------------------------------------------------------------------- ensaio (cliente falso)
class ClienteFalso:
    model = "ensaio-sem-rede"

    def __init__(self):
        self.chamadas = []

    def summarize_bundle(self, bundle_text, schema, system_instruction, max_retries=5):
        self.chamadas.append({"bundle": bundle_text, "system": system_instruction,
                              "schema": json.dumps(schema.model_json_schema(), sort_keys=True, ensure_ascii=False)})
        return schema()


def unidades_esperadas(entries, taxonomy):
    """Rótulo das chamadas: mesma seleção de compile_course_vocabulary (unidade com tópico rotulado e material)."""
    from src.builder.core import vocabulary_compile as VC
    from src.builder.routing.resolver_apply import _is_material
    com = {str(e.get("computed_unit_slug") or "").strip() for e in entries
           if _is_material(e) and str(e.get("category") or "").strip().lower() not in VC.OUT_CATS}
    return [(str(u.get("slug") or ""), str(u.get("title") or "")) for u in taxonomy.get("units") or []
            if [x for x in (u.get("topics") or []) if x.get("label")] and str(u.get("slug") or "") in com]


def ensaio():
    t = travas_base("ensaio")
    t.permite("referencia", STAGING, STAGING_MAN, somente_leitura=True)
    t.permite("saida", BASE)   # grava_atomico usa temporário na pasta-mãe; staging segue só leitura (raiz mais longa)
    t.instala()
    exige(not ENSAIO.exists(), "ensaio já existe: não sobrescrevo")
    reg = K.carrega_json_estrito(STAGING_MAN)
    for s, v in reg["cursos"].items():
        exige(K.arvore(DATA / v["staging"]) == v["arvore"], f"{s}: staging divergente do registrado")
    from src.builder.core import vocabulary_compile as VC
    from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
    inv = {"system_sha256": K.sha_bytes(VC.SYSTEM.encode("utf-8")), "system": VC.SYSTEM,
           "schema_sha256": K.sha_bytes(json.dumps(VC.Vocab.model_json_schema(), sort_keys=True, ensure_ascii=False).encode("utf-8")),
           "cursos": {}}
    rodadas = []
    for n in (1, 2):   # duas vezes: prova de determinismo das requests
        out = {}
        for s, nome in K.NOMES.items():
            src = DATA / reg["cursos"][s]["staging"]
            dst = ENSAIO / f"rodada{n}" / nome
            shutil.copytree(src, dst)
            entries = K.carrega_json_estrito(dst / "manifest_staging.json")["entries"]
            tax = load_internal_content_taxonomy(dst)
            falso = ClienteFalso()
            VC.compile_course_vocabulary(dst, entries, tax, falso)
            esperadas = unidades_esperadas(entries, tax)
            exige(len(esperadas) == len(falso.chamadas), f"{s}: {len(falso.chamadas)} chamadas != {len(esperadas)} unidades esperadas")
            out[s] = [{"indice": i, "unidade": u, "titulo": ti, "bundle_sha256": K.sha_bytes(c["bundle"].encode("utf-8")),
                       "chars": len(c["bundle"]), "system_sha256": K.sha_bytes(c["system"].encode("utf-8")),
                       "schema_sha256": K.sha_bytes(c["schema"].encode("utf-8")), "_bundle": c["bundle"]}
                      for i, ((u, ti), c) in enumerate(zip(esperadas, falso.chamadas, strict=True))]
        rodadas.append(out)
    exige(K.sha_json(rodadas[0]) == K.sha_json(rodadas[1]), "requests não determinísticas entre as duas rodadas do ensaio")
    for s, lst in rodadas[0].items():
        for c in lst:
            exige(c["system_sha256"] == inv["system_sha256"] and c["schema_sha256"] == inv["schema_sha256"], "system/schema variando")
            p = ENSAIO / "bundles" / f"{s}_{c['indice']:02d}.txt"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(c.pop("_bundle").encode("utf-8"))
            c["arquivo"] = rel(p)
        inv["cursos"][s] = lst
        print(f"  {s}: {len(lst)} chamadas previstas", flush=True)
    inv["total_chamadas"] = sum(len(v) for v in inv["cursos"].values())
    K.grava_atomico(INVENTARIO, inv)
    t.rehash_leituras()
    print("ENSAIO OK:", inv["total_chamadas"], "chamadas; requests idênticas nas 2 rodadas", flush=True)
    K.encerra(t, ok=True, codigo_falha=1)


# ------------------------------------------------------------------------------------------- congelamento
ARQUIVOS_CHAVE = ("src/builder/core/vocabulary_compile.py", "src/builder/runtime/gemini_client.py",
                  "src/builder/artifacts/navigation.py", "src/builder/extraction/content_taxonomy.py",
                  "src/builder/routing/resolver_apply.py", "src/builder/text/normalize.py", "src/utils/helpers.py",
                  "src/models/core.py", "src/builder/timeline/index.py", "src/builder/text/stopwords.py")
PARAMETROS_NAO_DEFINIDOS = ("temperature", "top_p", "top_k", "max_output_tokens", "seed", "candidate_count",
                            "presence_penalty", "frequency_penalty", "stop_sequences", "thinking_config", "safety_settings")


def distribuicoes():
    return sorted(f"{d.metadata['Name']}=={d.version}" for d in metadata.distributions() if d.metadata["Name"])


def normativo_protocolo():
    txt = PROTOCOLO.read_text(encoding="utf-8")
    ini, fim = "<!-- NORMATIVO:INICIO -->", "<!-- NORMATIVO:FIM -->"
    exige(txt.count(ini) == 1 and txt.count(fim) == 1, "marcadores do bloco normativo ausentes no pré-registro")
    return txt.split(ini, 1)[1].split(fim, 1)[0]


def modelo_da_config():
    """Só o NOME do modelo (a chave nunca sai daqui)."""
    cfg = json.loads(CONFIG_USUARIO.read_text(encoding="utf-8"))
    return str(cfg.get("gemini_model") or ""), bool(str(cfg.get("gemini_api_key") or "").strip())


def id_limpo(normativo):
    return K.sha_json({"esquema": "vocab-limpo-congelamento-1", **normativo})


def congelar():
    modelo, tem_chave = modelo_da_config()     # antes das travas; só nome e presença
    t = travas_base("congelar")
    t.permite("referencia", STAGING, STAGING_MAN, INVENTARIO, ENSAIO, PROTOCOLO, somente_leitura=True)
    t.permite("saida", BASE)
    t.instala()
    exige(not CONG_LIMPO.exists(), "congelamento da recompilação já existe: não sobrescrevo")
    exige(tem_chave, "config sem chave da API")
    reg, inv = K.carrega_json_estrito(STAGING_MAN), K.carrega_json_estrito(INVENTARIO)
    for s, v in reg["cursos"].items():
        exige(K.arvore(DATA / v["staging"]) == v["arvore"], f"{s}: staging divergente do registrado")
    for s, lst in inv["cursos"].items():
        for c in lst:
            exige(K.sha_arq(DATA / c["arquivo"]) == c["bundle_sha256"], f"{s}/{c['indice']}: bundle salvo divergente")
    from src.builder.core import vocabulary_compile as VC
    from src.builder.runtime import gemini_client as GC
    exige(inv["system_sha256"] == K.sha_bytes(VC.SYSTEM.encode("utf-8")), "SYSTEM mudou desde o ensaio")
    exige(modelo == GC.DEFAULT_MODEL, f"modelo da config ({modelo}) != default do código ({GC.DEFAULT_MODEL})")
    with t.comandos({"git"}):
        head, erro = K.git("rev-parse", "HEAD", cwd=DATA)
        srcdiff, erro2 = K.git("status", "--porcelain", "--", "src", cwd=DATA)
    exige(not erro and not erro2 and not srcdiff.strip(), f"git falhou ou src/ com mudanças: {erro or erro2 or srcdiff[:200]}")
    normativo = {
        "protocolo": {"arquivo": rel(PROTOCOLO), "protocolo_sha": K.sha_bytes(normativo_protocolo().encode("utf-8"))},
        "codigo_rodada": {n: K.sha_arq(p) for n, p in CODIGO_SCRIPTS.items()},
        "produto": {"head": head.strip(), "src_arvore_sha": K.sha_json(K.arvore(DATA / "src")),
                    "arquivos_chave": {a: K.sha_arq(DATA / a) for a in ARQUIVOS_CHAVE}},
        "interprete": {"executavel": sys.executable, "versao": sys.version, "distribuicoes_sha": K.sha_json(distribuicoes()),
                       "sdk": {n: metadata.version(n) for n in ("google-genai", "pydantic", "httpx")}},
        "ambiente": K.descritor_ambiente(os.environ),
        "modelo": {"identificador": modelo, "tipo": "alias (sem versão imutável no código)",
                   "fonte": "~/.gpt_tutor_config.json gemini_model = gemini_client.DEFAULT_MODEL",
                   "historico_vocab_llm": "gemini-3.5-flash (_modelo dos 7 sidecars históricos)"},
        "chamada": {"funcao": "vocabulary_compile.compile_course_vocabulary(root, entries, load_internal_content_taxonomy(root), client)",
                    "system_sha256": inv["system_sha256"], "system": inv["system"],
                    "response_mime_type": "application/json", "response_schema_sha256": inv["schema_sha256"],
                    "response_schema": VC.Vocab.model_json_schema(),
                    "parametros_nao_definidos_no_codigo": list(PARAMETROS_NAO_DEFINIDOS),
                    "nota": "valores efetivos = defaults do serviço (não observáveis nem versionados); sem semente"},
        "politicas": {
            "retry": "gemini_client.summarize_bundle: até 5 tentativas da mesma request, só ClientError 429/RESOURCE_EXHAUSTED e "
                     "ServerError 5xx; espera 1 s dobrando até 60 s; demais erros e parsed=None sem retry",
            "timeout": "nenhum no código (default do SDK google-genai)",
            "falha": "unidade em _unidades_com_erro, sem termos; nada completado à mão",
            "parsing": "resp.parsed pelo schema Vocab; tópico casa por label exato (espaços colapsados); termos com espaços "
                       "colapsados; vazios descartados",
            "normalizacao_dedup_descarte": "vocabulary_compile.filter_terms (duplicata, termo=label, termo em >1 tópico, "
                                           "identidade com outra unidade/tópico, só genéricos df, rótulos meta)",
            "bundle": "vocabulary_compile._bundle (título, label Moodle, até 24 headings de 60 caracteres, nomes-base dos "
                      "membros extraídos; corte em MAX_BUNDLE_CHARS=24000)"},
        "entradas": {"congelamento_fase1": ID5, "captura_cru": reg["fonte"]["captura_cru"],
                     "staging_registro_sha256": K.sha_arq(STAGING_MAN), "staging_arvore_sha": reg["arvore_sha"],
                     "unidade_substituida_pelo_cru": {s: v["unidade_substituida_pelo_cru"] for s, v in reg["cursos"].items()}},
        "inventario": {"arquivo": rel(INVENTARIO), "sha256": K.sha_arq(INVENTARIO), "total_chamadas": inv["total_chamadas"],
                       "chamadas": {s: [[c["indice"], c["unidade"], c["bundle_sha256"], c["chars"]] for c in lst]
                                    for s, lst in inv["cursos"].items()}},
        "rede": {"hosts_permitidos": sorted(HOSTS_PERMITIDOS), "somente_em": "--compilar"},
    }
    cong = {"normativo": normativo, "id_recompilacao": id_limpo(normativo)}
    K.grava_atomico(CONG_LIMPO, cong)
    t.rehash_leituras()
    print("CONGELADO", cong["id_recompilacao"], "| chamadas", inv["total_chamadas"], "| modelo", modelo, flush=True)
    K.encerra(t, ok=True, codigo_falha=1)


def carrega_congelamento_conferido():
    """Tudo o que o congelamento fixa é conferido de novo; divergência interrompe antes da rede."""
    cong = K.carrega_json_estrito(CONG_LIMPO)
    n = cong["normativo"]
    prob = []
    if id_limpo(n) != cong["id_recompilacao"]:
        prob.append("id_recompilacao não confere com o normativo")
    if K.sha_bytes(normativo_protocolo().encode("utf-8")) != n["protocolo"]["protocolo_sha"]:
        prob.append("protocolo (bloco normativo) mudou")
    prob += [f"código da rodada mudou: {k}" for k, p in CODIGO_SCRIPTS.items() if K.sha_arq(p) != n["codigo_rodada"][k]]
    if K.sha_json(K.arvore(DATA / "src")) != n["produto"]["src_arvore_sha"]:
        prob.append("árvore src/ mudou")
    if K.sha_json(distribuicoes()) != n["interprete"]["distribuicoes_sha"] or sys.version != n["interprete"]["versao"]:
        prob.append("intérprete ou distribuições mudaram")
    prob += [f"ambiente: {p}" for p in K.verifica_ambiente(os.environ)]
    if K.sha_arq(INVENTARIO) != n["inventario"]["sha256"] or K.sha_arq(STAGING_MAN) != n["entradas"]["staging_registro_sha256"]:
        prob.append("inventário ou registro do staging mudou")
    reg = K.carrega_json_estrito(STAGING_MAN)
    for s, v in reg["cursos"].items():
        if K.arvore(DATA / v["staging"]) != v["arvore"]:
            prob.append(f"{s}: staging mudou")
    exige(not prob, f"congelamento da recompilação não confere: {prob[:5]}")
    return cong, reg


# ------------------------------------------------------------------------------------------- geração oficial
class Aborto(BaseException):
    """Escapa do `except Exception` do compilador: request fora do inventário interrompe a rodada inteira."""


class Gravador:
    """Envolve `models.generate_content` do SDK: confere a request contra o inventário ANTES de enviar e grava tudo."""

    def __init__(self, original, inventario, modelo):
        self.original, self.inventario, self.modelo = original, inventario, modelo
        self.curso, self.i, self.tentativa, self.ultimo = None, -1, 0, None
        self.registros = []
        self.hosts = collections.Counter()

    def iniciar(self, curso):
        self.curso, self.i, self.tentativa, self.ultimo = curso, -1, 0, None

    def _grava(self, nome, obj):
        K.grava_atomico(CHAMADAS / nome, obj)
        return rel(CHAMADAS / nome), K.sha_arq(CHAMADAS / nome)

    def __call__(self, *, model, contents, config):
        sha = K.sha_bytes(str(contents).encode("utf-8"))
        if sha != self.ultimo:
            self.i, self.tentativa, self.ultimo = self.i + 1, 0, sha
        self.tentativa += 1
        esperadas = self.inventario[self.curso]
        if self.i >= len(esperadas) or esperadas[self.i]["bundle_sha256"] != sha or model != self.modelo:
            raise Aborto(f"{self.curso}/{self.i}: request fora do inventário congelado (ou modelo divergente)")
        exp = esperadas[self.i]
        base = f"{self.curso}_{self.i:02d}_t{self.tentativa}"
        try:
            cfg = config.model_dump(mode="json", exclude_none=True, exclude={"response_schema"})
        except Exception as exc:  # noqa: BLE001
            cfg = {"_erro_serializacao": f"{type(exc).__name__}: {exc}"}
        req_arq, req_sha = self._grava(f"{base}_request.json", {"model": model, "contents": contents, "config": cfg,
                                                                "response_schema_sha256": self.inventario["_schema_sha256"]})
        rec = {"curso": self.curso, "indice": self.i, "unidade": exp["unidade"], "tentativa": self.tentativa,
               "inicio": agora(), "modelo_pedido": model, "request": {"arquivo": req_arq, "sha256": req_sha,
                                                                      "contents_sha256": sha}}
        t0 = time.time()
        try:
            resp = self.original(model=model, contents=contents, config=config)
        except Exception as exc:
            rec.update(fim=agora(), segundos=round(time.time() - t0, 2), status="erro",
                       erro={"tipo": type(exc).__name__, "mensagem": str(exc)[:4000]})
            self.registros.append(rec)
            raise
        try:
            bruto = resp.model_dump(mode="json", exclude_none=True)
        except Exception as exc:  # noqa: BLE001
            bruto = {"_erro_serializacao": f"{type(exc).__name__}: {exc}", "text": getattr(resp, "text", None)}
        resp_arq, resp_sha = self._grava(f"{base}_response.json", bruto)
        parsed = getattr(resp, "parsed", None)
        rec.update(fim=agora(), segundos=round(time.time() - t0, 2), status="ok" if parsed is not None else "sem_parsed",
                   model_version=getattr(resp, "model_version", None),
                   response={"arquivo": resp_arq, "sha256": resp_sha},
                   parsed=parsed.model_dump() if hasattr(parsed, "model_dump") else None)
        self.registros.append(rec)
        return resp


def compilar():
    cong, reg = carrega_congelamento_conferido()      # antes de qualquer rede
    n = cong["normativo"]
    exige(not CHAMADAS.exists() and not (BASE / "compilacao.json").exists(), "geração oficial já executada: não repito")
    for s, nome in K.NOMES.items():
        exige(not (STAGING / nome / "course" / LLM_VOCAB).exists() and not (STAGING / nome / "course" / MANUAL_VOCAB).exists(),
              f"{s}: staging já tem sidecar")
    # chave: a config é lida como JSON puro ANTES das travas (não passa pelo registro de leituras, nunca é gravada,
    # impressa nem hasheada); src/ e o SDK só são importados DEPOIS das travas (.env e a config ficam negados)
    cfg = json.loads(CONFIG_USUARIO.read_text(encoding="utf-8"))
    inv = K.carrega_json_estrito(INVENTARIO)
    inventario = {**inv["cursos"], "_schema_sha256": inv["schema_sha256"]}
    originais = {"getaddrinfo": socket.getaddrinfo, "connect": socket.socket.connect,
                 "connect_ex": socket.socket.connect_ex, "create_connection": socket.create_connection}

    t = travas_base("compilar")
    t.permite("sistema", Path(DATA.anchor), somente_leitura=True)   # leituras fora da lista são registradas, não barradas
    t.permite("staging", STAGING, somente_leitura=True)
    t.permite("referencia", CONG_LIMPO, INVENTARIO, STAGING_MAN, PROTOCOLO, ENSAIO, somente_leitura=True)
    saidas = [BASE]   # grava_atomico usa temporário na pasta-mãe; staging e referências seguem só leitura (raiz mais longa)
    for nome in K.NOMES.values():
        out = STAGING / nome / "course" / LLM_VOCAB
        saidas += [out, out.with_name(out.name + ".tmp")]
    t.permite("saida", *saidas)
    t.congela(STAGING, {f"{Path(v['staging']).name}/{k}": h for v in reg["cursos"].values() for k, h in v["arvore"].items()})
    t.instala()
    CHAMADAS.mkdir(parents=True)

    def getaddrinfo_restrito(host, *a, **k):
        if str(host).lower() not in HOSTS_PERMITIDOS:
            t.registra("rede", f"host não autorizado: {host}")
            raise K.Violacao("host fora da lista")
        gravador.hosts[str(host).lower()] += 1
        return originais["getaddrinfo"](host, *a, **k)

    socket.getaddrinfo = getaddrinfo_restrito
    socket.socket.connect, socket.socket.connect_ex = originais["connect"], originais["connect_ex"]
    socket.create_connection = originais["create_connection"]

    from src.builder.runtime.gemini_client import get_gemini_client
    cliente = get_gemini_client(cfg)
    del cfg
    exige(cliente is not None and cliente.model == n["modelo"]["identificador"], "cliente ausente ou modelo divergente")
    cliente._ensure_client()
    gravador = Gravador(cliente._client.models.generate_content, inventario, cliente.model)
    cliente._client.models.generate_content = gravador
    from src.builder.core import vocabulary_compile as VC
    from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
    R = {"id_recompilacao": cong["id_recompilacao"], "inicio": agora(), "cursos": {}}
    abortado = None
    try:
        for s, nome in K.NOMES.items():
            root = STAGING / nome
            gravador.iniciar(s)
            entries = K.carrega_json_estrito(root / "manifest_staging.json")["entries"]
            res = VC.compile_course_vocabulary(root, entries, load_internal_content_taxonomy(root), cliente)
            regs = [r for r in gravador.registros if r["curso"] == s]
            R["cursos"][s] = {"chamadas_previstas": len(inventario[s]), "unidades_chamadas": len({r["indice"] for r in regs}),
                              "tentativas": len(regs), "retries": len(regs) - len({r["indice"] for r in regs}),
                              "erros_de_chamada": [r for r in regs if r["status"] != "ok"],
                              "unidades_com_erro": list((res or {}).get("_unidades_com_erro") or []),
                              "sidecar_sha256": K.sha_arq(root / "course" / LLM_VOCAB) if (root / "course" / LLM_VOCAB).exists() else None}
            print(f"  {s}: {R['cursos'][s]['unidades_chamadas']}/{len(inventario[s])} unidades, "
                  f"{R['cursos'][s]['tentativas']} tentativas, erros {R['cursos'][s]['unidades_com_erro']}", flush=True)
    except Aborto as exc:
        abortado = str(exc)
    R["fim"] = agora()
    R["abortado"] = abortado
    R["registros"] = gravador.registros
    R["hosts_resolvidos"] = dict(gravador.hosts)
    t.rehash_leituras()
    R["violacoes"], R["negados"] = t.violacoes, t.negados
    R["completa"] = (abortado is None and not t.violacoes
                     and all(v["unidades_chamadas"] == v["chamadas_previstas"] for v in R["cursos"].values())
                     and len(R["cursos"]) == len(K.NOMES))
    K.grava_atomico(BASE / "compilacao.json", R)
    print("GERACAO", "COMPLETA" if R["completa"] else "INCOMPLETA", "| abortado:", abortado, "| violacoes:", len(t.violacoes), flush=True)
    K.encerra(t, ok=R["completa"], codigo_falha=1)


if __name__ == "__main__":
    platform.uname()
    platform.platform()   # aquece o cache antes das travas (no Windows a 1ª consulta executa `ver`)
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"--staging": staging, "--ensaio": ensaio, "--congelar": congelar,
     "--compilar": compilar}.get(cmd, lambda: sys.exit(f"subcomando desconhecido: {cmd}"))()
