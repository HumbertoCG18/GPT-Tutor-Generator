"""Gate de avaliação VOCAB_LIMPO (26/09): raiz-espelho ENDEREÇADA POR CONTEÚDO para o avaliador congelado da rodada.

Mesmo procedimento aprovado na Fase 1 (../wad5_avaliacao_26-09/monta_espelho.py), só com os caminhos da rodada:
- régua: bytes de `git cat-file blob <blob congelado>` (descritor do congelamento 6a0f9652…), blob conferido;
- manifests de referência e salvos: cópia byte a byte com sha256 conferido contra o congelamento;
- avaliador.py e comum.py DA RODADA: cópia byte a byte conferida contra o manifesto da rodada e o congelamento.
Depois de gravar, TODO arquivo do espelho é relido do disco e reconferido (blob/sha256) e o conjunto de arquivos tem de
ser exatamente o previsto. Nenhum EOL é normalizado; nada é buscado em versão alternativa; divergência interrompe.
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
DATA = AQUI.parents[4]
PACOTE = AQUI.parent / "vocab_limpo_26-09"
sys.path.insert(0, str(PACOTE))
import comum as K  # noqa: E402

ESPELHO = DATA / ".frzero/vocab_limpo_avaliacao_26-09/espelho"
CONG = DATA / ".frzero/vocab_limpo_26-09/captura/congelamento.json"
ID_COMUM = "6a0f9652fb8cfaffde15cd9d113705536c7fcc5f9b303474a74438ceee8c0e81"


def exige(cond, msg):
    if not cond:
        raise K.ErroIntegridade(msg)


def grava(rel, dados):
    destino = ESPELHO / rel
    if destino.exists():   # mesmo caminho em dois papéis (manifest salvo = de referência em SO/ES2/TCC/FR): só se idêntico
        exige(destino.read_bytes() == dados, f"espelho já contém {rel} com outros bytes: não sobrescrevo")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(dados)


exige(not ESPELHO.exists(), f"espelho já existe: {ESPELHO}")
cong = K.carrega_json_estrito(CONG)
exige(cong["id_comum"] == ID_COMUM, "congelamento inesperado")
exige(not K.valida_congelamento(cong), "congelamento malformado")
entradas = K.carrega_json_estrito(CONG.parent / "congelamento_entradas.json")
exige(K.sha_json(entradas) == cong["normativo"]["entradas_arquivo_sha"], "entradas divergentes")
desc = cong["normativo"]["avaliacao"]
exige(desc["pendencias"] == [], "descritor da régua com pendências")
mr = K.carrega_json_estrito(PACOTE / "manifesto_rodada_vl.json")
manifesto = {"espelho": str(ESPELHO), "congelamento_id_comum": cong["id_comum"], "codigo": {}, "regua": {},
             "manifestos_referencia": {}, "manifestos_salvos": {}}
previsto = {}   # caminho relativo -> ("blob", id) | ("sha256", hash)

rel_pacote = PACOTE.relative_to(DATA).as_posix()
for n in ("avaliador.py", "comum.py"):
    dados = (PACOTE / n).read_bytes()
    h = K.sha_bytes(dados)
    exige(h == cong["normativo"]["codigo"][n] == mr["pacote"][f"{rel_pacote}/{n}"], f"{n}: hash != congelado/manifesto")
    grava(f"{rel_pacote}/{n}", dados)
    manifesto["codigo"][n] = h
    previsto[f"{rel_pacote}/{n}"] = ("sha256", h)

for papel, m in desc["arquivos"].items():
    for s, it in m.items():
        r = subprocess.run(["git", "cat-file", "blob", it["blob_git"]], cwd=DATA, capture_output=True)
        exige(r.returncode == 0, f"{it['caminho']}: blob {it['blob_git']} ausente no object store")
        exige(K.blob_git(r.stdout) == it["blob_git"], f"{it['caminho']}: bytes do object store != blob")
        grava(it["caminho"], r.stdout)
        manifesto["regua"][it["caminho"]] = {"blob_git": it["blob_git"], "sha256": K.sha_bytes(r.stdout), "bytes": len(r.stdout)}
        exige(previsto.get(it["caminho"], ("blob", it["blob_git"])) == ("blob", it["blob_git"]), f"{it['caminho']}: dois blobs")
        previsto[it["caminho"]] = ("blob", it["blob_git"])

for s, it in desc["manifestos_referencia"].items():
    dados = (DATA / it["caminho"]).read_bytes()
    exige(K.sha_bytes(dados) == it["sha256"], f"{it['caminho']}: sha256 != congelado")
    grava(it["caminho"], dados)
    manifesto["manifestos_referencia"][it["caminho"]] = it["sha256"]
    previsto[it["caminho"]] = ("sha256", it["sha256"])

for s, e in cong["normativo"]["entradas_comuns"].items():
    rel = f"{e['raiz']}/manifest.json"
    dados = (DATA / rel).read_bytes()
    exige(K.sha_bytes(dados) == entradas[s]["manifest.json"], f"{rel}: sha256 != árvore congelada")
    exige(previsto.get(rel, ("sha256", entradas[s]["manifest.json"])) == ("sha256", entradas[s]["manifest.json"]),
          f"{rel}: salvo e de referência com hashes diferentes")
    grava(rel, dados)
    manifesto["manifestos_salvos"][rel] = entradas[s]["manifest.json"]
    previsto[rel] = ("sha256", entradas[s]["manifest.json"])

# reconferência dos bytes GRAVADOS e do conjunto exato de arquivos, antes de qualquer interpretação
no_disco = {p.relative_to(ESPELHO).as_posix() for p in ESPELHO.rglob("*") if p.is_file()}
exige(no_disco == set(previsto), f"espelho com arquivos inesperados/faltando: {sorted(no_disco ^ set(previsto))[:5]}")
for rel, (tipo, h) in previsto.items():
    dados = (ESPELHO / rel).read_bytes()
    exige((K.blob_git(dados) if tipo == "blob" else K.sha_bytes(dados)) == h, f"{rel}: bytes gravados != {tipo} congelado")
manifesto["reconferencia"] = {"arquivos": len(previsto), "conjunto_exato": True, "bytes_gravados_conferidos": True}
fase1 = DATA / "docs/reports/_harness-2026-09-04/c1-3/wad5_avaliacao_26-09/espelho_manifesto.json"
manifesto["mesmos_blobs_da_fase1"] = ({c: v["blob_git"] for c, v in K.carrega_json_estrito(fase1)["regua"].items()}
                                      == {c: v["blob_git"] for c, v in manifesto["regua"].items()})
K.grava_atomico(AQUI / "espelho_manifesto_vl.json", manifesto)
print(f"espelho montado: {len(manifesto['regua'])} arquivos de régua (blob conferido), "
      f"{len(manifesto['manifestos_referencia'])} manifests de referência, {len(manifesto['manifestos_salvos'])} salvos, "
      f"avaliador e comum da rodada byte-idênticos; {len(previsto)} arquivos relidos e reconferidos; "
      f"mesmos blobs da Fase 1: {manifesto['mesmos_blobs_da_fase1']}")
