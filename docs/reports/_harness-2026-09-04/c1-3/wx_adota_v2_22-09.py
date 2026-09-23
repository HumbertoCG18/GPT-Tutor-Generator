"""W-X adoção (22/09): régua v2 vira a vigente por decisão do usuário.

Decisões do usuário (22/09, sessão 8072c4bb): "Adota a v2; microsservicos4/7 em u02; CG 5 vazios em u05".

1. Congela a régua histórica (cópias byte a byte em regua_historica_22-09/: subunit_gt_SO, material_gt_ES2,
   material_gt_CG) — a versão vigente antes da adoção; o git guarda o resto.
2. Monta a v2 FINAL em wx_gold_v2_final_22-09/ = v2 do W-X (SO 4 linhas, ES2 microsservicos5) + os 2 rulings novos:
   ES2 microsservicos4/7 unidade u01 → u02; CG animacao-v2, instanciamento, pagina-com-videos-sobre-instanciamento,
   transformacoesgeometricas, transformacoesgl unidade u04 → u05 (sobrepõe o oráculo de 06/09 para esses 5).
   Só as 12 linhas mudam (verificado por diff); subunidade dos 5 do CG segue vazia (fora do denominador; v3).
3. Remede o estado #49 pela cadeia real do W-X (decisões congeladas antes de qualquer gold) sob a régua vigente
   e sob a v2 final; denominadores devem ser iguais.
4. Com --apply: copia a v2 final para docs/reports/ (vigente). Sem --apply: só mede e escreve o relatório.
"""
import csv
import difflib
import hashlib
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

T0 = time.time()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
REP = DATA / "docs/reports"
HIST = HERE / "regua_historica_22-09"
V2 = HERE / "wx_gold_v2_22-09"
FINAL = HERE / "wx_gold_v2_final_22-09"
OUT_JSON = HERE / "wx_adota_v2_22-09.json"
OUT_MD = HERE / "wx_adota_v2_22-09.md"
APPLY = "--apply" in sys.argv

ARQS = ("subunit_gt_SO.csv", "material_gt_ES2.csv", "material_gt_CG.csv")
U02_ES2 = "unidade-02-integracao-de-desenvolvimento-e-operacao-devops"
U05_CG = "unidade-05-transformacoes-geometricas"
RULINGS = {
    "material_gt_ES2.csv": {
        "microsservicos4": (U02_ES2, "ruling-user 2026-09-22: u02 (2.7 integracao/implantacao de microsservicos); decide o conflito 19/08 x 26/08"),
        "microsservicos7": (U02_ES2, "ruling-user 2026-09-22: u02 (2.7 integracao/implantacao de microsservicos); decide o conflito 19/08 x 26/08"),
    },
    "material_gt_CG.csv": {
        eid: (U05_CG, "ruling-user 2026-09-22: u05 pelo conteudo (5.1 transformacoes geometricas); sobrepoe o oraculo de 06/09")
        for eid in ("animacao-v2", "instanciamento", "pagina-com-videos-sobre-instanciamento", "transformacoesgeometricas", "transformacoesgl")
    },
}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def edita_csv(src: Path, dst: Path, rulings: dict) -> list:
    """Reescreve só o campo gold_units (+ notas) das linhas com ruling; preserva BOM, CRLF e as demais linhas byte a byte."""
    raw = src.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    rows = list(csv.reader(text.splitlines()))
    header = rows[0]
    i_id, i_gu, i_notas = header.index("entry_id"), header.index("gold_units"), header.index("notas")
    mudadas = []
    out_lines = text.splitlines()
    for k, row in enumerate(rows[1:], start=1):
        if len(row) <= i_gu or row[i_id] not in rulings:
            continue
        novo, nota = rulings[row[i_id]]
        antes = row[i_gu]
        row[i_gu] = novo
        row[i_notas] = (row[i_notas] + " | " if row[i_notas] else "") + nota
        buf = []
        csv.writer(_W(buf), lineterminator="").writerow(row)
        out_lines[k] = "".join(buf)
        mudadas.append({"id": row[i_id], "de": antes, "para": novo})
    assert {m["id"] for m in mudadas} == set(rulings), f"{src.name}: ids nao encontrados"
    data = nl.join(out_lines) + (nl if text.endswith(("\n", "\r\n")) else "")
    dst.write_bytes((b"\xef\xbb\xbf" if bom else b"") + data.encode("utf-8"))
    return mudadas


class _W:
    def __init__(self, buf):
        self.buf = buf

    def write(self, s):
        self.buf.append(s)


def linhas_diferentes(a: Path, b: Path) -> list:
    la = a.read_text(encoding="utf-8-sig").splitlines()
    lb = b.read_text(encoding="utf-8-sig").splitlines()
    return [l for l in difflib.unified_diff(la, lb, lineterm="", n=0) if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]


def main():
    # 1. congelar a régua vigente (antes da adoção)
    HIST.mkdir(exist_ok=True)
    congelados = {}
    for nome in ARQS:
        alvo = HIST / nome
        if not alvo.exists():
            shutil.copy2(REP / nome, alvo)
        congelados[nome] = sha(alvo)
        assert sha(REP / nome) == congelados[nome] or APPLY, f"{nome}: docs/reports difere do congelado e --apply nao foi pedido"

    # 2. v2 final = v2 do W-X + rulings novos
    FINAL.mkdir(exist_ok=True)
    mudancas = {}
    shutil.copy2(V2 / "subunit_gt_SO.csv", FINAL / "subunit_gt_SO.csv")
    mudancas["subunit_gt_SO.csv"] = [{"origem": "W-X v2", "linha": l} for l in linhas_diferentes(HIST / "subunit_gt_SO.csv", FINAL / "subunit_gt_SO.csv")]
    mudancas["material_gt_ES2.csv"] = edita_csv(V2 / "material_gt_ES2.csv", FINAL / "material_gt_ES2.csv", RULINGS["material_gt_ES2.csv"])
    mudancas["material_gt_CG.csv"] = edita_csv(HIST / "material_gt_CG.csv", FINAL / "material_gt_CG.csv", RULINGS["material_gt_CG.csv"])
    n_linhas = {nome: len(linhas_diferentes(HIST / nome, FINAL / nome)) // 2 for nome in ARQS}
    assert n_linhas == {"subunit_gt_SO.csv": 4, "material_gt_ES2.csv": 3, "material_gt_CG.csv": 5}, n_linhas
    print("LINHAS QUE MUDAM", n_linhas, flush=True)

    # 3. remedição pela cadeia do W-X, congelada antes do gold
    wx = load("wx_mod", HERE / "wx_regua_corrigida_22-09.py")
    compare = load("wx_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    nomes, uni = mede.NOMES, mede.UNI
    estado, congelado, sha_cong = wx.cadeia(nomes, compare)
    assert sha_cong == "94e4b83943a3ed45ebc6c1128e7b06d99061308b0d353fcd452db157d324f955", f"congelamento difere do W-X: {sha_cong}"
    hist_tot, hist_cur, hist_id, _ = wx.avalia(nomes, compare, estado, congelado, lambda s: wx.golds_de(s, HIST, uni))
    fin_tot, fin_cur, fin_id, _ = wx.avalia(nomes, compare, estado, congelado, lambda s: wx.golds_de(s, FINAL, uni))
    assert set(hist_id) == set(fin_id), "denominador mudou"
    delta = [{"curso": k[0], "id": k[1], "eixo": k[2], "vigente": hist_id[k], "v2_final": fin_id[k]} for k in sorted(hist_id) if hist_id[k] != fin_id[k]]
    print("PLACAR vigente", hist_tot, flush=True)
    print("PLACAR v2 final", fin_tot, flush=True)
    print("DELTA por id", delta, flush=True)

    # 4. aplicar
    aplicado = False
    if APPLY:
        for nome in ARQS:
            shutil.copy2(FINAL / nome, REP / nome)
        aplicado = True
        print("APLICADO em docs/reports:", ARQS, flush=True)

    r = {
        "tarefa": "W-X adocao da regua v2 (decisao do usuario 22/09)",
        "decisoes_usuario": ["adota a v2", "ES2 microsservicos4/7 -> u02", "CG 5 vazios (unidade) -> u05"],
        "congelado_regua_vigente_sha256": congelados,
        "v2_final_sha256": {nome: sha(FINAL / nome) for nome in ARQS},
        "linhas_que_mudam": n_linhas,
        "mudancas": mudancas,
        "sha256_congelamento_decisoes": sha_cong,
        "placar_vigente": hist_tot, "placar_v2_final": fin_tot,
        "cursos_vigente": hist_cur, "cursos_v2_final": fin_cur,
        "delta_por_id": delta,
        "aplicado": aplicado,
        "segundos": round(time.time() - T0, 1),
    }
    OUT_JSON.write_text(json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    L = ["# W-X adoção — régua v2 vigente (22/09)", "",
         "Decisões do usuário: adota a v2; ES2 microsservicos4/7 → u02; CG 5 (animacao-v2, instanciamento, pagina-com-videos-sobre-instanciamento, transformacoesgeometricas, transformacoesgl) → u05.", "",
         "## Linhas que mudam", ""]
    for nome, ms in mudancas.items():
        L.append(f"- `{nome}`: {n_linhas[nome]} linhas")
        for m in ms:
            L.append("  - " + (m["linha"][:160] if "linha" in m else f"{m['id']}: {m['de']} → {m['para']}"))
    L += ["", "## Placar do estado #49 (mesma cadeia e congelamento do W-X)", "", "| eixo | régua vigente | v2 final | delta |", "|---|---|---|---|"]
    for eixo in ("bloco", "unidade", "sub_primaria", "sub_aceita"):
        L.append(f"| {eixo} | {hist_tot.get(eixo)}/{hist_tot.get(eixo + '_n')} | {fin_tot.get(eixo)}/{fin_tot.get(eixo + '_n')} | {fin_tot.get(eixo, 0) - hist_tot.get(eixo, 0):+d} |")
    L += ["", "Delta por id: " + (", ".join(f"{d['curso']} {d['id']} ({d['eixo']}: {d['vigente']} → {d['v2_final']})" for d in delta) or "nenhum"), "",
          f"Aplicado em docs/reports: {'sim' if aplicado else 'não (sem --apply)'} · congelamento `{sha_cong[:16]}…` · {r['segundos']} s"]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("OK", OUT_JSON.name, sha(OUT_JSON)[:16], r["segundos"], "s", flush=True)


if __name__ == "__main__":
    main()
