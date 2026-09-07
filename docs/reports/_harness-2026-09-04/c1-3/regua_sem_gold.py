"""REGUA SEM GOLD (07/09) — o produto real: o aluno nunca cria gold, a verdade vem do professor (SARC/Moodle/cronograma).
Tres eixos, tres fontes independentes do motor:
  BLOCO      posicao datada do professor no Moodle (label datado, data no nome do modulo, secao-semana, faixa dos irmaos datados)
             — mesma logica de `coerencia_moodle.py`; cobre onde o professor datou.
  UNIDADE    numero explicito de unidade na secao ("U2 - ..."), titulo da unidade contido na secao, ou — quando a secao nomeia um
             TOPICO do plano — a unidade DONA desse topico (o plano numera X.Y: "3.5 Segmentacao" pertence a unidade 03).
  SUBUNIDADE secao numerada do Moodle que nomeia um TOPICO do plano ("6 - Processo de Visualizacao 2D") — caso CG.
Reporta cobertura (quantos materiais a fonte alcanca) e concordancia (motor x professor), por curso e por regime.
CIRCULARIDADE declarada: o motor tem regras que leem a secao (unidade explicita, S1b da subunidade). A regua marca quantos
acertos vem de material onde essa regra AGIU (reason `unidade-explicita=`/`secao-nomeia-subtopico`) — esses nao sao independentes.
Uso: regua_sem_gold.py [<dir-do-regime> ...]   (sem args: produto)"""
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
C13 = GEN / "docs/reports/_harness-2026-09-04/c1-3"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
src = (C13 / "coerencia_moodle.py").read_text(encoding="utf-8")
ns = {"__name__": "coerencia_lib", "__file__": str(C13 / "coerencia_moodle.py")}
exec(src.split("TOT = collections.Counter()")[0], ns)
placement_of, bid = ns["placement_of"], ns["bid"]
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402
from src.builder.routing.file_map import explicit_unit_number, _unit_number_from_slug  # noqa: E402

REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
        "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
_SEC_NUM = re.compile(r"^\s*(\d+)\s*[-.:]\s*(.+)$")
_GEN = {"introducao", "conceitos", "fundamentos", "exercicios", "atividades", "provas", "gabarito", "plano", "avisos",
        "tutoriais", "duvidas", "noticias", "tde", "aula", "aulas", "material", "materiais", "resolvidas"}


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()).strip()


def toks(s):
    return {t for t in norm(s).split() if len(t) > 3 and t not in _GEN}


def secao_nomeia_topico(secao: str, tax: dict):
    """(unit_slug, topic_slug) do topico do plano que a SECAO do Moodle nomeia; (None, None) se nao houver 1 so."""
    m = _SEC_NUM.match(str(secao or ""))
    corpo = m.group(2) if m else str(secao or "")
    st = toks(corpo)
    if not st:
        return None, None
    achados = []
    for u in tax.get("units") or []:
        for t in u.get("topics") or []:
            tt = toks(t.get("label"))
            if tt and (tt <= st or st <= tt):
                achados.append((u["slug"], t["slug"]))
    return achados[0] if len(achados) == 1 else (None, None)


def secao_nomeia_unidade(entry: dict, tax: dict):
    n = explicit_unit_number(entry)
    if n:
        alvo = [u["slug"] for u in tax.get("units") or [] if _unit_number_from_slug(u["slug"]) == n]
        if len(alvo) == 1:
            return alvo[0]
    sec = norm(re.sub(r"^\s*\d+(\.\d+)*\s*[-.:]?\s*", "", str(entry.get("source_section") or "")))
    if not sec:
        return None
    alvo = []
    for u in tax.get("units") or []:
        core = norm(re.sub(r"^\s*unidade(\s+de\s+aprendizagem)?\s*\d+\s*[\u2014\-\u2013:]?\s*", "", str(u.get("title") or "")))
        if core and (core in sec or sec in core):
            alvo.append(u["slug"])
    return alvo[0] if len(alvo) == 1 else None


def bloco_por_assunto_da_secao(secao: str, blocks: list):
    """Blocos cujo ASSUNTO (topic_text + labels das sessoes, fonte = cronograma/SARC) casa com o nome da SECAO do Moodle.
    Independente do cronograma: a secao vem do Moodle, o assunto do bloco vem do syllabus. Vazio se nao casar em 1 grupo."""
    m = _SEC_NUM.match(str(secao or ""))
    st = toks(m.group(2) if m else str(secao or ""))
    if not st:
        return []
    hit = []
    for b in blocks:
        bt = toks(str(b.get("topic_text") or "") + " " + " ".join(str(s.get("label") or "") for s in (b.get("sessions") or [])))
        if bt and (st <= bt or bt <= st or len(st & bt) >= 2):
            hit.append(b["id"])
    return hit


def mede(root: Path, sig: str, tax: dict):
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    ti = {}
    for b in json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]:
        ti[b["block_uuid"]] = b["id"]; ti[b["id"]] = b["id"]
    ctx = build_motor_context(root, str((man.get("course") or {}).get("course_name") or ""))
    place = placement_of(sig, REPO[sig], man, ctx)
    c = collections.Counter()
    for e in man["entries"]:
        eid = e["id"]
        # BLOCO
        bl, _fonte = place.get(eid, ([], ""))
        bl = [x for x in dict.fromkeys(bl or [])]
        atual = ti.get(str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or ""), "")
        if not bl:
            # sem posicao datada (CG/LR/FR): assunto da secao do Moodle x assunto do bloco (cronograma)
            alvo = bloco_por_assunto_da_secao(e.get("source_section"), ctx.blocks)
            if alvo:
                c["bloco2: secao nomeia assunto"] += 1
                c["bloco2: coerente"] += atual in alvo
                c["bloco2: alvo unico"] += len(alvo) == 1
                if len(alvo) == 1:
                    c["bloco2: coerente (alvo unico)"] += atual == alvo[0]
        if bl:
            c["bloco: com posicao"] += 1
            c["bloco: coerente"] += atual in bl
            c["bloco: posicao unica"] += len(bl) == 1
            if len(bl) == 1:
                c["bloco: coerente (posicao unica)"] += atual == bl[0]
        # UNIDADE — direto (numero/titulo na secao) ou HERDADA do topico que a secao nomeia (o plano numera X.Y)
        u_prof = secao_nomeia_unidade(e, tax)
        u_topico = secao_nomeia_topico(e.get("source_section"), tax)[0]
        if not u_prof and u_topico:
            u_prof = u_topico
            c["unidade: herdada do topico da secao"] += 1
        if u_prof:
            c["unidade: secao nomeia"] += 1
            c["unidade: coerente"] += str(e.get("computed_unit_slug") or "") == u_prof
            if any(str(r).startswith("unidade-explicita=") or str(r).startswith("explicita-vence-bloco=") for r in (e.get("unit_match_reasons") or [])):
                c["unidade: (circular: regra da secao agiu)"] += 1
        # SUBUNIDADE
        u_t, t_t = secao_nomeia_topico(e.get("source_section"), tax)
        if t_t:
            c["sub: secao nomeia topico"] += 1
            c["sub: coerente"] += str(e.get("computed_subunit_slug") or "") == t_t
            c["sub: vazia"] += not str(e.get("computed_subunit_slug") or "")
            if any("secao-nomeia-subtopico" in str(r) for r in (e.get("subunit_match_reasons") or [])):
                c["sub: (circular: S1b agiu)"] += 1
    return c


REGIMES = {"produto": GH}
for a in sys.argv[1:]:
    REGIMES[Path(a).name] = Path(a)
for nome, base in REGIMES.items():
    print(f"\n########## REGIME {nome} ({base})")
    TOT = collections.Counter()
    for sig, repo in REPO.items():
        root = base / repo
        if not (root / "manifest.json").exists():
            continue
        tax_p = GH / repo / "course/.content_taxonomy.json"
        tax = json.loads(tax_p.read_text(encoding="utf-8")) if tax_p.exists() else {}
        c = mede(root, sig, tax)
        TOT.update(c)
        print(f"  {sig:4} bloco {c['bloco: coerente']:3}/{c['bloco: com posicao']:3}"
              f" (posicao unica {c['bloco: coerente (posicao unica)']:3}/{c['bloco: posicao unica']:3})"
              f" | bloco2 {c['bloco2: coerente']:3}/{c['bloco2: secao nomeia assunto']:3} (unico {c['bloco2: coerente (alvo unico)']:2}/{c['bloco2: alvo unico']:2}) | unidade {c['unidade: coerente']:3}/{c['unidade: secao nomeia']:3} (circ {c['unidade: (circular: regra da secao agiu)']:2})"
              f" | sub {c['sub: coerente']:3}/{c['sub: secao nomeia topico']:3} (circ {c['sub: (circular: S1b agiu)']:2}, vazia {c['sub: vazia']:2})")
    c = TOT
    print(f"  {'TOT':4} bloco {c['bloco: coerente']:3}/{c['bloco: com posicao']:3}"
          f" (posicao unica {c['bloco: coerente (posicao unica)']:3}/{c['bloco: posicao unica']:3})"
          f" | bloco2 {c['bloco2: coerente']:3}/{c['bloco2: secao nomeia assunto']:3} (unico {c['bloco2: coerente (alvo unico)']:2}/{c['bloco2: alvo unico']:2}) | unidade {c['unidade: coerente']:3}/{c['unidade: secao nomeia']:3} (circ {c['unidade: (circular: regra da secao agiu)']:2})"
          f" | sub {c['sub: coerente']:3}/{c['sub: secao nomeia topico']:3} (circ {c['sub: (circular: S1b agiu)']:2}, vazia {c['sub: vazia']:2})")
