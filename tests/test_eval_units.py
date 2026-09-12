import json

from scripts.eval_units import score_course


def test_score_course_compara_por_block_uuid(tmp_path):
    gold_csv = tmp_path / "gold_units_X.csv"
    gold_csv.write_text(
        "block_uuid,block_id,true_unit\n"
        "uuid-1,bloco-01,unidade-01\n"
        "uuid-2,bloco-02,unidade-02\n"
        "uuid-3,bloco-03,\n",  # sem rotulo -> fora do denominador
        encoding="utf-8",
    )
    index = {"blocks": [
        {"block_uuid": "uuid-1", "id": "bloco-01", "unit_slug": "unidade-01"},
        {"block_uuid": "uuid-2", "id": "bloco-02", "unit_slug": "unidade-99"},
        {"block_uuid": "uuid-3", "id": "bloco-03", "unit_slug": "unidade-03"},
    ]}
    r = score_course(gold_csv, index)
    assert (r["ok"], r["total"]) == (1, 2)
    assert r["mismatches"] == [{"block_uuid": "uuid-2", "block_id": "bloco-02",
                               "true": "unidade-02", "got": "unidade-99"}]
