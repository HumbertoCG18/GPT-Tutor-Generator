import inspect
from src.builder.ops import pedagogical_regeneration as pr


def test_resolve_unit_block_tags_runs_before_attach_block_summary():
    src = inspect.getsource(pr.regenerate_pedagogical_files)
    i_resolve = src.find("resolve_unit_block_tags_fn(")
    i_attach = src.find("attach_block_summary_fields(")
    assert i_resolve != -1 and i_attach != -1
    assert i_resolve < i_attach, "funil deve rodar antes do attach (consenso D1 depende disso)"
