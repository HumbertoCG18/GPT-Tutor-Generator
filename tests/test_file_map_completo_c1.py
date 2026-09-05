"""C1 TRAVESSIA item 1 — FILE_MAP completo e magro.

Medido em 04-05/09 (tracker §C0 ITEM 12): o FILE_MAP era cortado em 12 KB pela cauda e citava CG 26/93, IA 22/59,
MF 31/66; na travessia do CG com LLM, 8/8 erros tinham o alvo fora do corte e 7/7 acertos dentro. Cada material ocupava
2 linhas (tabela ~250 chars + "↳ rastreabilidade" ~230). Projecao nos 8 tutores: sem clamp 5,5-42,5 KB; magro 3-21 KB.
Aqui: (1) todos os materiais aparecem; (2) rastreabilidade sai para FILE_MAP_TRACE.md; (3) titulo = moodle_label
quando existe (o rebuild grava title = nome do arquivo: "Vis3d", "PlaneSweep"); (4) Secoes <= 3 headers / 80 chars;
(5) clamp 80 KB com aviso quando ainda cortar.
"""
from src.builder import engine as E

META = {"course_name": "Computação Gráfica"}


def file_map_md(*a, **k):
    return E.file_map_md(*a, **k)


def file_map_trace_md(*a, **k):
    return E.file_map_trace_md(*a, **k)


def _entry(i, title=None, label=None, md="", raw=True, tags=""):
    e = {"title": title or f"Material{i:03d}", "category": "material-de-aula", "tags": tags,
         "base_markdown": f"content/m{i:03d}.md", "raw_target": f"raw/pdfs/m{i:03d}.pdf" if raw else "",
         "_markdown_text_for_tests": md or f"# M{i}\n\n## Introdução ao tema {i}\n\ntexto"}
    if label:
        e["moodle_label"] = label
    return e


def _rows(md):
    return [l for l in md.splitlines() if l.startswith("| ") and l.split("|")[1].strip().isdigit()]


def _cell(row, idx):
    return row.split("|")[idx].strip()


def test_file_map_lista_todos_os_materiais_sem_corte():
    entries = [_entry(i) for i in range(1, 121)]          # 120 > os ~23 que cabiam em 12 KB
    md = file_map_md(META, entries)
    assert len(_rows(md)) == 120
    assert "Conteúdo truncado" not in md


def test_rastreabilidade_sai_do_file_map_e_vai_para_o_trace():
    entries = [_entry(1, tags="unidade-01")]
    md = file_map_md(META, entries)
    assert "rastreabilidade" not in md
    assert "raw/pdfs/m001.pdf" not in md
    trace = file_map_trace_md(META, entries)
    assert "FILE_MAP_TRACE" in trace
    assert "raw: `raw/pdfs/m001.pdf`" in trace and "tags: `unidade-01`" in trace
    assert "Material001" in trace                        # a linha do trace identifica o material


def test_titulo_usa_moodle_label_quando_existe_e_title_como_fallback():
    entries = [_entry(1, title="Vis3d", label="Visualização 3D - Projeção"), _entry(2, title="Recorte")]
    rows = _rows(file_map_md(META, entries))
    assert _cell(rows[0], 2) == "Visualização 3D - Projeção"
    assert _cell(rows[1], 2) == "Recorte"


def test_titulo_aceita_moodle_label_em_dict():
    rows = _rows(file_map_md(META, [_entry(1, title="Iluminacao", label={"text": "Página sobre Síntese de Imagens"})]))
    assert _cell(rows[0], 2) == "Página sobre Síntese de Imagens"


def test_secoes_limitadas_a_tres_headers_e_oitenta_chars(tmp_path):
    # a coluna Secoes le o markdown REAL do repo (path), nao o texto de teste: escreve o arquivo
    md_text = "# Doc\n\n" + "\n\n".join(f"## Seção número {k} com um título bem comprido para caber pouco" for k in range(1, 6))
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "m001.md").write_text(md_text, encoding="utf-8")
    rows = _rows(file_map_md({**META, "_repo_root": tmp_path}, [_entry(1, raw=False)]))
    assert rows, "entry com markdown existente tem de ser listada"
    secoes = _cell(rows[0], 7)
    assert secoes, "Secoes vazia: o teste nao esta lendo o markdown"
    assert secoes.count("Seção número") <= 3
    assert len(secoes) <= 80


def test_clamp_sobe_para_80kb_e_avisa_quando_corta():
    ok = file_map_md(META, [_entry(i) for i in range(1, 301)])       # ~45 KB: cabe
    assert len(_rows(ok)) == 300 and "Conteúdo truncado" not in ok
    cut = file_map_md(META, [_entry(i) for i in range(1, 1201)])     # ~180 KB: corta e avisa
    assert "Conteúdo truncado" in cut and len(cut) <= 80_000 + 200
