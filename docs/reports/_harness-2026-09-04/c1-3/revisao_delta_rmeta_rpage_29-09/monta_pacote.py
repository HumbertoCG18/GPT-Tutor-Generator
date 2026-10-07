"""Congela o pacote de revisão do delta R-META/R-PAGE: lista explícita, manifesto com sha256 e ZIP novo (não sobrescreve).
Uso: python monta_pacote.py"""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = next(p for p in AQUI.parents if (p / ".git").exists())
C13 = "docs/reports/_harness-2026-09-04/c1-3"
V4, V5 = f"{C13}/validacao_externa_etapa3_correcoes_29-09", f"{C13}/validacao_externa_etapa3_correcoes_v5_29-09"
ZIP = Path(r"C:/Users/Humberto/Desktop/para-gpt/revisao_delta_rmeta_rpage_29-09.zip")
INCLUIDOS = [
    # commit técnico proposto
    "src/builder/sources/moodle.py", "tests/test_moodle.py",
    # ferramentas experimentais v5 e testes pertinentes
    *[f"{V5}/correcoes/aquisicao/{n}" for n in ("adquire.py", "test_adquire_v3.py", "test_adquire_v4.py", "test_adquire_v5.py")],
    *[f"{V5}/correcoes/pacote_cego/{n}" for n in ("gera_pacote_cego.py", "test_pacote_cego.py", "test_pacote_cego_v2.py",
                                                   "test_pacote_cego_v3.py", "test_pacote_cego_v4.py", "test_pacote_cego_v5.py")],
    f"{V5}/roda_verificacao_v5.py",
    # diffs, resultados, manifesto da pasta
    *[f"{V5}/diffs/{n}" for n in ("diff_src_moodle.patch", "diff_tests_test_moodle.patch", "diff_adquire_v4_v5.patch",
                                   "diff_gerador_v4_v5.patch", "diff_testes_herdados_v4_v5.patch", "diff_adquire_v5_catalogo.patch",
                                   "diff_test_adquire_v5_catalogo.patch")],
    f"{V5}/reprodutores_v5_etapa3.json", f"{V5}/reprodutores_v5_catalogo_etapa3.json", f"{V5}/manifesto_correcoes_v5_etapa3.json",
    # logs de texto (JUnit fica fora: redundante com os JSON e com caminhos absolutos locais)
    *sorted(p.relative_to(REPO).as_posix() for p in (REPO / V5 / "logs").glob("*.txt")),
    # documentos (redigidos; nenhum original com texto excedente)
    f"{V4}/relatorio_correcoes_etapa3.md", f"{V4}/issue_correcoes_etapa3.md",
    f"{C13}/revisao_delta_rmeta_rpage_29-09/ESCOPO_REVISAO.md", f"{C13}/revisao_delta_rmeta_rpage_29-09/monta_pacote.py",
]
BASELINES = [   # não incluídos: identificados por caminho e hash
    f"{V4}/correcoes/aquisicao/adquire.py", f"{V4}/correcoes/pacote_cego/gera_pacote_cego.py", f"{V4}/roda_verificacao.py",
    f"{V4}/manifesto_correcoes_etapa3.json",
    f"{C13}/validacao_externa_etapa2_29-09/aquisicao/manifesto_aquisicao.json",
    f"{C13}/validacao_externa_etapa2_29-09/correcoes/populacao/enumera_candidatos.py",
    f"{C13}/validacao_externa_etapa2_29-09/correcoes/populacao/candidatos_29-09.json",
    f"{C13}/validacao_externa_29-09/gold/instrucoes_adjudicador.md",
    "src/builder/extraction/content_taxonomy.py", "src/builder/extraction/teaching_plan.py",
]
ENTREGAS_ANTERIORES = [r"C:/Users/Humberto/Desktop/para-gpt/validacao_externa_etapa3_29-09.zip",
                       r"C:/Users/Humberto/Desktop/para-gpt/validacao_externa_etapa3_correcoes_29-09.zip"]
EXCEDENTE = re.compile(r"\s+-\s+(?=Turmas?\b|\d{4}/\d|Modalidade\b|Profs?\b)")   # mesma regra da redação da etapa 3
CATALOGO = f"{C13}/validacao_externa_etapa2_29-09/aquisicao/catalogo.json"   # só lido: os excedentes não ficam no código


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, check=True).stdout


def main():
    if ZIP.exists():
        sys.exit(f"{ZIP} já existe: não sobrescrevo")
    head = git("rev-parse", "HEAD").decode().strip()
    cursos = json.loads((REPO / CATALOGO).read_text(encoding="utf-8"))["cursos"]
    excedentes = [EXCEDENTE.split(c["nome"], 1)[1] for c in cursos if EXCEDENTE.search(c["nome"])]
    assert excedentes, "regra de excedente não achou nada: conferência não seria significativa"
    incluidos = {}
    for rel in INCLUIDOS:
        dados = (REPO / rel).read_bytes()
        assert not any(x.encode() in dados or re.escape(x).encode() in dados for x in excedentes), f"texto excedente em {rel}"
        incluidos[rel] = sha_b(dados)
    man = {"esquema": "pacote-revisao-delta-1", "branch": git("rev-parse", "--abbrev-ref", "HEAD").decode().strip(), "head": head,
           "commit_proposto": {rel: {"sha256": incluidos[rel], "blob_git": git("hash-object", rel).decode().strip(),
                                     "baseline_head_sha256": sha_b(git("show", f"HEAD:{rel}")),
                                     "baseline_head_blob": git("rev-parse", f"HEAD:{rel}").decode().strip()}
                               for rel in ("src/builder/sources/moodle.py", "tests/test_moodle.py")},
           "incluidos": incluidos,
           "baselines_e_dependencias_nao_incluidos": {rel: sha_b((REPO / rel).read_bytes()) for rel in BASELINES},
           "entregas_anteriores_preservadas": {Path(z).name: sha_b(Path(z).read_bytes()) for z in ENTREGAS_ANTERIORES},
           "excluidos": {"JUnit XML": "redundante com os JSON de resultados; contém caminhos absolutos locais",
                         "exposicao_local*.json originais": "texto excedente; só cópias redigidas existem em outras entregas",
                         "fontes .frzero/": "material acadêmico", "credenciais": "nenhuma lida ou incluída"}}
    man_p = AQUI / "manifesto_pacote_revisao_delta.json"
    man_p.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    raiz = "revisao_delta_rmeta_rpage_29-09/"
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in INCLUIDOS:
            z.write(REPO / rel, raiz + rel)
        z.write(man_p, raiz + man_p.relative_to(REPO).as_posix())
    with zipfile.ZipFile(ZIP) as z:
        lido = {n[len(raiz):]: sha_b(z.read(n)) for n in z.namelist()}
    assert all(lido[k] == v for k, v in incluidos.items()) and len(lido) == len(incluidos) + 1
    print(len(lido), "entradas;", ZIP, sha_b(ZIP.read_bytes()))


if __name__ == "__main__":
    main()
