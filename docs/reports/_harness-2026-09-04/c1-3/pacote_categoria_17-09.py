"""Pacote de fontes com a categoria prova corrigida na entrada; 0 LLM; src/ intocado."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

# protocolo-herancas-cru_15-09.md:55-60: MF e IA em paralelo saturaram com 50 threads por processo.
for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(var, "1")
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pacote_driver", HERE / "pacote_fontes_15-09.py")
pacote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pacote)
DESTINO = ".frzero/pacote_categoria_17-09"


def candidate(name, original):
    # Copia literal de verifica_categoria_prova_15-09.py:21-26; importar de la arrasta diagnostica_perdas.
    normalized = "".join(c for c in unicodedata.normalize("NFD", name.lower())
                         if not unicodedata.combining(c))
    explicit_exam = re.search(r"(?:^|[\W_])(?:p[123]|av[12]|exame|test|avaliacao|prova[\W_]*[123])(?:$|[\W_])", normalized)
    mathematical = re.search(r"provas?[\W_]*(?:indutiv\w*|por[\W_]+induc\w*)", normalized)
    return "material-de-aula" if original == "provas" and mathematical and not explicit_exam else original


def selfcheck():
    ref = json.loads((HERE / "verificacao_categoria_prova_verificada_15-09.json").read_text(encoding="utf-8"))["courses"]["MF"]
    assert len(ref["category_changes"]) == 3 and len(ref["synthetic_exam_guards"]) == 6, "referencia de 15/09 mudou"
    for row in ref["category_changes"]:
        assert candidate(row["input"], row["before"]) == row["after"] == "material-de-aula", row
    for row in ref["synthetic_exam_guards"]:
        assert candidate(row["synthetic_name"], "provas") == row["category"] == "provas", row
    assert candidate("Prova por inducao.pdf", "listas") == "listas"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curso", choices=pacote.base.COURSES, required=True)
    parser.add_argument("--inventario", action="store_true", help="so classifica; nao constroi")
    args = parser.parse_args()
    selfcheck()
    base_main = pacote.base.main
    dest = pacote.base.ROOT / DESTINO / pacote.base.COURSES[args.curso]
    decisions, inventory = {}, []

    def main_with_destino():
        # pacote_fontes_15-09.py:59-62 fixa o destino em sys.argv logo antes de chamar base.main.
        argv = list(sys.argv)
        argv[argv.index("--destino") + 1] = DESTINO
        if args.inventario:
            argv.append("--inventario")
        sys.argv = argv
        from src.builder.core import stash_import
        original_detect, original_scan = stash_import.auto_detect_category, stash_import.scan_stash_cards

        def detect(name, is_image=False, frases_do_plano=None):
            before = original_detect(name, is_image=is_image, frases_do_plano=frases_do_plano)
            after = candidate(name, before)
            decisions[name] = {"original": before, "proposed": after}
            return after

        def scan(*a, **kw):
            result = original_scan(*a, **kw)
            for item in result.items:
                if item.file_type == "zip":  # stash_import.py:40-41: sem classificacao por nome
                    record = {"classified_name": None, "original": item.category, "proposed": item.category}
                else:  # stash_import.py:43-44 monta o nome classificado
                    name = f"{item.moodle_label} {Path(item.source_path).name}" if item.moodle_label else Path(item.source_path).name
                    record = {"classified_name": name, **decisions[name]}
                assert record["proposed"] == item.category, (item.source_path, record)
                inventory.append({"source_path": item.source_path, "file_type": item.file_type,
                                  "card": item.card_name, **record})
            return result

        stash_import.auto_detect_category, stash_import.scan_stash_cards = detect, scan
        try:
            return base_main()
        finally:
            stash_import.auto_detect_category, stash_import.scan_stash_cards = original_detect, original_scan

    pacote.base.main = main_with_destino
    sys.argv = [str(HERE / "pacote_fontes_15-09.py"), "--curso", args.curso]
    try:
        return pacote.main()
    finally:
        pacote.base.main = base_main
        changes = [r for r in inventory if r["original"] != r["proposed"]]
        record = {"course": args.curso, "destino": str(dest), "inputs": inventory, "changes": changes,
                  "calls": dict(pacote.base.CALLS), "rule": "candidate() de verifica_categoria_prova_15-09.py"}
        if dest.is_dir():
            (dest / "_categoria_17-09.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{args.curso}] categorias alteradas={len(changes)}: "
              + json.dumps([(Path(r["source_path"]).name, r["original"], r["proposed"]) for r in changes], ensure_ascii=False),
              flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
