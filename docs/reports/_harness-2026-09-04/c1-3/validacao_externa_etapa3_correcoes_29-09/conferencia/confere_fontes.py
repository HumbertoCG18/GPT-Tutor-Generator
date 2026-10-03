"""Conferência física local e READ-ONLY das fontes adquiridas na etapa 2 (29/09). Sem rede, sem escrita nas fontes.
v2 (CONF01): o resumo traz `integridade_global` = bytes conferem E inventário completo E selo do inventário confere.

1. bytes em disco x árvore congelada (`fontes_congeladas.json`) e x sha256 do inventário; divergências só listadas;
2. inventário x `contents.json` congelado de cada curso, item a item (módulo, arquivo, multiplicidade);
3. todo item no escopo (conteúdo de módulo) tem status; módulos sem conteúdo listados por tipo;
4. páginas e anexos de página: classificação e registro;
5. falhas, duplicatas (no curso e entre cursos) e formatos fora do recorte do pacote cego.
Os valores esperados NUNCA são recalculados para aceitar divergência. Uso: python confere_fontes.py
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
REPO = next(p for p in AQUI.parents if (p / ".git").is_dir())
E2 = AQUI.parents[1] / "validacao_externa_etapa2_29-09/aquisicao"
FONTES = REPO / ".frzero/validacao_externa_aquisicao_29-09"
STATUS_CONHECIDOS = {"ok", "link_externo", "sem_arquivo", "acima_do_limite", "nao_baixado_orcamento", "tipo_inesperado",
                     "assinatura_invalida"}
EXT_RECORTE = {"pdf", "docx", "pptx", "xlsx", "odt", "odp", "ods", "zip", "doc", "ppt", "xls", "png", "jpg", "jpeg", "gif",
               "txt", "md", "csv", "html", "htm", "ipynb", "py", "java", "c", "h", "cpp", "js", "ts", "sql", "mp4"}   # pacote-cego-2


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    inv_p, fc_p = E2 / "inventario_downloads.json", E2 / "fontes_congeladas.json"
    inv, fc = json.loads(inv_p.read_text(encoding="utf-8")), json.loads(fc_p.read_text(encoding="utf-8"))
    out = {"entradas": {"inventario_sha256": sha(inv_p), "fontes_congeladas_sha256": sha(fc_p),
                        "inventario_confere_com_congelamento": sha(inv_p) == fc["inventario_sha256"]}, "cursos": {}}
    por_sha_global = collections.defaultdict(set)
    for c in inv["cursos"]:
        cid, raiz = c["id"], FONTES / c["id"]
        esperado = fc["cursos"][cid]["arvore"]
        disco = {p.relative_to(raiz).as_posix(): sha(p) for p in sorted(raiz.rglob("*")) if p.is_file()}
        anexos_dir = FONTES / f"{cid}_anexos_de_pagina"
        anexos = sorted(p.name for p in anexos_dir.iterdir()) if anexos_dir.is_dir() else []
        r = {"bytes": {"arquivos_esperados": len(esperado), "arquivos_em_disco": len(disco),
                       "faltando": sorted(set(esperado) - set(disco)), "extras": sorted(set(disco) - set(esperado)),
                       "divergentes": sorted(k for k in set(esperado) & set(disco) if esperado[k] != disco[k])}}
        r["bytes"]["inventario_x_disco"] = sorted(a["caminho"] for a in c["arquivos"] if a.get("caminho")
                                                  and disco.get(a["caminho"]) != a.get("sha256"))
        contents = json.loads((raiz / "raw/moodle/contents.json").read_text(encoding="utf-8"))
        esperados_api, fora_escopo, paginas = collections.Counter(), collections.Counter(), []
        for sec in contents:
            for mod in sec.get("modules") or []:
                itens = mod.get("contents") or []
                if not itens:
                    fora_escopo[str(mod.get("modname"))] += 1
                if mod.get("modname") == "page":
                    paginas.append({"modulo_id": str(mod.get("id")), "arquivos": [str(i.get("filename")) for i in itens]})
                for i in itens:
                    esperados_api[(str(mod.get("id")), str(i.get("filename") or ""))] += 1
        registrados = collections.Counter((a["modulo_id"], a["arquivo"]) for a in c["arquivos"])
        status = collections.Counter(a["status"] for a in c["arquivos"])
        r["inventario_x_contents"] = {
            "itens_na_api": sum(esperados_api.values()), "itens_no_inventario": sum(registrados.values()),
            "sem_registro": sorted(f"{m}/{f}" for (m, f), n in esperados_api.items() if registrados[(m, f)] < n),
            "registro_sem_item_na_api": sorted(f"{m}/{f}" for (m, f), n in registrados.items() if esperados_api[(m, f)] < n),
            "chaves_modulo_arquivo_repetidas": sorted(f"{m}/{f} x{n}" for (m, f), n in esperados_api.items() if n > 1),
            "modulos_sem_conteudo_fora_do_escopo": dict(sorted(fora_escopo.items())),
            "todos_os_registros_com_status_conhecido": all(a["status"] in STATUS_CONHECIDOS for a in c["arquivos"]),
            "status": dict(sorted(status.items()))}
        reg_pag = [a for a in c["arquivos"] if a["modname"] == "page"]
        r["paginas"] = {"modulos": paginas, "registros": [{k: a.get(k) for k in ("modulo_id", "arquivo", "status", "caminho")} for a in reg_pag],
                        "anexos_em_disco": anexos}
        r["falhas"] = [{k: a.get(k) for k in ("modulo_id", "modname", "arquivo", "status", "tamanho_api")}
                       for a in c["arquivos"] if a["status"] not in ("ok", "link_externo")]
        grupos = collections.defaultdict(list)
        for a in c["arquivos"]:
            if a.get("sha256"):
                grupos[a["sha256"]].append(a["caminho"])
                por_sha_global[a["sha256"]].add(cid)
        r["duplicatas_no_curso"] = [sorted(v) for v in grupos.values() if len(v) > 1]
        r["colisoes_de_nome"] = [a.get("caminho") for a in c["arquivos"] if a.get("colisao")]
        ext = collections.Counter(Path(a["arquivo"]).suffix.lower().lstrip(".") or "(sem)" for a in c["arquivos"] if a["status"] == "ok")
        r["formatos_ok"] = dict(sorted(ext.items()))
        r["formatos_fora_do_recorte"] = {e: n for e, n in ext.items() if e not in EXT_RECORTE}
        out["cursos"][cid] = r
    out["duplicatas_entre_cursos"] = sorted(sorted(v) for v in por_sha_global.values() if len(v) > 1)
    tot = collections.Counter()
    for r in out["cursos"].values():
        tot.update(r["inventario_x_contents"]["status"])
    ok_bytes = all(not (r["bytes"]["faltando"] or r["bytes"]["extras"] or r["bytes"]["divergentes"] or r["bytes"]["inventario_x_disco"])
                   for r in out["cursos"].values())
    ok_inv = all(not (r["inventario_x_contents"]["sem_registro"] or r["inventario_x_contents"]["registro_sem_item_na_api"])
                 and r["inventario_x_contents"]["todos_os_registros_com_status_conhecido"] for r in out["cursos"].values())
    selo = out["entradas"]["inventario_confere_com_congelamento"]
    out["resumo"] = {"integridade_global": ok_bytes and ok_inv and selo,   # v2 (CONF01): inclui o selo do inventário
                     "inventario_confere_com_congelamento": selo,
                     "bytes_conferem": ok_bytes, "inventario_completo": ok_inv, "status_total": dict(sorted(tot.items())),
                     "falhas": sum(len(r["falhas"]) for r in out["cursos"].values()),
                     "duplicatas_no_curso": sum(len(r["duplicatas_no_curso"]) for r in out["cursos"].values()),
                     "colisoes_de_nome": sum(len(r["colisoes_de_nome"]) for r in out["cursos"].values()),
                     "formatos_fora_do_recorte": {cid: r["formatos_fora_do_recorte"] for cid, r in out["cursos"].items()
                                                  if r["formatos_fora_do_recorte"]},
                     "paginas": sum(len(r["paginas"]["modulos"]) for r in out["cursos"].values()),
                     "anexos_de_pagina_em_disco": sum(len(r["paginas"]["anexos_em_disco"]) for r in out["cursos"].values())}
    (AQUI / "conferencia_fontes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out["resumo"], ensure_ascii=False, indent=1))
    for cid, r in out["cursos"].items():
        print(cid, "| repetidas", r["inventario_x_contents"]["chaves_modulo_arquivo_repetidas"][:3], "| fora", r["inventario_x_contents"]["modulos_sem_conteudo_fora_do_escopo"],
              "| páginas", [(p["modulo_id"], len(p["arquivos"])) for p in r["paginas"]["modulos"]])


if __name__ == "__main__":
    main()
