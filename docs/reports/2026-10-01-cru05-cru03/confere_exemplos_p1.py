"""Confere a coluna 'hoje' dos exemplos E1–E4 com o pontuador REAL (bf46d51f). Não implementa P1."""
import sys

WT = "C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-noite-20260930"
sys.path.insert(0, WT)
sys.dont_write_bytecode = True
from src.builder.timeline import index as IX  # noqa: E402

N = IX._normalize_match_text


def topico(label, aliases=(), short=()):
    return {"unit_slug": "u1", "topic_slug": IX.slugify(label), "topic_label": label, "kind": "topic",
            "aliases": list(aliases), "generic_tokens": ["zzzz"], "short_vocab": list(short)}


def sinais(**campos):
    base = {k: "" for k in ("title_text", "markdown_headings_text", "markdown_lead_text", "markdown_text", "category_text",
                            "manual_tags_text", "auto_tags_text", "legacy_tags_text", "raw_text")}
    base.update({k: N(v) for k, v in campos.items()})
    return base


U1 = [topico("Máquinas de Turing"), topico("Variações de Máquinas de Turing"), topico("Máquinas de Turing Universais")]
casos = {
    "E1": (U1, sinais(title_text="Máquinas de Turing")),
    "E2": (U1, sinais(title_text="Máquinas de Turing", markdown_headings_text="Variações de Máquinas de Turing")),
    "E4": ([topico("Escalonamento"), topico("Algoritmos de Escalonamento")], sinais(markdown_headings_text="Escalonamento")),
    "E3": ([topico("Swapping"), topico("Memória Virtual"), topico("Paginação")], sinais(title_text="Memória Virtual")),
    # v2 (02/10): palavra única curta que não casa nem consigo mesma; E7 com divisor 1 -> 2 na taxonomia enriquecida
    "E4b": ([topico("CPU", short=["cpu"]), topico("Memória", short=["cpu"])], sinais(markdown_headings_text="CPU")),
    "E7_T1": ([topico("Swapping"), topico("Paginação")], sinais(markdown_headings_text="Paginação")),
    "E7_T2": ([topico("Swapping", aliases=["Paginação sob demanda"]), topico("Paginação")],
              sinais(markdown_headings_text="Paginação")),
}
for nome, (ts, s) in casos.items():
    sc = [round(IX._score_entry_against_taxonomy_topic(s, t), 4) for t in ts]
    o = sorted(sc, reverse=True)
    print(nome, sc, "margem_rel", round((o[0] - o[1]) / o[0], 4) if o[0] > 0 else None)
