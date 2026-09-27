"""Gate de avaliação W-AD5 (26/09), etapa 1: validação dos artefatos ANTES de abrir a régua. Não lê gold.

Roda no ambiente controlado (comum.ambiente_controlado, -B). Só leitura. Saída 0 = tudo confere; 1 = parar.
"""
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PACOTE = AQUI.parent / "wad5_25-09"
sys.path.insert(0, str(PACOTE))
import captura as CP  # noqa: E402  (só stdlib no import; não importa src/)
import comum as K  # noqa: E402

ESPERADO = {"id_comum": "3fe5d1ff97258644b3148860cbe235aa3e16acfac91e9a291ea3c3e63a8e355d",
            "avaliador.py": "aeac2996d96fd2085f7add91cfe20bc9c675bdd23ad0e144cdadd0f796978017",
            "comum.py": "04a535b678bfe6610701f0db91c43641c027275ea48fb1a111f4ef595e2a7e49"}
ok, info = {}, {}


def marca(nome, cond, detalhe=None):
    ok[nome] = bool(cond)
    if detalhe is not None:
        info[nome] = detalhe
    print(("OK    " if cond else "FALHA ") + nome + (f"  {detalhe}" if detalhe is not None and not cond else ""), flush=True)


info["interprete"] = {"executavel": sys.executable, "versao": sys.version, "flags_B": sys.flags.dont_write_bytecode,
                      "no_user_site": sys.flags.no_user_site, "pycache_prefix": sys.pycache_prefix}
info["ambiente"] = K.descritor_ambiente(__import__("os").environ)
marca("ambiente declarado", not K.verifica_ambiente(__import__("os").environ), K.verifica_ambiente(__import__("os").environ))

# código aprovado
for n in ("avaliador.py", "comum.py"):
    marca(f"{n} = hash aprovado", K.sha_arq(PACOTE / n) == ESPERADO[n], K.sha_arq(PACOTE / n))

# congelamento
cong = K.carrega_json_estrito(CP.CONG)
marca("congelamento: id_comum = aprovado", cong["id_comum"] == ESPERADO["id_comum"], cong["id_comum"])
marca("congelamento: ligações normativo→id e insumos→insumos_braco", not K.valida_congelamento(cong), K.valida_congelamento(cong))
marca("código do pacote = congelado (inclui avaliador, comum, testes, helpers)",
      not K.verifica_codigo(cong["normativo"]["codigo"], CP.CODIGO), K.verifica_codigo(cong["normativo"]["codigo"], CP.CODIGO))
marca("intérprete = congelado", sys.executable == cong["normativo"]["interprete"]["executavel"]
      and sys.version == cong["normativo"]["interprete"]["versao"])
marca("distribuições = assinatura congelada", not CP.verifica_distribuicoes(cong), CP.verifica_distribuicoes(cong))
entradas = K.carrega_json_estrito(CP.CONG_ENTRADAS)
marca("congelamento de entradas = normativo", K.sha_json(entradas) == cong["normativo"]["entradas_arquivo_sha"])
marca("protocolo normativo (adendo v4) = protocolo_sha",
      K.sha_bytes(CP.normativo_protocolo().encode("utf-8")) == cong["normativo"]["protocolo_sha"])

# as sete capturas (caminhos explícitos do manifesto)
man = K.carrega_json_estrito(PACOTE / "manifesto_capturas_v5.json")
marca("manifesto de capturas aprovado e do mesmo congelamento", man["aprovado"] is True and man["congelamento_id_comum"] == cong["id_comum"])
marca("manifesto com os sete braços", set(man["capturas"]) == set(K.BRACOS), sorted(man["capturas"]))
caps = {}
for b in K.BRACOS:
    c = man["capturas"][b]
    p = CP.DATA / c["arquivo"]
    esperado_nome = f"capturar_{b}_{cong['id_comum'][:16]}_{cong['insumos_braco'][b][:16]}.json"
    cap = K.carrega_json_estrito(p)
    caps[b] = cap
    prob = K.valida_historica(cap, cong, braco=b)
    marca(f"{b}: arquivo = caminho esperado pelo avaliador", p.name == esperado_nome and p.parent == CP.CAPS)
    marca(f"{b}: sha256 do arquivo = manifesto", K.sha_arq(p) == c["sha256"])
    marca(f"{b}: conteudo_sha recalculado = manifesto", K.conteudo_sha(cap) == cap["conteudo_sha"] == c["conteudo_sha"])
    marca(f"{b}: validador completo", not prob, prob[:3])
    marca(f"{b}: identidade (braço, modo, esquema, id_comum, insumos, 0 violações)",
          cap["braco"] == b and cap["modo"] == "capturar" and cap["esquema"] == K.ESQUEMA_CAPTURA
          and cap["congelamento_comum"] == cong["id_comum"] and cap["insumos_braco"] == cong["insumos_braco"][b]
          and cap["violacoes"] == [] and cap["status"] == "concluida")
    marca(f"{b}: 350 registros = inventário congelado",
          sum(len(v) for v in cap["decisoes"].values()) == 350
          and {s: sorted(v) for s, v in cap["decisoes"].items()} == cong["normativo"]["inventario"])
capturar = sorted(x.name for x in CP.CAPS.glob("capturar_*.json"))
marca("diretório de capturas: exatamente sete capturas completas, todas deste congelamento",
      len(capturar) == 7 and all(f"_{cong['id_comum'][:16]}_" in x for x in capturar), capturar)
marca("sem falhas registradas no congelamento", not (CP.FALHAS.exists() and any(CP.FALHAS.iterdir())))

# snapshots e palcos locais (fora do ZIP) contra o congelamento
snap_ok = []
for b in K.BRACOS:
    for s in K.NOMES:
        ins = cong["insumos"][b][s]
        snap_ok.append(K.sha_arq(CP.SNAP / b / s / "taxonomia.json") == ins["taxonomia_arquivo_sha"]
                       and K.sha_arq(CP.SNAP / b / s / "indice_unidade.json") == ins["indice_arquivo_sha"]
                       and CP.arquivos_do_palco(b, s) == ins["palco"])
marca("snapshots de taxonomia e índice + palcos locais = congelamento (7 braços x 7 cursos)", all(snap_ok) and len(snap_ok) == 49)

# insumos da avaliação que não são régua
desc = cong["normativo"]["avaliacao"]
marca("descritor da régua sem pendências", desc["pendencias"] == [], desc["pendencias"])
for s, m in desc["manifestos_referencia"].items():
    marca(f"{s}: manifest de referência = sha256 congelado", K.sha_arq(CP.DATA / m["caminho"]) == m["sha256"])
for s, e in cong["normativo"]["entradas_comuns"].items():
    marca(f"{s}: manifest salvo = árvore congelada", K.sha_arq(CP.DATA / e["raiz"] / "manifest.json") == entradas[s]["manifest.json"])

# blobs da régua no índice do git (sem abrir os arquivos): ainda os congelados
caminhos = sorted({it["caminho"] for papel in desc["arquivos"].values() for it in papel.values()})
r = subprocess.run(["git", "ls-files", "-s", "--", *caminhos], cwd=CP.DATA, capture_output=True, text=True, encoding="utf-8")
blobs = {ln.split("\t", 1)[1]: ln.split()[1] for ln in r.stdout.splitlines()}
div = [c for papel in desc["arquivos"].values() for c in [it for it in papel.values()] if blobs.get(c["caminho"]) != c["blob_git"]]
marca(f"régua: {len(caminhos)} arquivos com blob do índice = congelado (arquivos não abertos)", r.returncode == 0 and not div,
      [d["caminho"] for d in div])

info["capturas"] = {b: {"arquivo": man["capturas"][b]["arquivo"], "sha256": man["capturas"][b]["sha256"],
                        "conteudo_sha": man["capturas"][b]["conteudo_sha"]} for b in K.BRACOS}
res = {"etapa": "validação pré-régua (sem gold)", "aprovado": all(ok.values()), "condicoes": ok, "info": info}
K.grava_atomico(AQUI / "validacao_pre_regua.json", res)
print("PRE-REGUA", "APROVADA" if res["aprovado"] else "REPROVADA", flush=True)
sys.exit(0 if res["aprovado"] else 1)
