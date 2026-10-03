"""Checagem barata de vínculo (PC24), READ-ONLY e sem rede: para cada registro `ok` do inventário da etapa 2, compara o
`filesize` que a API declarou no `contents.json` congelado (fonte independente do inventário) com o tamanho real do
arquivo em disco ligado a ele. Vínculo trocado entre arquivos de tamanhos diferentes aparece como divergência; com
tamanhos iguais a checagem não prova nada. Uso: python confere_tamanhos.py
"""
import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
REPO = next(p for p in AQUI.parents if (p / ".git").is_dir())
INV = AQUI.parents[1] / "validacao_externa_etapa2_29-09/aquisicao/inventario_downloads.json"
FONTES = REPO / ".frzero/validacao_externa_aquisicao_29-09"


def main():
    inv = json.loads(INV.read_text(encoding="utf-8"))
    out, total = {}, collections.Counter()
    for curso in inv["cursos"]:
        raiz = FONTES / curso["id"]
        declarado = collections.defaultdict(list)   # (módulo, arquivo) -> filesizes na ordem da API
        for sec in json.loads((raiz / "raw/moodle/contents.json").read_text(encoding="utf-8")):
            for mod in sec.get("modules") or []:
                for c in mod.get("contents") or []:
                    if c.get("type") == "file":
                        declarado[(str(mod.get("id")), str(c.get("filename")))].append(c.get("filesize"))
        vistos, r = collections.Counter(), {"iguais": 0, "sem_declaracao": [], "divergentes": []}
        for a in curso["arquivos"]:
            chave = (a["modulo_id"], a["arquivo"])
            k = vistos[chave]
            vistos[chave] += 1
            if a["status"] != "ok" or not a.get("caminho"):
                continue
            base = raiz if a.get("base", "curso") == "curso" else FONTES / f"{curso['id']}_anexos_de_pagina"
            real = (base / a["caminho"]).stat().st_size
            api = declarado[chave][k] if k < len(declarado[chave]) else None
            if not api:
                r["sem_declaracao"].append({"caminho": a["caminho"], "api": api, "real": real})
            elif api == real:
                r["iguais"] += 1
            else:
                r["divergentes"].append({"modulo_id": a["modulo_id"], "arquivo": a["arquivo"], "caminho": a["caminho"],
                                         "api": api, "real": real})
        out[curso["id"]] = r
        total.update(iguais=r["iguais"], sem_declaracao=len(r["sem_declaracao"]), divergentes=len(r["divergentes"]))
    resumo = {"registros_ok_conferidos": sum(total.values()), **total}
    (AQUI / "conferencia_tamanhos.json").write_text(json.dumps({"resumo": resumo, "cursos": out}, ensure_ascii=False, indent=1) + "\n",
                                                    encoding="utf-8", newline="\n")
    print(json.dumps(resumo, ensure_ascii=False))
    for cid, r in out.items():
        print(cid, "iguais", r["iguais"], "| sem declaração", [(x["caminho"], x["api"], x["real"]) for x in r["sem_declaracao"]][:5],
              "| divergentes", r["divergentes"][:5])


if __name__ == "__main__":
    main()
