"""#65: matéria nova (diálogo e importador do Moodle) nasce com o D9 explícito no perfil, sem recursos opcionais.

Perfis existentes, valores False, default de código, pinos e fallback não mudam. O processamento cru de uma
matéria nova não tenta rede.
"""
import socket

from src.builder.ops import assignment_run as ar
from src.builder.ops import pedagogical_regeneration as pr
from src.models.core import NEW_SUBJECT_FEATURE_FLAGS, SubjectProfile
from src.ui.app import _build_options_from_config

OPCIONAIS = ("use_llm_voter", "compile_vocabulary", "enable_material_residual")


class _Store:
    def __init__(self, *profiles):
        self.data = {p.name: p for p in profiles}

    def names(self):
        return list(self.data.keys())

    def get(self, name):
        return self.data.get(name)

    def add(self, profile):
        self.data[profile.name] = profile


class _Client:
    def get_course_contents(self, cid):
        return []


def test_constante_liga_so_o_d9():
    assert NEW_SUBJECT_FEATURE_FLAGS == {"use_anchor_engine": True}


def test_default_de_codigo_do_d9_continua_desligado():
    assert ar.FLAG_DEFAULTS["use_anchor_engine"] is False
    assert ar.new_run({})["effective"]["use_anchor_engine"] is False


def test_importador_cria_materia_nova_so_com_d9(tmp_path):
    from src.builder.sources.moodle import import_moodle_courses

    store = _Store()
    import_moodle_courses([{"id": 1, "fullname": "X - Métodos Formais - Turma 031 - 2026/1 - Prof. J"}],
                          tmp_path / "Moodle", store, _Client())
    sp = store.get("Métodos Formais")
    assert sp.feature_flags == {"use_anchor_engine": True}
    assert sp.feature_flags is not NEW_SUBJECT_FEATURE_FLAGS


def test_importador_nao_migra_materia_existente(tmp_path):
    from src.builder.sources.moodle import import_moodle_courses

    por_id = SubjectProfile(name="Métodos Formais", slug="metodos-formais", moodle_course_id="1", feature_flags={})
    por_slug = SubjectProfile(name="SO", slug="so", feature_flags={"use_anchor_engine": False})
    store = _Store(por_id, por_slug)
    import_moodle_courses([{"id": 1, "fullname": "X - Métodos Formais - Turma 031 - 2026/1 - Prof. J"},
                           {"id": 2, "fullname": "Y - SO - Turma 010 - 2026/1 - Prof. K"}],
                          tmp_path / "Moodle", store, _Client())
    assert store.get("Métodos Formais").feature_flags == {}
    assert store.get("SO").feature_flags == {"use_anchor_engine": False}


def test_configuracao_efetiva_da_materia_nova():
    nova = SubjectProfile(name="Nova", feature_flags=dict(NEW_SUBJECT_FEATURE_FLAGS))
    opts = _build_options_from_config("auto", "por", {}, subject=nova)
    assert opts["use_anchor_engine"] is True
    assert not any(k in opts for k in OPCIONAIS)
    efetivo = ar.new_run(opts)["effective"]
    assert efetivo["use_anchor_engine"] is True and efetivo["use_concept_resolver"] is True
    assert not any(efetivo[k] for k in OPCIONAIS)


def test_processamento_cru_da_materia_nova_nao_tenta_rede(tmp_path, monkeypatch):
    """Escopo: regeneração de matéria nova com as options derivadas do perfil. O D9 é chamado e as camadas opcionais
    não resolvem cliente Gemini nem abrem socket/DNS. Sem cronograma o D9 não decide bloco aqui; a decisão efetiva
    sem rede está no reprodutor isolado c1-3/waa_iso_d9_fluxo_real_23-09.py (26/27 com rede bloqueada)."""
    from src.builder import engine as engine_mod
    from src.models.core import StudentProfile

    tentativas = []

    def _tripwire(*a, **k):
        tentativas.append(a[1:] if len(a) > 1 else a)
        raise OSError("rede bloqueada no teste")

    monkeypatch.setattr(socket.socket, "connect", _tripwire)
    monkeypatch.setattr(socket.socket, "connect_ex", _tripwire)
    monkeypatch.setattr(socket, "create_connection", _tripwire)
    monkeypatch.setattr(socket, "getaddrinfo", _tripwire)
    gemini = []
    monkeypatch.setattr(pr, "_resolve_gemini_client", lambda builder: gemini.append(1))

    nova = SubjectProfile(name="Nova", slug="nova", feature_flags=dict(NEW_SUBJECT_FEATURE_FLAGS))
    repo = tmp_path / "repo"
    builder = engine_mod.RepoBuilder(
        repo, {"course_name": "Nova", "course_slug": "nova", "semester": "2026/1", "professor": "P",
               "institution": "PUCRS"},
        [], _build_options_from_config("auto", "por", {}, subject=nova),
        student_profile=StudentProfile(), subject_profile=nova,
    )
    builder._create_structure()
    (repo / "content" / "curated" / "item.md").write_text("# Exercicios\n", encoding="utf-8")
    manifest = {"entries": [{"id": "item", "title": "item", "category": "listas", "file_type": "pdf",
                             "source_path": "raw/lista.pdf", "base_markdown": "content/curated/item.md", "tags": ""}]}
    builder._regenerate_pedagogical_files(manifest)

    run = manifest["assignment_run"]
    assert tentativas == [] and gemini == []
    assert run["executed"]["use_anchor_engine"] is True
    assert run["fallback"] == {}
    assert not any(run["executed"][k] for k in OPCIONAIS)
