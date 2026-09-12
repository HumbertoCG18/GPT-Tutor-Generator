"""GERADOR do sidecar de sinonimos SEM GOLD: so SARC + Moodle + headings dos materiais.

Substitui `course/.glossary_curation.json` (hoje "proposto-claude a partir de subunit_gt_<curso>" em SO/IA/ES2/TCC)
por um sidecar derivado apenas de fontes do professor. Cada sinonimo carrega a origem.

Regras de doacao (nenhuma olha o gold):
  SECAO   a secao do Moodle nomeia exatamente UM topico da unidade dominante dos seus materiais -> o vocabulario dos
          materiais daquela secao (titulo + label do Moodle + headings do markdown) doa para esse topico.
          Medido em 07/09: 19 de 76 secoes nomeiam, cobrem 68/222 materiais e a atribuicao direta acerta 78%.
  SARC    o label da sessao do bloco nomeia exatamente UM topico da unidade do bloco -> os tokens restantes do label
          doam para esse topico.

Filtros do ruido (o que separa vocabulario de boilerplate; sem eles a doacao traz "conteudo", "extraido", "slides"):
  - stopwords e genericos do motor (`_tokens` do unit_matcher ja tira);
  - token que aparece no rotulo/alias de OUTRO topico do curso (nao discrimina);
  - token com document frequency > DF_MAX dos materiais do curso (o mesmo teto de `_partes_de_rotulo`);
  - token com menos de MIN_LEN caracteres ou puramente numerico.

Uso: gera_sidecar_professor.py [--escrever DIR]   (sem --escrever, so imprime o que geraria)
"""
import collections
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
CURSOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
          "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor",
          "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
DF_MAX = 0.15      # token em mais de 15% dos materiais do curso nao discrimina
MIN_LEN = 4
CONC_MIN = 0.80    # o token doado tem de estar CONCENTRADO na secao que doa: >=80% das suas ocorrencias no curso
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing.resolver_apply import _secao_nomeia_subtopico  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.text.stopwords import (MOTOR_GENERIC_STEMS, SEMANTIC_TOKEN_STOPWORDS,  # noqa: E402
                                        TIMELINE_GENERIC_TOKENS)
from src.builder.timeline.unit_matcher import _tokens  # noqa: E402
from src.models.core import moodle_label_text  # noqa: E402

H_RE = re.compile(r"^#{1,3}\s+(.+)$", re.M)
NUM_RE = re.compile(r"^\d+$")
BOILER = set(SEMANTIC_TOKEN_STOPWORDS) | set(TIMELINE_GENERIC_TOKENS)


def gera(root: Path) -> dict:
    man = list(json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"])
    tax = load_internal_content_taxonomy(root)
    units = tax.get("units")
    ulist = list(units.values()) if isinstance(units, dict) else list(units or [])
    # taxonomia LIMPA: sem os sinonimos do sidecar atual (o gerador nao pode depender do que substitui)
    curp = root / "course/.glossary_curation.json"
    curados = set()
    if curp.exists():
        for k, v in json.loads(curp.read_text(encoding="utf-8")).items():
            if not k.startswith("_"):
                curados |= {N(s) for s in (v.get("synonyms") or [])}
    tops_por_unidade = collections.defaultdict(list)
    chave, vocab_topico = {}, {}
    for u in ulist:
        us = str(u.get("slug") or "")
        for t in (u.get("topics") or []):
            al = [a for a in (t.get("aliases") or []) if N(a) not in curados]
            rec = {"topic_slug": str(t.get("slug") or ""), "topic_label": str(t.get("label") or ""),
                   "aliases": al, "generic_tokens": t.get("generic_tokens") or []}
            tops_por_unidade[us].append(rec)
            code = str(t.get("code") or "").strip()
            chave[(us, rec["topic_slug"])] = f"{code} {rec['topic_label']}".strip()
            vocab_topico[(us, rec["topic_slug"])] = _tokens(" ".join([rec["topic_label"]] + al))
    # document frequency dos tokens nos materiais
    df = collections.Counter()
    textos = 0
    for e in man:
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        if not md:
            continue
        textos += 1
        df.update(set(_tokens(md)))
    teto = DF_MAX * max(1, textos)
    # vocabulario de TODOS os topicos (para tirar token que nomeia outro)
    todo_vocab = collections.Counter()
    for k, v in vocab_topico.items():
        todo_vocab.update(set(v))

    doado = collections.defaultdict(lambda: collections.defaultdict(set))  # (u,t) -> origem -> tokens
    escopo: dict = {}   # (u,t) -> ids dos materiais da secao doadora
    tok_ids = collections.defaultdict(set)   # token -> ids dos materiais do curso que o contem
    for e in man:
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        for tk in _tokens(md):
            tok_ids[tk].add(str(e.get("id") or ""))
    # --- SECAO do Moodle
    porsec = collections.defaultdict(list)
    for e in man:
        s = str(e.get("source_section") or "").strip()
        if s:
            porsec[s].append(e)
    for sec, ents in porsec.items():
        u = collections.Counter(str(x.get("computed_unit_slug") or "") for x in ents).most_common(1)[0][0]
        tops = tops_por_unidade.get(u, [])
        alvo = _secao_nomeia_subtopico({"source_section": sec}, tops, MOTOR_GENERIC_STEMS)
        if not alvo:
            continue
        ids_sec = {str(x.get("id") or "") for x in ents}
        escopo.setdefault((u, alvo), set()).update(ids_sec)
        for e in ents:
            md = eng._entry_markdown_text_for_file_map(root, e) or ""
            txt = f"{e.get('title') or ''} {moodle_label_text(e) or ''} {' '.join(H_RE.findall(md)[:8])}"
            doado[(u, alvo)]["secao"] |= _tokens(txt)
    # --- SARC
    tlp = root / "course/.timeline_index.json"
    if tlp.exists():
        for b in json.loads(tlp.read_text(encoding="utf-8")).get("blocks") or []:
            u = str(b.get("unit_slug") or "")
            tops = tops_por_unidade.get(u, [])
            lab = " ".join(str(s.get("label") or "") for s in (b.get("sessions") or []))
            if not tops or not lab:
                continue
            alvo = _secao_nomeia_subtopico({"source_section": lab}, tops, MOTOR_GENERIC_STEMS)
            if alvo:
                doado[(u, alvo)]["sarc"] |= _tokens(lab)

    out, stats = {}, collections.Counter()
    for (u, t), porig in doado.items():
        proprio = vocab_topico.get((u, t), set())
        syn = {}
        for origem, toks in porig.items():
            for tok in toks:
                stats["bruto"] += 1
                if len(tok) < MIN_LEN or NUM_RE.match(tok):
                    continue
                if tok in proprio:
                    continue
                if todo_vocab[tok] - (1 if tok in proprio else 0) > 0:   # nomeia outro topico
                    stats["corta_outro"] += 1
                    continue
                if tok in BOILER:
                    stats["corta_boiler"] += 1
                    continue
                if df[tok] > teto:
                    stats["corta_df"] += 1
                    continue
                ocorr = tok_ids.get(tok, set())
                dentro = ocorr & escopo.get((u, t), set())
                if ocorr and len(dentro) / len(ocorr) < CONC_MIN:
                    stats["corta_concentracao"] += 1
                    continue
                syn.setdefault(tok, set()).add(origem)
        if not syn:
            continue
        k = chave.get((u, t)) or t
        out[k] = {"synonyms": sorted(syn), "_origem": {s: sorted(o) for s, o in sorted(syn.items())}}
        stats["topicos"] += 1
        stats["sinonimos"] += len(syn)
    out["_nota"] = (
        "GERADO automaticamente de fontes do PROFESSOR (SARC + secao do Moodle + titulo/headings dos materiais da secao), "
        "sem olhar gold nenhum — `c1-3/gera_sidecar_professor.py`, 2026-09-07. Substitui o sidecar anterior, que era "
        "'proposto-claude a partir de subunit_gt' e contaminava a regua (medido: 86/93 -> 26/93 ao remove-lo). "
        f"Filtros: df > {DF_MAX:.0%} dos materiais, token no vocabulario de outro topico, boilerplate academico "
        f"(SEMANTIC_TOKEN_STOPWORDS + TIMELINE_GENERIC_TOKENS), token disperso (menos de {CONC_MIN:.0%} das ocorrencias na secao que doa), "
        f"token com menos de {MIN_LEN} chars ou numerico, stopwords do motor. `_origem` diz de que fonte veio cada termo.")
    return out, stats


ESCREVER = "--escrever" in sys.argv
print(f"{'':5} {'topicos':>8} {'sinonimos':>10} {'df':>5} {'outro':>6} {'boiler':>7} {'disperso':>9}")
for sig, repo in CURSOS.items():
    root = GH / repo
    if not (root / "manifest.json").exists():
        continue
    out, st = gera(root)
    print(f"{sig:5} {st['topicos']:8} {st['sinonimos']:10} {st['corta_df']:5} {st['corta_outro']:6} {st['corta_boiler']:7} {st['corta_concentracao']:9}")
    for k, v in out.items():
        if k.startswith("_"):
            continue
        print(f"        {k[:44]:44} <- {v['synonyms'][:9]}")
    if ESCREVER:
        p = root / "course/.glossary_curation.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"        [escrito em {p}]")
