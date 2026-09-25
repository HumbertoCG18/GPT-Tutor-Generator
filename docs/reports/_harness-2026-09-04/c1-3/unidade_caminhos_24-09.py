"""Unidade (24/09): caminhos admissíveis sobre o congelamento do W-Z2, estimativa direta sem replay.

Lê só wz2_diagnostico_causal_23-09.json (base v2, 284 materiais com gold de unidade). Gold só avalia.
H-secao: seção do Moodle presente vence o bloco. É a variante "seção sozinha" já medida em 21/09 (W-H,
regra_secao_sozinha_fase_real_21-09): dominada pela R-sem-misto e com perda de subunidade em material SEM gold de
unidade (TCC aula-06), que esta estimativa não vê. Fica fora da soma; só documenta o alcance atual.
H-fallback: texto bruto acima do gate, sem empate, vence o `computed_block_id` do resolvedor antigo. Frente 3
(fronteiras/janela/cabeçalho) entra pelo ideal medido no W-Z2 (+4).
Uso: python unidade_caminhos_24-09.py  (grava unidade_caminhos_24-09.json ao lado)
"""
import collections
import hashlib
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FONTE = AQUI / "wz2_diagnostico_causal_23-09.json"
CURSOS = ("MF", "SO", "IA", "ES2", "TCC", "CG")
FRENTE3_IDEAL = {"ES2": 1, "IA": 2, "TCC": 1}  # W-Z2 §2.1/§5, oráculo de bloco; mecanismo ainda não definido


def _efeito(m, venceria: bool, acertaria: bool):
    if not venceria:
        return 0
    if acertaria and not m["acerto"]:
        return 1
    if m["acerto"] and not acertaria:
        return -1
    return 0


def main():
    bruto = FONTE.read_bytes()
    d = json.loads(bruto)
    M = d["unidade_materiais"]
    efeitos = {"H-secao": collections.Counter(), "H-fallback": collections.Counter()}
    ids = {"H-secao": [], "H-fallback": []}
    alcance = collections.Counter()
    for m in M:
        c = m["curso"]
        h = {
            "H-secao": (bool(m["secao"]), m["secao_acertaria"]),
            "H-fallback": (m["origem_do_bloco_usado"].startswith("computed") and m["bruto_gated"]
                           and not m["bruto_amb"] and m["bruto"] != m["previsto"], m["bruto_acertaria"]),
        }
        alcance[(c, "secao_presente")] += bool(m["secao"])
        alcance[(c, "secao_gold_da_secao")] += bool(m["secao"]) and m["proveniencia_gold"].endswith("secao_moodle")
        alcance[(c, "fallback")] += m["origem_do_bloco_usado"].startswith("computed")
        for nome, (vence, acertaria) in h.items():
            e = _efeito(m, vence, acertaria)
            if e:
                efeitos[nome][(c, "ganho" if e > 0 else "perda")] += 1
                ids[nome].append({"curso": c, "entry_id": m["entry_id"], "efeito": e})
    base = collections.Counter(m["curso"] for m in M if m["acerto"])
    total = collections.Counter(m["curso"] for m in M)
    linhas = []
    for c in CURSOS:
        ganho = efeitos["H-fallback"][(c, "ganho")] + FRENTE3_IDEAL.get(c, 0)
        perda = efeitos["H-fallback"][(c, "perda")]
        minimo = -(-9 * total[c] // 10) if total[c] * 9 % 10 else 9 * total[c] // 10 + 1
        linhas.append({"curso": c, "base": base[c], "n": total[c], "ideal": base[c] + ganho - perda,
                       "minimo_90": minimo, "ganho": ganho, "perda": perda})
    out = {
        "fonte_sha256": hashlib.sha256(bruto).hexdigest(),
        "escopo": "estimativa direta sobre o congelamento do W-Z2; sem replay; 2a passada e subunidade não recalculadas",
        "efeitos": {n: {f"{k[0]}:{k[1]}": v for k, v in e.items()} for n, e in efeitos.items()},
        "ids": ids,
        "alcance": {f"{k[0]}:{k[1]}": v for k, v in alcance.items()},
        "frente3_ideal": FRENTE3_IDEAL,
        "por_curso": linhas,
        "total": {"base": sum(base.values()), "n": len(M),
                  "ideal": sum(r["ideal"] for r in linhas), "minimo_90": 256},
    }
    (AQUI / "unidade_caminhos_24-09.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in linhas:
        print(f'{r["curso"]:4} {r["base"]}/{r["n"]} -> ideal {r["ideal"]} (mínimo >90%: {r["minimo_90"]})')
    t = out["total"]
    print(f'total {t["base"]}/{t["n"]} -> ideal {t["ideal"]} (mínimo >90%: {t["minimo_90"]})')
    print("ids:", json.dumps(ids, ensure_ascii=False))


if __name__ == "__main__":
    main()
