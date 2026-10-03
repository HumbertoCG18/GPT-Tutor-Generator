"""Verificação da rodada v5 (R-META e R-PAGE), cada versão em processo próprio. Sem rede; transporte falso.

1. vermelho: testes v5 contra o código v4 (cópia espelhada em c1-3/_replay_vermelho_v5_tmp, removida);
2. verde: pastas v5 (testes novos e herdados);
3. produto: `tests/test_moodle.py` e a suíte completa `tests` (a alteração em src/);
4. regressão: pastas v4, etapa 3 e etapa 2, sem alteração;
5. os 5 casos anteriores contra v5 (subprocesso, com o executor da v4);
6. grava logs/ e reprodutores_v5_etapa3.json (não sobrescreve nada anterior).
O vermelho do src (antes da alteração) está em logs/vermelho_src_test_moodle.txt, gravado antes de mudar o arquivo.
Uso: python roda_verificacao_v5.py
"""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
C13 = AQUI.parent
REPO = next(p for p in AQUI.parents if (p / ".git").exists())
V4 = C13 / "validacao_externa_etapa3_correcoes_29-09"
E2, E3 = C13 / "validacao_externa_etapa2_29-09", C13 / "validacao_externa_etapa3_29-09"
LOGS = AQUI / "logs"
_spec = importlib.util.spec_from_file_location("runner_v4", V4 / "roda_verificacao.py")
R4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R4)   # só pytest(), junit() e o caso anterior
AREAS = [("correcoes/aquisicao", "adquire.py", "test_adquire_v5.py"), ("correcoes/pacote_cego", "gera_pacote_cego.py", "test_pacote_cego_v5.py")]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def vermelho_e_verde():
    tmp = C13 / "_replay_vermelho_v5_tmp"
    if tmp.exists():
        sys.exit(f"{tmp} já existe: não sobrescrevo")
    out = {}
    try:
        for area, codigo, _ in AREAS:
            d = tmp / area
            d.mkdir(parents=True)
            shutil.copy2(V4 / area / codigo, d / codigo)
            for t in (AQUI / area).glob("test_*.py"):
                shutil.copy2(t, d / t.name)
        for area, codigo, teste in AREAS:
            nome = Path(area).name
            out[nome] = {"v4_sha256": sha(V4 / area / codigo), "v5_sha256": sha(AQUI / area / codigo),
                         "vermelho": R4.pytest(tmp, f"{area}/{teste}", LOGS / f"junit_vermelho_v5_{nome}.xml", LOGS / f"vermelho_final_v5_{nome}.txt")}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for area, _, teste in AREAS:
        nome = Path(area).name
        out[nome]["verde_novos"] = R4.pytest(AQUI / area, teste, LOGS / f"junit_verde_v5_{nome}.xml", LOGS / f"verde_novos_v5_{nome}.txt")
        out[nome]["verde_pasta"] = R4.pytest(AQUI / area, ".", LOGS / f"junit_verde_pasta_v5_{nome}.xml", LOGS / f"verde_pasta_v5_{nome}.txt")
    return out


def produto():
    return {"src_sha256": sha(REPO / "src/builder/sources/moodle.py"),
            "test_moodle": R4.pytest(REPO, "tests/test_moodle.py", LOGS / "junit_produto_test_moodle.xml", LOGS / "verde_src_test_moodle_final.txt"),
            "suite_completa": R4.pytest(REPO, "tests", LOGS / "junit_produto_suite.xml", LOGS / "produto_suite_depois_final.txt")}


def regressao():
    alvos = {"v4_pacote_cego": (V4, "correcoes/pacote_cego"), "v4_aquisicao": (V4, "correcoes/aquisicao"),
             "v4_exposicao": (V4, "exposicao"), "v4_conferencia": (V4, "conferencia"),
             "etapa3_pacote_cego": (E3, "correcoes/pacote_cego"), "etapa3_aquisicao": (E3, "correcoes/aquisicao"),
             "etapa3_exposicao": (E3, "exposicao"), "etapa2_correcoes": (E2, "correcoes")}
    return {k: R4.pytest(cwd, alvo, LOGS / f"junit_regressao_v5_{k}.xml", LOGS / f"regressao_v5_{k}.txt") for k, (cwd, alvo) in alvos.items()}


CASO_V5 = """
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("runner_v4", sys.argv[1]); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
R.VERSOES["v5"] = (sys.argv[2], sys.argv[3])
R.Cliente.bytes_recebidos, R.Cliente.limite_bytes = 0, None   # interface de contagem do MoodleClient (falso: 0 bytes)
print(json.dumps(R.casos_anteriores("v5"), ensure_ascii=False, default=str))
"""


def casos_anteriores_v5():
    r = subprocess.run([sys.executable, "-B", "-c", CASO_V5, str(V4 / "roda_verificacao.py"),
                        str(AQUI / "correcoes/pacote_cego/gera_pacote_cego.py"), str(AQUI / "correcoes/aquisicao/adquire.py")],
                       capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout) if r.returncode == 0 else {"erro": r.stderr[-600:]}


def main():
    destino = AQUI / "reprodutores_v5_etapa3.json"
    if destino.exists():
        sys.exit(f"{destino.name} já existe: não sobrescrevo")
    LOGS.mkdir(exist_ok=True)
    execucao = vermelho_e_verde()
    prod = produto()
    reg = regressao()
    casos = []
    for area, _, _ in AREAS:
        nome = Path(area).name
        antes, depois = R4.junit(LOGS / f"junit_vermelho_v5_{nome}.xml"), R4.junit(LOGS / f"junit_verde_v5_{nome}.xml")
        casos += [{"area": nome, "teste": t, "v4": antes.get(t, "ausente"), "v5": depois[t]} for t in sorted(depois)]
    out = {"esquema": "reprodutores-v5-etapa3-1", "autorizacao": "Gate 1 parcial de 29/09: R-META (inclusive src/) e R-PAGE",
           "restricoes": {"rede": False, "gold": False, "adjudicacao": False, "motor": False, "build_replay": False,
                          "aquisicao_real": False, "P3_P31_aplicada": False, "elegibilidade": False, "R_VIS_implementada": False},
           "definicao_orcamento": "bytes dos corpos HTTP lidos pela aplicação (webservice e downloads); não é todo o tráfego de rede",
           "vermelho_src": "logs/vermelho_src_test_moodle.txt (10 falhas antes da alteração; 44 existentes verdes)",
           "linha_de_base_produto": "logs/produto_suite_antes_linha_de_base.txt",
           "execucao": execucao, "produto": prod, "regressao": reg, "casos_anteriores_v5": casos_anteriores_v5(), "casos": casos}
    destino.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"execucao": execucao, "produto": prod, "regressao": reg}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
