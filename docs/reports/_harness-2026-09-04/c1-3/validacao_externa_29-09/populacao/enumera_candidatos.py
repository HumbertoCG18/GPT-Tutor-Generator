"""Validação externa do regime VOCAB (29/09): enumeração de cursos candidatos por critérios NÃO preditivos.

Lê só: nomes e bytes (para hash) dos arquivos das fontes brutas locais, os tipos de módulo do `contents.json` da API do
Moodle e o texto do repositório (para evidência de exposição). NÃO lê manifest de tutor, taxonomia, timeline, sidecar,
captura, placar ou qualquer saída do motor. Candidatos, padrões, limiares e regra são declarados abaixo, antes de rodar.
Saída: populacao_candidata.json e populacao_candidata.md nesta pasta.
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
REPO = AQUI.parents[5]
HOME = Path.home()
GITHUB = REPO.parent
MOODLE = HOME / "Desktop/Moodle"

# ---------------------------------------------------------------- declarações (antes de qualquer contagem)
SAL = "vocab-validacao-externa-2026-09-29"
K_MAX = 6                      # orçamento de cursos por população
MIN_CURSOS_GERAL = 3           # mínimo amostral da validação de generalização
MIN_ADJUDICAVEIS_GERAL = 100   # idem, soma dos potencialmente adjudicáveis
MIN_ADJUDICAVEIS_CURSO = 10    # E3
MIN_FRACAO_LOCAL = 0.90        # E4
EXT_MATERIAL = {"pdf", "ppt", "pptx", "doc", "docx", "odt", "odp", "html", "htm", "ipynb", "zip", "py", "java", "c", "h",
                "cpp", "js", "ts", "sql", "txt", "md", "png", "jpg", "jpeg", "gif", "mp4", "xlsx", "csv"}
GERADOS_PELO_PRODUTO = re.compile(r"(^|/)(links\.json|manual-review/|raw/moodle/[^/]+\.json|raw/site/|stash/\.moodle_nomes\.json)"
                                  r"|_ARQUIVOS_DO_CARD\.txt$")
META = re.compile(r"plano|cronograma|ementa|programa[ _-]?d[ae]|apresenta[cç][aã]o da disciplina", re.I)
DESENVOLVIMENTO = {"MF", "SO", "IA", "ES2", "TCC", "CG", "FR"}   # os sete cursos com gold e régua (campanhas do motor)

CANDIDATOS = [
    {"sigla": "MF", "nome": "Métodos Formais para Computação", "fonte": MOODLE / "metodos-formais-para-computacao",
     "tutor": "Metodos-Formais-Tutor", "padrao": r"Metodos-Formais|M[ée]todos Formais"},
    {"sigla": "SO", "nome": "Sistemas Operacionais", "fonte": MOODLE / "sistemas-operacionais",
     "tutor": "Sistemas-Operacionais-Tutor", "padrao": r"Sistemas-Operacionais-Tutor"},
    {"sigla": "IA", "nome": "Inteligência Artificial", "fonte": MOODLE / "inteligencia-artificial",
     "tutor": "Inteligencia-Artifical-Tutor", "padrao": r"Inteligencia-Artifical"},
    {"sigla": "ES2", "nome": "Engenharia de Software II", "fonte": MOODLE / "engenharia-de-software-ii",
     "tutor": "Engenharia-Software-2-Tutor", "padrao": r"Engenharia-Software-2"},
    {"sigla": "TCC", "nome": "Teoria da Computabilidade e Complexidade", "fonte": MOODLE / "teoria-da-computabilidade-e-complexidade",
     "tutor": "TCC-Tutor", "padrao": r"TCC-Tutor"},
    {"sigla": "CG", "nome": "Computação Gráfica", "fonte": MOODLE / "computacao-grafica",
     "tutor": "Computacao-Grafica-Tutor", "padrao": r"Computacao-Grafica"},
    {"sigla": "FR", "nome": "Fundamentos de Redes de Computadores", "fonte": MOODLE / "fundamentos-de-redes-de-computadores",
     "tutor": "Fundamentos-de-Redes-Tutor", "padrao": r"Fundamentos-de-Redes"},
    {"sigla": "LR", "nome": "Laboratório de Redes de Computadores", "fonte": MOODLE / "laboratorio-de-redes-de-computadores",
     "tutor": "Laboratorio-de-Redes-Tutor", "padrao": r"Laboratorio-de-Redes|Lab(oratório)? (de )?Redes|\bLR\b"},
    {"sigla": "LSO", "nome": "Laboratório de Sistemas Operacionais", "fonte": MOODLE / "laboratorio-de-sistemas-operacionais",
     "plano_externo": HOME / "Desktop/claude-tutor/lab-so.pdf",
     "padrao": r"laboratorio-de-sistemas-operacionais|Laborat[oó]rio de Sistemas Operacionais|\blab-so\b|\bLab SO\b|95227|4646I"},
    {"sigla": "UX", "nome": "Experiência do Usuário", "fonte": MOODLE / "experiencia-do-usuario",
     "padrao": r"experiencia-do-usuario|Experi[eê]ncia do Usu[aá]rio|\bIHC\b|92619"},
    {"sigla": "CALC1", "nome": "Cálculo 1 (pasta do aluno)", "fonte": HOME / "OneDrive/Aulas-PUCRS/Calculo 1",
     "padrao": r"C[aá]lculo[ -]?1\b"},
    {"sigla": "FP", "nome": "Fundamentos da Programação (pasta do aluno)", "fonte": HOME / "OneDrive/Aulas-PUCRS/Fundamentos-da-Programacao",
     "padrao": r"Fundamentos[- ]da[- ]Programa[cç][aã]o"},
    {"sigla": "IC", "nome": "Introdução à Computação (pasta do aluno)", "fonte": HOME / "OneDrive/Aulas-PUCRS/Introdução a Computação",
     "padrao": r"Introdu[cç][aã]o [àa] Computa[cç][aã]o"},
    {"sigla": "MD", "nome": "Matemática Discreta (pasta do aluno)", "fonte": HOME / "OneDrive/Aulas-PUCRS/Matemática Discreta",
     "padrao": r"Matem[aá]tica Discreta"},
    {"sigla": "MC", "nome": "Metodologia Científica (pasta do aluno)", "fonte": HOME / "OneDrive/Aulas-PUCRS/Metodologia Cientifica",
     "padrao": r"Metodologia Cient[ií]fica"},
    {"sigla": "MSA", "nome": "Modelagem, Simulação e Métodos Analíticos (projeto do aluno)", "fonte": HOME / "Desktop/MetodosAnaliticos",
     "padrao": r"M[ée]todos Anal[ií]ticos|MetodosAnaliticos|Filas em Tandem"},
]
# Evidência de exposição: texto do repositório no commit FIXO anterior a esta preparação (a cópia de trabalho seria
# contaminada pelos próprios documentos da preparação). git grep/log com PCRE; binários e benchmarks ignorados.
BASE_EVIDENCIA = "bf46d51fc80d1e7dcc62c08cccd0399c056bcbe1"
EVIDENCIA_RAIZES = ["docs", "tests", "src", "scripts", ".mex", ".workflow"]
EVIDENCIA_EXCLUI = re.compile(r"_codegraph-benchmark|graphify-out|__pycache__|\.(exe|zip|pyc|png|jpg|pdf)$")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def estrutura(fonte):
    """Contagens estruturais da fonte bruta. Nenhum campo computado do produto é lido."""
    if not fonte.is_dir():
        return {"existe": False}
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
    paginas_locais = sum(1 for r in materiais if r.startswith("raw/moodle/pages/"))
    entries = len(materiais) + urls
    meta = [r for r in materiais if META.search(Path(r).name)]
    adjudicaveis = entries - len(meta)
    local = len(materiais) - len(meta)
    return {"existe": True, "arquivos_total": len(arquivos), "materiais_unicos_por_hash": len(materiais),
            "extensoes": dict(sorted(ext.items())), "modulos_moodle": dict(sorted(modulos.items())),
            "links_moodle": urls, "paginas_moodle_locais": paginas_locais, "entries_brutas": entries,
            "meta_por_nome": len(meta), "potencialmente_adjudicaveis": adjudicaveis,
            "fracao_com_fonte_local": round(local / adjudicaveis, 3) if adjudicaveis else 0.0}


def plano(c, est):
    if c.get("plano_externo"):
        p = c["plano_externo"]
        return {"disponivel": p.is_file(), "arquivo": str(p).replace(str(HOME), "~"), "sha256": sha(p) if p.is_file() else None}
    fonte = c["fonte"]
    cands = sorted(p for p in fonte.rglob("*") if p.is_file() and re.search(r"plano", p.name, re.I)
                   and p.suffix.lower() in {".pdf", ".docx", ".doc", ".md", ".html"}) if fonte.is_dir() else []
    return {"disponivel": bool(cands), "arquivo": str(cands[0]).replace(str(HOME), "~") if cands else None,
            "sha256": sha(cands[0]) if cands else None}


def exposicao(c):
    saida = git("grep", "-P", "-i", "-l", c["padrao"], BASE_EVIDENCIA, "--", *EVIDENCIA_RAIZES)
    hits = sorted({ln.split(":", 1)[1] for ln in saida.splitlines() if ":" in ln and not EVIDENCIA_EXCLUI.search(ln)})
    dev = [h for h in hits if re.match(r"(src|tests)/", h) or re.match(r"docs/(plans|specs)/", h)]
    tutor = (GITHUB / c["tutor"]).is_dir() if c.get("tutor") else False
    arvore = git("ls-tree", "-r", "--name-only", BASE_EVIDENCIA, "--", "docs/reports", "tests/fixtures").splitlines()
    gold = sorted(p for p in arvore if re.search(rf"(ground_truth|material_gt|subunit_gt|coverage_gt|gold_units)_{re.escape(c['sigla'])}\.csv$", p))
    log = git("log", BASE_EVIDENCIA, "--oneline", "-i", "--perl-regexp", f"--grep={c['padrao']}").splitlines()
    if c["sigla"] in DESENVOLVIMENTO:
        nivel = "N3"
    elif tutor:
        nivel = "N2"
    elif hits or log:
        nivel = "N1"
    else:
        nivel = "N0"
    return {"nivel": nivel, "tutor_construido": tutor, "gold": gold, "mencoes_repo": len(hits),
            "mencoes_desenvolvimento_src_tests_planos": len(dev), "exemplos": hits[:6], "commits": log[:4]}


def main():
    linhas = []
    for c in CANDIDATOS:
        est = estrutura(c["fonte"])
        pl = plano(c, est)
        ex = exposicao(c)
        e2 = pl["disponivel"]
        e3 = est.get("potencialmente_adjudicaveis", 0) >= MIN_ADJUDICAVEIS_CURSO
        e4 = est.get("fracao_com_fonte_local", 0.0) >= MIN_FRACAO_LOCAL
        if ex["nivel"] == "N3":
            pop, motivo = "excluido", "desenvolvimento: gold visto e usado nas campanhas do motor"
        elif ex["nivel"] == "N2":
            pop, motivo = "smoke", "tutor construído e processado pelo motor; fora da população principal"
        elif not (e2 and e3 and e4):
            falta = [n for n, ok in (("plano", e2), (f">= {MIN_ADJUDICAVEIS_CURSO} adjudicáveis", e3),
                                     (f">= {int(MIN_FRACAO_LOCAL * 100)}% com fonte local", e4)) if not ok]
            pop, motivo = "inelegivel", "falta: " + ", ".join(falta)
        elif ex["nivel"] == "N1":
            pop, motivo = "piloto", "exposição estrutural no desenvolvimento do motor; nunca teve atribuição, gold ou vocabulário"
        else:
            pop, motivo = "geral", "nenhuma exposição encontrada"
        linhas.append({"sigla": c["sigla"], "nome": c["nome"], "fonte": str(c["fonte"]).replace(str(HOME), "~"),
                       "estrutura": est, "plano": pl, "exposicao": ex, "E2_plano": e2, "E3_tamanho": e3, "E4_fonte_local": e4,
                       "populacao": pop, "motivo": motivo,
                       "ordem_deterministica": hashlib.sha256(f"{SAL}|{c['sigla']}".encode()).hexdigest()})

    def seleciona(pop):
        elegiveis = sorted((x for x in linhas if x["populacao"] == pop), key=lambda x: x["ordem_deterministica"])
        return [x["sigla"] for x in elegiveis[:K_MAX]], [x["sigla"] for x in elegiveis[K_MAX:]]

    geral, geral_fora = seleciona("geral")
    piloto, piloto_fora = seleciona("piloto")
    n_geral = sum(x["estrutura"].get("potencialmente_adjudicaveis", 0) for x in linhas if x["sigla"] in geral)
    out = {"regra": {"sal": SAL, "K_MAX": K_MAX, "MIN_CURSOS_GERAL": MIN_CURSOS_GERAL, "MIN_ADJUDICAVEIS_GERAL": MIN_ADJUDICAVEIS_GERAL,
                     "MIN_ADJUDICAVEIS_CURSO": MIN_ADJUDICAVEIS_CURSO, "MIN_FRACAO_LOCAL": MIN_FRACAO_LOCAL,
                     "script_sha256": sha(Path(__file__)), "base_evidencia": BASE_EVIDENCIA},
           "candidatos": linhas,
           "proposta": {"generalizacao": geral, "generalizacao_fora_do_orcamento": geral_fora, "piloto_externo": piloto,
                        "piloto_fora_do_orcamento": piloto_fora, "smoke_descritivo": [x["sigla"] for x in linhas if x["populacao"] == "smoke"],
                        "adjudicaveis_generalizacao": n_geral,
                        "minimo_generalizacao_atingido": len(geral) >= MIN_CURSOS_GERAL and n_geral >= MIN_ADJUDICAVEIS_GERAL}}
    (AQUI / "populacao_candidata.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = ["# População candidata (gerado por enumera_candidatos.py; não editar à mão)", "",
          "| curso candidato | nível | realmente novo? | usado em campanha anterior? | plano disponível? | entries brutas | "
          "potencialmente adjudicáveis | elegível? | motivo |", "|---|---|---|---|---|---:|---:|---|---|"]
    for x in linhas:
        ex, est = x["exposicao"], x["estrutura"]
        novo = {"N0": "sim", "N1": "parcial", "N2": "não", "N3": "não"}[ex["nivel"]]
        usado = ("sim (gold)" if ex["nivel"] == "N3" else "sim (tutor)" if ex["nivel"] == "N2"
                 else f"estrutura ({ex['mencoes_repo']} menções)" if ex["nivel"] == "N1" else "não encontrado")
        eleg = {"geral": "sim (generalização)", "piloto": "só piloto externo", "smoke": "fora; no máximo smoke test descritivo",
                "excluido": "não", "inelegivel": "não"}[x["populacao"]]
        md.append(f"| {x['sigla']} — {x['nome']} | {ex['nivel']} | {novo} | {usado} | {'sim' if x['plano']['disponivel'] else 'não'} | "
                  f"{est.get('entries_brutas', 0)} | {est.get('potencialmente_adjudicaveis', 0)} | {eleg} | {x['motivo']} |")
    p = out["proposta"]
    md += ["", f"- Generalização: {p['generalizacao'] or 'nenhum'} ({p['adjudicaveis_generalizacao']} adjudicáveis); "
               f"mínimo atingido: {p['minimo_generalizacao_atingido']}.",
           f"- Piloto externo: {p['piloto_externo'] or 'nenhum'}.", f"- Smoke descritivo: {p['smoke_descritivo'] or 'nenhum'}."]
    (AQUI / "populacao_candidata.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
