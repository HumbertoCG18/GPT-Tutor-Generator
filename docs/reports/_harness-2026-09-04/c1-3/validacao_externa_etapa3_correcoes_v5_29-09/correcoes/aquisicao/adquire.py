"""Aquisição prospectiva de candidatos N0 (etapa restrita de 29/09), sob `manifesto_aquisicao.json` (fixado antes da rede).

Rede só para o catálogo da própria conta e os materiais dos cursos dela, pelo webservice do Moodle com o token já
configurado no produto (o executor nunca lê nem imprime o valor). Usa do produto só `MoodleClient` (chamadas de
webservice), `parse_moodle_course`, `sanitize_folder_name` e `looks_like_expected`; nenhum pipeline de ingestão,
atribuição, LLM ou sidecar. Nunca imprime nem grava URL com parâmetro de autenticação, token, cookie ou credencial;
erros de rede são registrados só pelo tipo (a mensagem pode conter a URL autenticada).

v3 (etapa 3, sem rede; ../../../validacao_externa_etapa2_29-09/aquisicao/adquire.py é a versão executada em 29/09):
- anexo de página fora da raiz do curso tem referência válida (`base` + `caminho` relativo a ela) e é congelado;
- limites por arquivo e total valem para os bytes REAIS (leitura cortada em limite + 1), além do `filesize` declarado;
- falha de um arquivo vira status `falha_local:<Tipo>` e o curso continua; os registros vão para a lista do chamador
  na hora e o inventário é gravado a cada curso e no `finally` (`concluido: false` se interrompido);
- `filepath` do Moodle registrado; nenhum arquivo sobrescrito; `congelar` recusa inventário parcial.

v4 (correções pós-revisão da etapa 3, sem rede; v3 em ../../../validacao_externa_etapa3_29-09/correcoes/aquisicao/):
- registro antes da gravação (`status: gravando`, `caminho` + `caminho_parcial`); gravação em `.parcial` + `os.replace`;
  falha local mantém a referência ao parcial (`bytes_gravados`); `grava_json` atômico (inventário e `contents.json`);
- corpo menor que o Content-Length = `falha_http:IncompleteRead` (regressão da v3 corrigida);
- alvo resolvido fora da base = `caminho_inseguro`, sem baixar;
- contadores separados: `bytes_transferidos` (tudo que chegou, inclusive recusados e o byte de sondagem, que só é lido
  se couber no orçamento restante), `bytes_aceitos` (corpos gravados) e `bytes_metadados` (não medido: impedimento
  registrado, sem alterar src/). O limite total vale para os transferidos. Esquema `inventario-downloads-3`.

v5 (Gate 1 parcial de 29/09: R-META e R-PAGE; v4 em ../../../validacao_externa_etapa3_correcoes_29-09/):
- orçamento = bytes dos CORPOS HTTP lidos pela aplicação (webservice pelo `MoodleClient`, downloads pelo
  `baixa_arquivo`); não inclui cabeçalhos, TLS, retransmissões nem outro tráfego. O catálogo (`site_info`,
  `get_users_courses`) e `get_course_contents` são medidos pelo cliente; os deltas entram no orçamento também quando a
  chamada falha (JSON inválido, erro da API, resposta incompleta, orçamento excedido);
- R-PAGE (regra operacional provisória, inferida das respostas locais disponíveis, inclusive o lote; não é contrato
  confirmado do Moodle): HTML principal = conteúdo `index.html` com `filepath "/"` e `filesize 0`; exatamente um.
  Zero ou vários = registro `html_principal_ausente|ambiguo` (não coberto, no denominador); o resto é anexo.

Modos (em ordem):
  python adquire.py --catalogo    catálogo (campos permitidos) + triagem (exclusões, exposição, ordem)
  python adquire.py --baixar      baixa as disciplinas N0 em ordem, sob orçamento e regra de parada
  python adquire.py --congelar    árvores sha256 por curso + sha256 do inventário
"""
import hashlib
import importlib.util
import json
import logging
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
logging.disable(logging.CRITICAL)
AQUI = Path(__file__).resolve().parent
REPO = next(p for p in AQUI.parents if (p / ".git").is_dir())
HOME = Path.home()
ETAPA2 = AQUI.parents[2] / "validacao_externa_etapa2_29-09"   # v3: manifesto, enumerador e candidatos da etapa 2
MAN_P = ETAPA2 / "aquisicao/manifesto_aquisicao.json"
MAN = json.loads(MAN_P.read_text(encoding="utf-8"))
DESTINO = REPO / ".frzero/validacao_externa_aquisicao_29-09"
SAL = "vocab-validacao-externa-2026-09-29"
ORC = MAN["orcamento"]
MAX_ELEGIVEIS, MAX_FALHAS_SEGUIDAS = 6, 3
PARAM_AUTENTICACAO = re.compile(r"^(ws)?token$|^sesskey$|^key$|^sig(nature)?$|^access_token$|^auth", re.I)
IDS_CONHECIDOS = {"95473": "LR", "95227": "LSO", "92619": "UX"}   # ids citados no repositório (commit base)

sys.path.insert(0, str(REPO))
from src.builder.sources import moodle as M  # noqa: E402  (só funções de webservice, nomes e assinatura)

_spec = importlib.util.spec_from_file_location("enum_v2", ETAPA2 / "correcoes/populacao/enumera_candidatos.py")
EV2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(EV2)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def chave(nome):
    t = unicodedata.normalize("NFKD", str(nome or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", t.casefold())


def sem_autenticacao(url):
    partes = urllib.parse.urlsplit(str(url or ""))
    q = [(k, v) for k, v in urllib.parse.parse_qsl(partes.query, keep_blank_values=True) if not PARAM_AUTENTICACAO.match(k)]
    return urllib.parse.urlunsplit(partes._replace(query=urllib.parse.urlencode(q)))


def limpa_contents(o):
    """Resposta da API sem nenhum parâmetro de autenticação em URLs (defesa: a API não deveria trazê-los)."""
    if isinstance(o, dict):
        return {k: (sem_autenticacao(v) if k in ("fileurl", "url") and isinstance(v, str) else limpa_contents(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [limpa_contents(x) for x in o]
    return o


def grava_json(p, obj):
    """v4: publicação atômica (temporário no mesmo diretório + os.replace): interrupção não trunca o anterior.
    Sem fsync: cobre interrupção do processo, não queda de energia."""
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, p)


def cliente():
    url, token = M.load_moodle_token()
    if not token:
        sys.exit("sem token configurado: pare e peça a conta")
    cli = M.MoodleClient(url, token)
    del token
    return cli, url


def conhecidos():
    dados = json.loads((ETAPA2 / "correcoes/populacao/candidatos_29-09.json").read_text(encoding="utf-8"))
    return {chave(re.sub(r"\s*\(.*?\)\s*$", "", c["nome"])): c["sigla"] for c in dados["candidatos"]}


def pastas_anteriores():
    base = HOME / "Desktop/Moodle"
    return {chave(p.name) for p in base.iterdir() if p.is_dir()} if base.is_dir() else set()


# ------------------------------------------------------------------------------------------- catálogo e triagem
class RegistroIlegivel(RuntimeError):
    """Registro persistido de consumo ilegível ou inconsistente: nunca é tomado como consumo zero."""


def le_consumo_catalogo():
    """(registro, bytes_total) de `metadados_catalogo.json`; (None, None) se ausente. Ilegível ou inconsistente
    (total != soma, bytes negativos ou não inteiros) = RegistroIlegivel."""
    reg_p = AQUI / "metadados_catalogo.json"
    if not reg_p.exists():
        return None, None
    try:
        reg = json.loads(reg_p.read_text(encoding="utf-8"))
        parcelas = [e["bytes"] for e in reg["execucoes"]]
        valido = all(type(b) is int and b >= 0 for b in parcelas) and reg["bytes_total"] == sum(parcelas)
    except (ValueError, KeyError, TypeError) as exc:
        raise RegistroIlegivel(f"registro de consumo do catálogo ilegível ({type(exc).__name__}): não assumo zero") from None
    if not valido:
        raise RegistroIlegivel("registro de consumo do catálogo inconsistente: não assumo zero")
    return reg, reg["bytes_total"]


def catalogo():
    reg_cat, consumido = le_consumo_catalogo()   # v5: lido ANTES de qualquer requisição
    reg_cat = reg_cat or {"execucoes": []}
    cli, url = cliente()
    cli.limite_bytes = max(0, ORC["bytes_totais_max"] - (consumido or 0))   # só o que resta do orçamento comum
    erro = "interrompido"   # vale se uma interrupção (BaseException) escapar das chamadas
    try:
        site = cli.site_info()
        host_ok = urllib.parse.urlsplit(str(site.get("siteurl") or "")).netloc == urllib.parse.urlsplit(url).netloc
        cursos = cli.get_users_courses(site["userid"])
        del site
        erro = None
    except Exception as exc:   # noqa: BLE001
        erro = f"falha:{type(exc).__name__}"
        raise
    finally:   # bytes registrados em sucesso, falha ou interrupção; a exceção original propaga
        reg_cat["execucoes"].append({"bytes": cli.bytes_recebidos, "erro": erro})
        reg_cat["bytes_total"] = sum(e["bytes"] for e in reg_cat["execucoes"])
        grava_json(AQUI / "metadados_catalogo.json", reg_cat)
    known, anteriores = conhecidos(), pastas_anteriores()
    linhas, triagem = [], []
    for c in cursos:
        p = M.parse_moodle_course(c)
        full = str(c.get("fullname") or "")
        codigo = full.split(" - ", 1)[0].strip() if " - " in full else ""
        reg = {"id": str(c.get("id")), "shortname": str(c.get("shortname") or ""), "codigo": codigo, "nome": p["name"],
               "turma": p["turma"], "semestre": p["semester"], "startdate": c.get("startdate"), "enddate": c.get("enddate"),
               "category": c.get("category"), "visible": c.get("visible"), "format": c.get("format")}
        linhas.append(reg)
        t = {"id": reg["id"], "nome": reg["nome"], "semestre": reg["semestre"]}
        k = chave(reg["nome"])
        sigla = IDS_CONHECIDOS.get(reg["id"]) or known.get(k)
        parciais = sorted({s for kk, s in known.items() if kk and (kk in k or k in kk)}) if not sigla and k else []
        if not reg["semestre"]:
            t.update(classe="nao_disciplina", motivo="fullname sem semestre AAAA/S")
        elif sigla in {"MF", "SO", "IA", "ES2", "TCC", "CG", "FR", "LR"}:
            t.update(classe="excluido_conhecido", sigla=sigla, motivo="desenvolvimento ou LR: fora da população principal")
        elif sigla in {"LSO", "UX"}:
            t.update(classe="N1_conhecido", sigla=sigla, motivo="já classificado N1 em 29/09: só piloto, não baixado")
        elif parciais:
            t.update(classe="excluido_correspondencia_parcial", siglas=parciais,
                     motivo="nome contém ou está contido no de um curso conhecido: excluído por cautela")
        else:
            alternativas = [rf"(?<!\d){re.escape(reg['id'])}(?!\d)", re.escape(reg["nome"])] + \
                ([re.escape(codigo)] if len(codigo) >= 4 else [])
            ex = EV2.exposicao({"padrao": "|".join(alternativas)})
            anterior = chave(reg["nome"]) in anteriores or chave(p["slug"]) in anteriores
            nivel = "N1" if (anterior and ex["nivel"] == "N0") else ex["nivel"]
            t.update(classe=nivel, exposicao={"mencoes_repo": ex["mencoes_repo"], "exemplos": ex["exemplos"],
                                              "commits": ex["commits"], "falhas_da_busca": ex["falhas_da_busca"],
                                              "download_anterior": anterior},
                     motivo={"N0": "nenhuma exposição encontrada", "N1": "exposição no repositório ou download anterior",
                             "INDETERMINADO": "busca de exposição falhou"}[nivel])
        t["ordem"] = sha(f"{SAL}|moodle:{reg['id']}".encode())
        triagem.append(t)
    grava_json(AQUI / "catalogo.json", {"esquema": "catalogo-1", "host_confere_com_a_conta": host_ok,
                                        "n": len(linhas), "cursos": sorted(linhas, key=lambda x: int(x["id"]))})
    ordem = sorted((t for t in triagem if t["classe"] == "N0"), key=lambda t: t["ordem"])
    grava_json(AQUI / "triagem.json", {"esquema": "triagem-1", "manifesto_sha256": sha(MAN_P.read_bytes()),
                                       "bytes_metadados_catalogo": reg_cat["bytes_total"],
                                       "cursos": sorted(triagem, key=lambda t: int(t["id"])),
                                       "ordem_de_download": [t["id"] for t in ordem]})
    contagem = {}
    for t in triagem:
        contagem[t["classe"]] = contagem.get(t["classe"], 0) + 1
    print("catálogo:", len(linhas), "cursos | host confere:", host_ok, "| classes:", contagem, "| N0 na ordem:", len(ordem))


# ------------------------------------------------------------------------------------------- download
DEFINICAO_ORCAMENTO = ("bytes dos corpos HTTP lidos pela aplicação: respostas do webservice (medidas pelo MoodleClient) e "
                       "downloads de arquivos; não inclui cabeçalhos, TLS, retransmissões nem outro tráfego de rede. O tamanho "
                       "do JSON reserializado não é medida de transferência.")


def eh_html_principal(c):
    """R-PAGE: `index.html`, `filepath "/"`, `filesize 0` (campos ausentes = não é candidato)."""
    return c.get("type") == "file" and c.get("filename") == "index.html" and c.get("filepath") == "/" and c.get("filesize") == 0


def baixa_arquivo(cli, fileurl, nome, limite_arquivo, restante):
    """(bytes, status, bytes recebidos). Lê no máximo `min(limite + 1, restante)`: o byte de sondagem só é lido se couber
    no orçamento restante. Corpo menor que o Content-Length = transferência incompleta (como na v2)."""
    teto = min(limite_arquivo + 1, restante)
    if teto <= 0:
        return None, "nao_baixado_orcamento_real", 0
    try:
        with urllib.request.urlopen(cli._download_url(fileurl), timeout=120) as r:
            ctype = (r.headers.get("content-type") or "").lower()
            declarado = str(r.headers.get("content-length") or "").strip()
            dados = r.read(teto)
    except urllib.error.HTTPError as exc:
        return None, f"falha_http:{exc.code}", 0
    except Exception as exc:   # noqa: BLE001  (só o tipo: a mensagem pode conter a URL autenticada)
        return None, f"falha_http:{type(exc).__name__}", 0
    n = len(dados)
    if n > limite_arquivo:
        return None, "acima_do_limite_real", n
    if declarado.isdigit() and n < int(declarado):   # corpo parou antes do tamanho anunciado
        return None, ("nao_baixado_orcamento_real" if n == teto else "falha_http:IncompleteRead"), n
    if not declarado.isdigit() and n == teto:   # cheio até o orçamento, sem como confirmar o fim sem ler mais
        return None, "nao_baixado_orcamento_real", n
    if ctype.startswith(("text/html", "application/json")) and not nome.lower().endswith((".html", ".htm", ".json")):
        return None, "tipo_inesperado", n
    if not M.looks_like_expected(nome, dados):
        return None, "assinatura_invalida", n
    return dados, "ok", n


def nao_sobrescreve(alvo):
    stem, suf, k = alvo.stem, alvo.suffix, 2
    while alvo.exists():
        alvo, k = alvo.with_name(f"{stem} ({k}){suf}"), k + 1
    return alvo


def baixa_curso(cli, cid, raiz, orcamento, arquivos):
    """Acrescenta em `arquivos` (lista do chamador) um registro por item; o de um download aceito entra ANTES da gravação
    (`status: gravando`, com `caminho` e `caminho_parcial`), então interrupção em qualquer ponto deixa referência.

    Gravação: `<alvo>.parcial` e depois `os.replace`. `caminho` é relativo à `base`: "curso" (a raiz do curso) ou
    "anexos_de_pagina" (`<id>_anexos_de_pagina`, ao lado). Alvo resolvido fora da base = `caminho_inseguro`, sem baixar.
    `orcamento`: {"transferidos": bytes recebidos, inclusive recusados e sondagem; "aceitos": corpos gravados}."""
    antes = cli.bytes_recebidos
    cli.limite_bytes = antes + max(0, ORC["bytes_totais_max"] - orcamento["transferidos"])   # orçamento comum restante
    try:
        contents = cli.get_course_contents(cid)
    finally:   # delta publicado também na falha (JSON inválido, erro da API, incompleta, orçamento excedido)
        delta = cli.bytes_recebidos - antes
        orcamento["transferidos"] += delta
        orcamento["metadados"] = orcamento.get("metadados", 0) + delta
    grava_json(raiz / "raw/moodle/contents.json", limpa_contents(contents))
    anexos = raiz.parent / f"{raiz.name}_anexos_de_pagina"
    for sec in contents or []:
        secao = M.sanitize_folder_name(str(sec.get("name") or ""))
        for mod in sec.get("modules") or []:
            modname, mid = str(mod.get("modname")), str(mod.get("id"))
            principal = None
            if modname == "page":   # R-PAGE: exatamente um HTML principal; senão, ocorrência não coberta registrada
                cands = [c for c in mod.get("contents") or [] if eh_html_principal(c)]
                if len(cands) == 1:
                    principal = cands[0]
                else:
                    arquivos.append({"secao": secao, "modulo_id": mid, "modname": modname, "arquivo": "index.html",
                                     "papel": "html_principal", "candidatos": len(cands),
                                     "status": "html_principal_ausente" if not cands else "html_principal_ambiguo"})
            for c in mod.get("contents") or []:
                nome = str(c.get("filename") or "")
                reg = {"secao": secao, "modulo_id": mid, "modname": modname, "arquivo": nome, "filepath": c.get("filepath"),
                       "tamanho_api": c.get("filesize")}
                if c.get("type") == "url" or modname == "url":
                    arquivos.append({**reg, "status": "link_externo"})
                    continue
                if c.get("type") != "file" or not nome or not c.get("fileurl"):
                    arquivos.append({**reg, "status": "sem_arquivo"})
                    continue
                try:
                    base, base_dir = "curso", raiz
                    if modname == "page" and c is principal:
                        reg["papel"] = "html_principal"
                        alvo = nao_sobrescreve(raiz / "raw/moodle/pages" / f"{mid}-index.html")
                    elif modname == "page":   # anexo de página (inclusive .html): fora da raiz do curso
                        reg["papel"] = "anexo_de_pagina"
                        base, base_dir = "anexos_de_pagina", anexos
                        alvo = nao_sobrescreve(anexos / f"{mid}-{nome}")
                    else:
                        alvo = raiz / "stash" / secao / nome
                        if alvo.exists():   # colisão de nome na seção: pasta do módulo (+ subpasta do Moodle), nunca sobrescreve
                            sub = [x for x in str(c.get("filepath") or "").strip("/").split("/") if x]
                            alvo = nao_sobrescreve(raiz / "stash" / secao / f"_mod{mid}" / Path(*sub, nome))
                            reg["colisao"] = True
                    if not alvo.resolve().is_relative_to(base_dir.resolve()):
                        arquivos.append({**reg, "status": "caminho_inseguro"})
                        continue
                    if (c.get("filesize") or 0) > ORC["bytes_por_arquivo_max"]:
                        arquivos.append({**reg, "status": "acima_do_limite"})
                        continue
                    if orcamento["transferidos"] + (c.get("filesize") or 0) > ORC["bytes_totais_max"]:
                        arquivos.append({**reg, "status": "nao_baixado_orcamento"})
                        continue
                    dados, status, lidos = baixa_arquivo(cli, c["fileurl"], nome, ORC["bytes_por_arquivo_max"],
                                                         ORC["bytes_totais_max"] - orcamento["transferidos"])
                    orcamento["transferidos"] += lidos
                    reg["bytes_lidos"] = lidos
                    if dados is None:
                        arquivos.append({**reg, "status": status})
                        continue
                    parcial = alvo.with_name(alvo.name + ".parcial")
                    reg.update(base=base, caminho=alvo.relative_to(base_dir).as_posix(),
                               caminho_parcial=parcial.relative_to(base_dir).as_posix(), sha256=sha(dados), bytes=len(dados),
                               status="gravando")
                    arquivos.append(reg)   # registro antes da gravação
                    alvo.parent.mkdir(parents=True, exist_ok=True)
                    parcial.write_bytes(dados)
                    os.replace(parcial, alvo)
                    del reg["caminho_parcial"]
                    reg["status"] = "ok"
                    orcamento["aceitos"] += len(dados)
                except Exception as exc:   # noqa: BLE001  falha local de um arquivo: registrada, o curso continua
                    reg["status"] = f"falha_local:{type(exc).__name__}"
                    for k in ("caminho", "sha256", "bytes"):
                        reg.pop(k, None)
                    if reg.get("caminho_parcial") and (base_dir / reg["caminho_parcial"]).exists():
                        reg["bytes_gravados"] = (base_dir / reg["caminho_parcial"]).stat().st_size   # parcial referenciado
                    else:
                        reg.pop("caminho_parcial", None)
                    if not any(a is reg for a in arquivos):
                        arquivos.append(reg)


def baixar():
    tri = json.loads((AQUI / "triagem.json").read_text(encoding="utf-8"))
    if (AQUI / "inventario_downloads.json").exists() or DESTINO.exists():
        sys.exit("download já executado: não repito nem sobrescrevo")
    _, catalogo_bytes = le_consumo_catalogo()   # o registro vale sobre a triagem (que pode ser anterior a tentativas)
    na_triagem = tri.get("bytes_metadados_catalogo")
    impedimentos = []
    if catalogo_bytes is None:
        catalogo_bytes = na_triagem or 0
        impedimentos.append("registro de consumo do catálogo ausente: consumo do catálogo "
                            + ("tomado da triagem (limite inferior)" if na_triagem is not None else "não contado"))
    elif na_triagem is not None and na_triagem > catalogo_bytes:
        raise RegistroIlegivel("triagem registra mais consumo do catálogo que o registro persistido: inconsistente")
    cli, _ = cliente()
    orcamento = {"transferidos": catalogo_bytes, "aceitos": 0, "metadados": catalogo_bytes}
    cursos, elegiveis, falhas_seguidas, parada = [], 0, 0, "fim das disciplinas N0 do catálogo"
    nomes = {t["id"]: t for t in tri["cursos"]}
    concluido = False
    try:
        for n, cid in enumerate(tri["ordem_de_download"], 1):
            if len(cursos) >= ORC["cursos_baixados_max"]:
                parada = "10 cursos baixados"
                break
            if elegiveis >= MAX_ELEGIVEIS:
                parada = "6 cursos elegíveis (E2, E3, E4)"
                break
            if orcamento["transferidos"] >= ORC["bytes_totais_max"]:
                parada = "orçamento de bytes atingido"
                break
            raiz = DESTINO / cid
            t0 = time.time()
            curso = {"id": cid, "nome": nomes[cid]["nome"], "semestre": nomes[cid]["semestre"], "ordem": n,
                     "erro": "interrompido", "arquivos": []}
            cursos.append(curso)   # antes do download: interrupção ainda deixa o parcial no inventário
            try:
                baixa_curso(cli, cid, raiz, orcamento, curso["arquivos"])
                erro = None
            except urllib.error.HTTPError as exc:
                erro = f"falha_http:{exc.code}"
            except M.OrcamentoExcedido:
                erro = "nao_baixado_orcamento_real:metadados"
            except Exception as exc:   # noqa: BLE001
                erro = f"falha:{type(exc).__name__}"
            falhas_seguidas = falhas_seguidas + 1 if erro else 0
            est = EV2.estrutura(raiz) if raiz.is_dir() else {"potencialmente_adjudicaveis": 0, "com_fonte_local": 0}
            pl = EV2.plano({"fonte": str(raiz)}) if raiz.is_dir() else {"disponivel": False}
            e2, e3, e4 = pl["disponivel"], est.get("potencialmente_adjudicaveis", 0) >= EV2.MIN_ADJUDICAVEIS_CURSO, EV2.e4(est)
            elegiveis += bool(e2 and e3 and e4)
            status = {}
            for a in curso["arquivos"]:
                status[a["status"]] = status.get(a["status"], 0) + 1
            curso.update(erro=erro, segundos=round(time.time() - t0, 1), status_arquivos=status, E2=e2, E3=e3, E4=e4)
            print(f"  {n}. curso {cid}: {status} erro={erro} E2={e2} E3={e3} E4={e4}", flush=True)
            grava_inventario(parada, orcamento, cursos, tri, concluido=False, impedimentos=impedimentos)   # parcial
            if falhas_seguidas >= MAX_FALHAS_SEGUIDAS:
                parada = "3 cursos seguidos com falha (parada por erro)"
                break
        concluido = True
    finally:
        grava_inventario(parada if concluido else "interrompido", orcamento, cursos, tri, concluido, impedimentos)
    print("parada:", parada, "| cursos baixados:", len(cursos), "| elegíveis:", elegiveis, "| bytes:", orcamento)


def grava_inventario(parada, orcamento, cursos, tri, concluido, impedimentos=()):
    nao_baixados = [c for c in tri["ordem_de_download"] if c not in {x["id"] for x in cursos}]
    grava_json(AQUI / "inventario_downloads.json", {
        "esquema": "inventario-downloads-3", "concluido": concluido, "parada": parada,
        "definicao_orcamento": DEFINICAO_ORCAMENTO, "bytes_transferidos": orcamento["transferidos"],
        "bytes_aceitos": orcamento["aceitos"], "bytes_metadados": orcamento.get("metadados", 0),
        "impedimentos": list(impedimentos), "cursos": cursos, "n0_nao_baixados_por_parada": nao_baixados})


def congelar():
    inv_p = AQUI / "inventario_downloads.json"
    inv = json.loads(inv_p.read_text(encoding="utf-8"))
    if not inv.get("concluido", True):
        sys.exit("inventário parcial (download interrompido): não congelo")

    def arvore_de(d):
        return {p.relative_to(d).as_posix(): sha(p.read_bytes()) for p in sorted(d.rglob("*")) if p.is_file()} if d.is_dir() else {}

    cursos = {}
    for c in inv["cursos"]:
        arvores = {"curso": arvore_de(DESTINO / c["id"]), "anexos_de_pagina": arvore_de(DESTINO / f"{c['id']}_anexos_de_pagina")}
        esperado = {(a.get("base", "curso"), a["caminho"]): a["sha256"] for a in c["arquivos"] if a.get("caminho") and a["status"] == "ok"}
        parciais = {(a.get("base", "curso"), a["caminho_parcial"]) for a in c["arquivos"] if a.get("caminho_parcial")}
        cursos[c["id"]] = {"arvore": arvores["curso"], "arvore_anexos_de_pagina": arvores["anexos_de_pagina"],
                           "arvore_sha": sha(json.dumps(arvores, sort_keys=True).encode()),
                           "arquivos_ok_conferem": all(arvores[b].get(k) == v for (b, k), v in esperado.items()),
                           "parciais_referenciados": sorted(f"{b}:{k}" for b, k in parciais),
                           "extras_alem_dos_downloads": sorted(f"{b}:{k}" for b, arv in arvores.items() for k in arv
                                                               if (b, k) not in esperado and (b, k) not in parciais
                                                               and (b, k) != ("curso", "raw/moodle/contents.json"))}
    grava_json(AQUI / "fontes_congeladas.json", {"esquema": "fontes-congeladas-3", "inventario_sha256": sha(inv_p.read_bytes()),
                                                 "raiz": DESTINO.relative_to(REPO).as_posix(), "cursos": cursos})
    print("congelado:", {k: (len(v["arvore"]) + len(v["arvore_anexos_de_pagina"]), v["arquivos_ok_conferem"]) for k, v in cursos.items()})


if __name__ == "__main__":
    sys.exit("adquire v5 (R-META e R-PAGE, 29/09): sem rede, testado só com transporte falso. Nova aquisição exige "
             "manifesto novo, pasta própria e Gate de rede específico.")
