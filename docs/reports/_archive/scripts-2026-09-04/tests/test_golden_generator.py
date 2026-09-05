"""Testes do gerador do golden set (funções puras; sem disco real)."""
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "build_golden",
    Path(__file__).resolve().parents[1] / "scripts" / "build_golden_metodos_formais.py",
)
build_golden = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(build_golden)

_CARD_MAP = {
    "Secao Um Bloco": {"block_ids": ["bloco-04"], "source": "manual"},
    "Secao Dois Blocos": {"block_ids": ["bloco-05", "bloco-06"], "source": "manual"},
}
_SEC_INDEX = {"a.pdf": "Secao Um Bloco", "b.pdf": "Secao Dois Blocos",
              "d.pdf": "Secao Sem Gabarito"}


def _entry(eid, base, **kw):
    e = {"id": eid, "title": eid, "category": "material-de-aula",
         "source_path": f"C:/x/{base}", "computed_unit_slug": "u1",
         "unit_match_confidence": 0.7}
    e.update(kw)
    return e


def test_secao_um_bloco_vira_expected_automatico():
    case = build_golden.case_for_entry(_entry("e1", "a.pdf"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_block_id"] == "bloco-04"
    assert case["expected_origin"] == "gabarito_1bloco"


def test_secao_dois_blocos_vira_null_com_candidatos():
    case = build_golden.case_for_entry(_entry("e2", "b.pdf"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_block_id"] is None
    assert case["expected_origin"] == "precisa_decisao"
    assert case["candidates"] == ["bloco-05", "bloco-06"]


def test_sem_secao_fisica_vira_excluido():
    case = build_golden.case_for_entry(_entry("e3", "naoexiste.pdf"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_origin"] == "excluido"


def test_secao_sem_gabarito():
    case = build_golden.case_for_entry(_entry("e4", "d.pdf"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_block_id"] is None
    assert case["expected_origin"] == "sem_gabarito"


def test_bloco_manual_vira_excluido():
    case = build_golden.case_for_entry(
        _entry("e5", "a.pdf", manual_timeline_block_id="bloco-09"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_origin"] == "excluido"


def test_categoria_fora_da_timeline_vira_excluido():
    case = build_golden.case_for_entry(
        _entry("e6", "a.pdf", category="bibliografia"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_origin"] == "excluido"


def test_case_grava_raw_target_com_basename_do_source_path():
    """S4b: o harness deriva a ferramenta da EXTENSÃO via raw_target — o caso
    precisa carregar o basename do source_path real (.thy/.dfy inclusos)."""
    case = build_golden.case_for_entry(_entry("e1", "a.pdf"), _SEC_INDEX, _CARD_MAP)
    assert case["raw_target"] == "a.pdf"
    e_thy = _entry("e7", "a.pdf")
    e_thy["source_path"] = r"C:\x\Provas por Inducao\provas.thy"
    case_thy = build_golden.case_for_entry(e_thy, {"provas.thy": "Secao Um Bloco"}, _CARD_MAP)
    assert case_thy["raw_target"] == "provas.thy"


def test_merge_preserva_decisao_humana():
    old = [{"id": "e2", "category": "material-de-aula", "expected_block_id": "bloco-06",
            "expected_origin": "precisa_decisao", "note": "aula de listas"}]
    new = [build_golden.case_for_entry(_entry("e2", "b.pdf"), _SEC_INDEX, _CARD_MAP)]
    build_golden.merge_manual_decisions(old, new)
    assert new[0]["expected_block_id"] == "bloco-06"


def test_merge_nao_inventa_decisao():
    new = [build_golden.case_for_entry(_entry("e2", "b.pdf"), _SEC_INDEX, _CARD_MAP)]
    build_golden.merge_manual_decisions([], new)
    assert new[0]["expected_block_id"] is None


def test_merge_distingue_ids_duplicados_por_categoria():
    """Manifest real tem ids duplicados (ex. 'introducao' material + codigo)."""
    old = [{"id": "e2", "category": "material-de-aula", "expected_block_id": "bloco-05",
            "expected_origin": "precisa_decisao", "note": ""},
           {"id": "e2", "category": "codigo-professor", "expected_block_id": "bloco-06",
            "expected_origin": "precisa_decisao", "note": ""}]
    new = [build_golden.case_for_entry(_entry("e2", "b.pdf"), _SEC_INDEX, _CARD_MAP),
           build_golden.case_for_entry(_entry("e2", "b.pdf", category="codigo-professor"),
                                       _SEC_INDEX, _CARD_MAP)]
    build_golden.merge_manual_decisions(old, new)
    assert new[0]["expected_block_id"] == "bloco-05"
    assert new[1]["expected_block_id"] == "bloco-06"


def test_stash_section_index_exclui_basename_ambiguo(tmp_path):
    (tmp_path / "Sec A").mkdir(); (tmp_path / "Sec B").mkdir()
    (tmp_path / "Sec A" / "x.pdf").write_bytes(b"a")
    (tmp_path / "Sec B" / "x.pdf").write_bytes(b"b")
    (tmp_path / "Sec A" / "unico.pdf").write_bytes(b"c")
    idx = build_golden.stash_section_index(tmp_path)
    assert "x.pdf" not in idx
    assert idx["unico.pdf"] == "Sec A"
