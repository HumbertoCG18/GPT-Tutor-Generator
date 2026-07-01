from scripts.dedup_manifest import norm_key, plan_dedup


def test_norm_key_collapses_spacing_dash_and_combining_diacritic():
    a = norm_key("Aula07 Maquinas de Turing.pdf")
    b = norm_key("Aula 07 - Maquinas de Turing.pdf")
    c = norm_key("Aula 07 - Maquinas de Turing .pdf")  # espaco sobrando
    assert a == b == c
    # precomposto (U+00E9) vs decomposto (e + U+0301) colapsam na mesma chave
    assert norm_key("café.pdf") == norm_key("café.pdf")
    # acento removido: 'Maquinas' (NFKD de a-acute -> a)
    assert norm_key("Máquinas.pdf") == norm_key("Maquinas.pdf")


def test_plan_dedup_removes_stale_twin_keeps_stash():
    entries = [
        {"id": "old", "source_path": "C:/Users/x/Downloads/TCC/Aula 17 - NP-Completude .pdf",
         "source_section": "Semana 12"},
        {"id": "new", "source_path": "C:/Users/x/Desktop/Moodle/tcc/Semana 12/Aula 17 - NP-Completude.pdf",
         "source_section": "Semana 12"},
    ]
    stash = {"aula 17 - np-completude.pdf"}  # so o novo existe no stash
    removals, ambiguous = plan_dedup(entries, stash)
    assert [e["id"] for _i, e in removals] == ["old"]
    assert ambiguous == []


def test_plan_dedup_preserves_when_no_stash_twin():
    entries = [
        {"id": "a", "source_path": "/d/Aula 01.pdf"},
        {"id": "b", "source_path": "/d/Aula 01 .pdf"},
    ]
    removals, ambiguous = plan_dedup(entries, set())  # nenhum no stash
    assert removals == []
    assert len(ambiguous) == 1


def test_plan_dedup_preserves_when_all_in_stash():
    entries = [
        {"id": "a", "source_path": "/d/Aula 01.pdf"},
        {"id": "b", "source_path": "/d/Aula 01 .pdf"},
    ]
    stash = {"aula 01.pdf", "aula 01 .pdf"}  # ambos no stash
    removals, ambiguous = plan_dedup(entries, stash)
    assert removals == []
    assert len(ambiguous) == 1


def test_plan_dedup_ignores_distinct_files():
    entries = [
        {"id": "a", "source_path": "/d/Aula 01.pdf"},
        {"id": "b", "source_path": "/d/Aula 02.pdf"},
    ]
    removals, ambiguous = plan_dedup(entries, {"aula 02.pdf"})
    assert removals == []
    assert ambiguous == []
