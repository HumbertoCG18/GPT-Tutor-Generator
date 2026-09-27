"""Gate de avaliação W-AD5 (26/09), correção autorizada: raiz-espelho ENDEREÇADA POR CONTEÚDO para o avaliador congelado.

Motivo (parada_avaliacao_26-09.md): a cópia de trabalho do Windows tem CRLF (core.autocrlf=true, * text=auto) e o blob
congelado é o conteúdo normalizado (LF); o avaliador compara bytes crus com o blob. O espelho reproduz os MESMOS
caminhos relativos com:
- régua: bytes de `git cat-file blob <blob congelado>` (exatamente o que o congelamento identifica), blob reconferido;
- manifests de referência e salvos: cópia byte a byte com sha256 conferido contra o congelamento;
- avaliador.py e comum.py: cópia byte a byte conferida contra os hashes aprovados (nenhuma linha muda).
Nada é inventado, ajustado ou buscado em versão alternativa: qualquer divergência interrompe.
"""
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DATA = AQUI.parents[4]
PACOTE = AQUI.parent / "wad5_25-09"
sys.path.insert(0, str(PACOTE))
import comum as K  # noqa: E402

ESPELHO = DATA / ".frzero/wad5_avaliacao_26-09/espelho"
APROVADO = {"avaliador.py": "aeac2996d96fd2085f7add91cfe20bc9c675bdd23ad0e144cdadd0f796978017",
            "comum.py": "04a535b678bfe6610701f0db91c43641c027275ea48fb1a111f4ef595e2a7e49"}


def exige(cond, msg):
    if not cond:
        raise K.ErroIntegridade(msg)


def grava(rel, dados):
    destino = ESPELHO / rel
    if destino.exists():   # mesmo caminho em dois papéis (manifest salvo = de referência em SO/ES2/TCC/FR): só se idêntico
        exige(destino.read_bytes() == dados, f"espelho já contém {rel} com outros bytes: não sobrescrevo")
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(dados)
    return destino


exige(not ESPELHO.exists(), f"espelho já existe: {ESPELHO}")
cong = K.carrega_json_estrito(DATA / ".frzero/wad5_25-09/congelamento.json")
exige(cong["id_comum"] == "3fe5d1ff97258644b3148860cbe235aa3e16acfac91e9a291ea3c3e63a8e355d", "congelamento inesperado")
exige(not K.valida_congelamento(cong), "congelamento malformado")
entradas = K.carrega_json_estrito(DATA / ".frzero/wad5_25-09/congelamento_entradas.json")
exige(K.sha_json(entradas) == cong["normativo"]["entradas_arquivo_sha"], "entradas divergentes")
desc = cong["normativo"]["avaliacao"]
exige(desc["pendencias"] == [], "descritor da régua com pendências")
manifesto = {"espelho": str(ESPELHO), "congelamento_id_comum": cong["id_comum"], "codigo": {}, "regua": {},
             "manifestos_referencia": {}, "manifestos_salvos": {}}

rel_pacote = PACOTE.relative_to(DATA).as_posix()
for n, h in APROVADO.items():
    dados = (PACOTE / n).read_bytes()
    exige(K.sha_bytes(dados) == h == cong["normativo"]["codigo"][n], f"{n}: hash != aprovado/congelado")
    grava(f"{rel_pacote}/{n}", dados)
    manifesto["codigo"][n] = h

for papel, m in desc["arquivos"].items():
    for s, it in m.items():
        r = subprocess.run(["git", "cat-file", "blob", it["blob_git"]], cwd=DATA, capture_output=True)
        exige(r.returncode == 0, f"{it['caminho']}: blob {it['blob_git']} ausente no object store")
        exige(K.blob_git(r.stdout) == it["blob_git"], f"{it['caminho']}: bytes do object store != blob")
        grava(it["caminho"], r.stdout)
        manifesto["regua"][it["caminho"]] = {"blob_git": it["blob_git"], "sha256": K.sha_bytes(r.stdout), "bytes": len(r.stdout)}

for s, it in desc["manifestos_referencia"].items():
    dados = (DATA / it["caminho"]).read_bytes()
    exige(K.sha_bytes(dados) == it["sha256"], f"{it['caminho']}: sha256 != congelado")
    grava(it["caminho"], dados)
    manifesto["manifestos_referencia"][it["caminho"]] = it["sha256"]

for s, e in cong["normativo"]["entradas_comuns"].items():
    rel = f"{e['raiz']}/manifest.json"
    dados = (DATA / rel).read_bytes()
    exige(K.sha_bytes(dados) == entradas[s]["manifest.json"], f"{rel}: sha256 != árvore congelada")
    grava(rel, dados)
    manifesto["manifestos_salvos"][rel] = entradas[s]["manifest.json"]

K.grava_atomico(AQUI / "espelho_manifesto.json", manifesto)
print(f"espelho montado: {len(manifesto['regua'])} arquivos de régua (blob conferido), "
      f"{len(manifesto['manifestos_referencia'])} manifests de referência, {len(manifesto['manifestos_salvos'])} salvos, "
      f"avaliador e comum byte-idênticos")
