"""Validação externa do regime VOCAB — enumeração de candidatos, versão 2 (etapa restrita de 29/09).

Correções da revisão independente sobre a v1 (../../../validacao_externa_29-09/populacao/enumera_candidatos.py):
1. falha da busca de exposição (git ausente, commit base inexistente, padrão inválido, erro de execução) vira
   INDETERMINADO, nunca N0; INDETERMINADO não entra em nenhuma população;
2. E4 decidido por comparação inteira exata (local × 100 ≥ 90 × adjudicáveis), sem arredondamento;
3. candidatos como DADOS (JSON `candidatos-1`), separados do algoritmo; nenhum curso aparece neste arquivo.
Níveis, critérios, limiares, sal, orçamento e mínimos são os da v1, sem mudança.

Lê só: nomes e bytes (para hash) dos arquivos das fontes brutas, tipos de módulo do `contents.json` da API do Moodle e
o texto do repositório no commit base (evidência). NÃO lê manifest de tutor, taxonomia, timeline, sidecar, captura ou
placar. Uso: python enumera_candidatos.py <candidatos.json> <pasta de saída>
"""
import collections
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[6]   # raiz do repositório (conferida em exposicao() por git rev-parse --show-toplevel)
HOME = Path.home()

# ---------------------------------------------------------------- regra (idêntica à v1; limiares inteiros)
SAL = "vocab-validacao-externa-2026-09-29"
K_MAX = 6
MIN_CURSOS_GERAL = 3
MIN_ADJUDICAVEIS_GERAL = 100
MIN_ADJUDICAVEIS_CURSO = 10       # E3
MIN_PERCENT_LOCAL = 90            # E4: local * 100 >= 90 * adjudicáveis (exato)
BASE_EVIDENCIA = "bf46d51fc80d1e7dcc62c08cccd0399c056bcbe1"
EVIDENCIA_RAIZES = ["docs", "tests", "src", "scripts", ".mex", ".workflow"]
EVIDENCIA_EXCLUI = re.compile(r"_codegraph-benchmark|graphify-out|__pycache__|\.(exe|zip|pyc|png|jpg|pdf)$")
EXT_MATERIAL = {"pdf", "ppt", "pptx", "doc", "docx", "odt", "odp", "html", "htm", "ipynb", "zip", "py", "java", "c", "h",
                "cpp", "js", "ts", "sql", "txt", "md", "png", "jpg", "jpeg", "gif", "mp4", "xlsx", "csv"}
GERADOS_PELO_PRODUTO = re.compile(r"(^|/)(links\.json|manual-review/|raw/moodle/[^/]+\.json|raw/site/|stash/\.moodle_nomes\.json)"
                                  r"|_ARQUIVOS_DO_CARD\.txt$")
META = re.compile(r"plano|cronograma|ementa|programa[ _-]?d[ae]|apresenta[cç][aã]o da disciplina", re.I)
CAMPOS_CANDIDATO = {"sigla", "nome", "fonte", "padrao", "tutor", "plano_externo", "desenvolvimento", "origem"}


class DadosInvalidos(ValueError):
    pass


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def caminho(s):
    return Path(str(s).replace("~", str(HOME), 1)) if str(s).startswith("~") else Path(s)


def carrega_candidatos(p):
    dados = json.loads(Path(p).read_text(encoding="utf-8"))
    if dados.get("esquema") != "candidatos-1" or not isinstance(dados.get("candidatos"), list):
        raise DadosInvalidos("esquema candidatos-1 com lista de candidatos")
    siglas = [c.get("sigla") for c in dados["candidatos"]]
    if len(set(siglas)) != len(siglas) or not all(isinstance(s, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{0,15}", s) for s in siglas):
        raise DadosInvalidos("siglas inválidas ou repetidas")
    for c in dados["candidatos"]:
        if not {"sigla", "nome", "fonte", "padrao"} <= set(c) <= CAMPOS_CANDIDATO:
            raise DadosInvalidos(f"{c.get('sigla')}: campos fora do esquema {sorted(set(c) - CAMPOS_CANDIDATO)} "
                                 f"ou obrigatórios faltando {sorted({'sigla', 'nome', 'fonte', 'padrao'} - set(c))}")
    return dados


def git(repo, *args):
    """(código de saída, stdout); código None = git não pôde ser executado."""
    try:
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError:
        return None, ""
    return r.returncode, r.stdout


def estrutura(fonte):
    """Contagens estruturais da fonte bruta. Nenhum campo computado do produto é lido."""
    if not fonte.is_dir():
        return {"existe": False, "potencialmente_adjudicaveis": 0, "com_fonte_local": 0}
    arquivos = [p for p in fonte.rglob("*") if p.is_file()]
    materiais, ext, unicos = [], collections.Counter(), {}
    for p in arquivos:
        rel = p.relative_to(fonte).as_posix()
        e = p.suffix.lower().lstrip(".")
        if GERADOS_PELO_PRODUTO.search(rel) or e not in EXT_MATERIAL or "__pycache__" in rel:
            continue
        h = sha(p)
        if h in unicos:
            continue
        unicos[h] = rel
        ext[e] += 1
        materiais.append(rel)
    modulos = collections.Counter()
    cj = fonte / "raw/moodle/contents.json"
    if cj.is_file():
        for sec in json.loads(cj.read_text(encoding="utf-8")):
            for m in sec.get("modules") or []:
                modulos[str(m.get("modname"))] += 1
    urls = modulos.get("url", 0)
    meta = [r for r in materiais if META.search(Path(r).name)]
    adjudicaveis = len(materiais) + urls - len(meta)
    local = len(materiais) - len(meta)
    return {"existe": True, "arquivos_total": len(arquivos), "materiais_unicos_por_hash": len(materiais),
            "extensoes": dict(sorted(ext.items())), "modulos_moodle": dict(sorted(modulos.items())), "links_moodle": urls,
            "entries_brutas": len(materiais) + urls, "meta_por_nome": len(meta), "potencialmente_adjudicaveis": adjudicaveis,
            "com_fonte_local": local, "fracao_com_fonte_local": {"num": local, "den": adjudicaveis}}


def e4(est):
    """E4 exato: sem arredondamento, sem ponto flutuante."""
    n, d = est.get("com_fonte_local", 0), est.get("potencialmente_adjudicaveis", 0)
    return d > 0 and n * 100 >= MIN_PERCENT_LOCAL * d


def plano(c):
    if c.get("plano_externo"):
        p = caminho(c["plano_externo"])
        return {"disponivel": p.is_file(), "arquivo": c["plano_externo"], "sha256": sha(p) if p.is_file() else None}
    fonte = caminho(c["fonte"])
    cands = sorted(p for p in fonte.rglob("*") if p.is_file() and re.search(r"plano", p.name, re.I)
                   and p.suffix.lower() in {".pdf", ".docx", ".doc", ".md", ".html"}) if fonte.is_dir() else []
    return {"disponivel": bool(cands), "arquivo": str(cands[0]).replace(str(HOME), "~") if cands else None,
            "sha256": sha(cands[0]) if cands else None}


def exposicao(c, repo=REPO, base=BASE_EVIDENCIA, github=None):
    github = github if github is not None else repo.parent
    tutor = (github / c["tutor"]).is_dir() if c.get("tutor") else False
    falhas = []
    rc, topo = git(repo, "rev-parse", "--show-toplevel")
    if rc != 0 or Path(topo.strip()).resolve() != Path(repo).resolve():
        falhas.append(f"repositório de evidência não é a raiz do git (saiu {rc})")
    rc, _ = git(repo, "cat-file", "-e", f"{base}^{{commit}}")
    if rc != 0:
        falhas.append(f"commit base indisponível (git saiu {rc})")
    for raiz in EVIDENCIA_RAIZES:   # pathspec inexistente faria o grep "não achar nada" (saída 1) sem erro
        rc, _ = git(repo, "cat-file", "-e", f"{base}:{raiz}")
        if rc != 0:
            falhas.append(f"raiz de evidência ausente no commit base: {raiz}")
    rc_g, saida = git(repo, "grep", "-P", "-i", "-l", c["padrao"], base, "--", *EVIDENCIA_RAIZES)
    if rc_g not in (0, 1):   # 0 = achou, 1 = não achou; qualquer outro = a busca falhou
        falhas.append(f"git grep falhou (saiu {rc_g})")
    rc_l, log = git(repo, "log", base, "--oneline", "-i", "--perl-regexp", f"--grep={c['padrao']}")
    if rc_l != 0:
        falhas.append(f"git log falhou (saiu {rc_l})")
    hits = sorted({ln.split(":", 1)[1] for ln in saida.splitlines() if ":" in ln and not EVIDENCIA_EXCLUI.search(ln)})
    commits = log.splitlines() if rc_l == 0 else []
    if c.get("desenvolvimento"):
        nivel = "N3"
    elif tutor:
        nivel = "N2"
    elif falhas:
        nivel = "INDETERMINADO"
    elif hits or commits:
        nivel = "N1"
    else:
        nivel = "N0"
    return {"nivel": nivel, "tutor_construido": tutor, "falhas_da_busca": falhas, "mencoes_repo": len(hits),
            "exemplos": hits[:6], "commits": commits[:4]}


def classifica(c):
    est = estrutura(caminho(c["fonte"]))
    pl = plano(c)
    ex = exposicao(c)
    e2, e3, e4_ok = pl["disponivel"], est.get("potencialmente_adjudicaveis", 0) >= MIN_ADJUDICAVEIS_CURSO, e4(est)
    if ex["nivel"] == "N3":
        pop, motivo = "excluido", "desenvolvimento: gold visto e usado nas campanhas do motor"
    elif ex["nivel"] == "N2":
        pop, motivo = "smoke", "tutor construído e processado pelo motor; fora da população principal"
    elif ex["nivel"] == "INDETERMINADO":
        pop, motivo = "indeterminado", "busca de exposição falhou: " + "; ".join(ex["falhas_da_busca"])
    elif not (e2 and e3 and e4_ok):
        falta = [n for n, ok in (("plano", e2), (f">= {MIN_ADJUDICAVEIS_CURSO} adjudicáveis", e3),
                                 (f">= {MIN_PERCENT_LOCAL}% com fonte local (exato)", e4_ok)) if not ok]
        pop, motivo = "inelegivel", "falta: " + ", ".join(falta)
    elif ex["nivel"] == "N1":
        pop, motivo = "piloto", "exposição no repositório; nunca teve atribuição, gold ou vocabulário"
    else:
        pop, motivo = "geral", "nenhuma exposição encontrada"
    return {"sigla": c["sigla"], "nome": c["nome"], "fonte": c["fonte"], "origem": c.get("origem", ""), "estrutura": est,
            "plano": pl, "exposicao": ex, "E2_plano": e2, "E3_tamanho": e3, "E4_fonte_local": e4_ok, "populacao": pop,
            "motivo": motivo, "ordem_deterministica": hashlib.sha256(f"{SAL}|{c['sigla']}".encode()).hexdigest()}


def seleciona(linhas, pop):
    elegiveis = sorted((x for x in linhas if x["populacao"] == pop), key=lambda x: x["ordem_deterministica"])
    return [x["sigla"] for x in elegiveis[:K_MAX]], [x["sigla"] for x in elegiveis[K_MAX:]]


def main():
    dados_p, saida = Path(sys.argv[1]), Path(sys.argv[2])
    dados = carrega_candidatos(dados_p)
    linhas = [classifica(c) for c in dados["candidatos"]]
    geral, geral_fora = seleciona(linhas, "geral")
    piloto, piloto_fora = seleciona(linhas, "piloto")
    n_geral = sum(x["estrutura"].get("potencialmente_adjudicaveis", 0) for x in linhas if x["sigla"] in geral)
    out = {"regra": {"versao": 2, "sal": SAL, "K_MAX": K_MAX, "MIN_CURSOS_GERAL": MIN_CURSOS_GERAL,
                     "MIN_ADJUDICAVEIS_GERAL": MIN_ADJUDICAVEIS_GERAL, "MIN_ADJUDICAVEIS_CURSO": MIN_ADJUDICAVEIS_CURSO,
                     "MIN_PERCENT_LOCAL": MIN_PERCENT_LOCAL, "script_sha256": sha(__file__), "base_evidencia": BASE_EVIDENCIA,
                     "candidatos_arquivo": dados_p.name, "candidatos_sha256": sha(dados_p)},
           "candidatos": linhas,
           "proposta": {"generalizacao": geral, "generalizacao_fora_do_orcamento": geral_fora, "piloto_externo": piloto,
                        "piloto_fora_do_orcamento": piloto_fora,
                        "smoke_descritivo": [x["sigla"] for x in linhas if x["populacao"] == "smoke"],
                        "indeterminados": [x["sigla"] for x in linhas if x["populacao"] == "indeterminado"],
                        "adjudicaveis_generalizacao": n_geral,
                        "minimo_generalizacao_atingido": len(geral) >= MIN_CURSOS_GERAL and n_geral >= MIN_ADJUDICAVEIS_GERAL}}
    saida.mkdir(parents=True, exist_ok=True)
    base = saida / f"populacao_{dados_p.stem}"
    base.with_suffix(".json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    md = [f"# População (enumera_candidatos v2 sobre {dados_p.name}; gerado, não editar)", "",
          "| curso candidato | nível | plano | entries brutas | adjudicáveis | com fonte local | E2 | E3 | E4 | população | motivo |",
          "|---|---|---|---:|---:|---:|---|---|---|---|---|"]
    for x in linhas:
        est = x["estrutura"]
        md.append(f"| {x['sigla']} — {x['nome']} | {x['exposicao']['nivel']} | {'sim' if x['plano']['disponivel'] else 'não'} | "
                  f"{est.get('entries_brutas', 0)} | {est.get('potencialmente_adjudicaveis', 0)} | {est.get('com_fonte_local', 0)} | "
                  f"{x['E2_plano']} | {x['E3_tamanho']} | {x['E4_fonte_local']} | {x['populacao']} | {x['motivo']} |")
    p = out["proposta"]
    md += ["", f"- Generalização: {p['generalizacao'] or 'nenhum'} ({p['adjudicaveis_generalizacao']} adjudicáveis); mínimo "
               f"atingido: {p['minimo_generalizacao_atingido']}.", f"- Piloto externo: {p['piloto_externo'] or 'nenhum'}.",
           f"- Smoke descritivo: {p['smoke_descritivo'] or 'nenhum'}.", f"- Indeterminados: {p['indeterminados'] or 'nenhum'}."]
    base.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
