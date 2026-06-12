"""Testes TDD para _dedup_entry_id (bug B5).

Comportamentos esperados (ver Task 10 do plano):
- 2 arquivos mesmo basename, categorias diferentes -> ids únicos com sufixo de categoria
- 3º mesmo id+categoria -> contador
- mesmo source_path -> fluxo already_exists intacto (não passa por _dedup_entry_id)
"""
from src.builder.ops.lifecycle_ops import _dedup_entry_id


def test_ids_sem_colisao_retorna_original():
    existing = {"introducao", "aula-01"}
    assert _dedup_entry_id("introducao-slides", "slides", existing) == "introducao-slides"


def test_ids_duplicados_ganham_sufixo_de_categoria():
    # "introducao" existe (de outro source_path) -> ganha sufixo da categoria
    existing = {"introducao"}
    result = _dedup_entry_id("introducao", "codigo-professor", existing)
    assert result == "introducao-codigo-professor"
    assert result not in existing  # novo id nao colide


def test_ids_duplicados_categoria_vazia_ganha_contador():
    # sem categoria -> sufixo numérico
    existing = {"introducao"}
    result = _dedup_entry_id("introducao", "", existing)
    assert result == "introducao-2"


def test_mesmo_id_mesma_categoria_ganha_contador():
    # 3o arquivo "introducao" também codigo-professor (outra pasta)
    # -> "introducao-codigo-professor-2"
    existing = {"introducao", "introducao-codigo-professor"}
    result = _dedup_entry_id("introducao", "codigo-professor", existing)
    assert result == "introducao-codigo-professor-2"


def test_contador_incrementa_ate_livre():
    # varios ja existentes -> continua contando
    existing = {
        "introducao",
        "introducao-slides",
        "introducao-slides-2",
        "introducao-slides-3",
    }
    result = _dedup_entry_id("introducao", "slides", existing)
    assert result == "introducao-slides-4"


def test_categoria_slugificada():
    # categoria com espaços/maiúsculas é slugificada
    existing = {"introducao"}
    result = _dedup_entry_id("introducao", "Código Professor", existing)
    # slugify("Código Professor") -> "codigo-professor"
    assert result == "introducao-codigo-professor"
