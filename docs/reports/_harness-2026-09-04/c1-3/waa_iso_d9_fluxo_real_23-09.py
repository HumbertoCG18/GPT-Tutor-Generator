"""Conferência isolada (23/09): flag efetiva do motor D9 e resolvedor usado no FLUXO REAL da UI.

Ambiente isolado: APPDATA temporário (subjects.json novo), cópias do TCC em pasta temporária, rede/Gemini/Datalab
bloqueados. Usa as classes e funções reais: SubjectManagerDialog (_new/_on_select/_save), SubjectStore,
_build_options_from_config (o que a UI passa ao RepoBuilder) e RepoBuilder.incremental_build (botão Reprocessar).
Únicas substituições: grab_set e messagebox.showinfo do diálogo (janelas modais), e contadores que DELEGAM às
funções reais apply_anchor_engine / apply_concept_resolver. Nada no repositório é alterado.
"""
import json
import os
import shutil
import socket
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[4]
T = Path(tempfile.gettempdir()) / "iso_d9_fluxo_real"   # pasta temporaria do sistema; apagada e recriada a cada execucao
if T.exists():
    shutil.rmtree(T)
(T / "appdata").mkdir(parents=True)
os.environ["APPDATA"] = str(T / "appdata")
sys.path.insert(0, str(REPO))


def _bloqueado(*a, **k):
    raise RuntimeError("bloqueado (tripwire)")


socket.socket.connect = _bloqueado
socket.create_connection = _bloqueado
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None
_gc.GeminiClient.__init__ = _bloqueado
from src.builder.runtime import datalab_client  # noqa: E402
from src.builder import engine as engine_module  # noqa: E402
datalab_client.convert_document_to_markdown = _bloqueado
engine_module.convert_document_to_markdown = _bloqueado

from src.utils.helpers import get_app_data_dir  # noqa: E402
assert str(get_app_data_dir()).startswith(str(T / "appdata")), get_app_data_dir()
import tkinter as tk  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402
import src.ui.dialogs as dialogs  # noqa: E402
from src.ui.theme import ThemeManager  # noqa: E402
from src.ui.app import _build_options_from_config  # noqa: E402
from src.builder.engine import RepoBuilder  # noqa: E402
import src.builder.routing.motor.apply as motor_apply  # noqa: E402
import src.builder.routing.resolver_apply as resolver_apply  # noqa: E402

CHAMADAS = {"apply_anchor_engine": 0, "apply_concept_resolver": 0}
_orig_anchor, _orig_concept = motor_apply.apply_anchor_engine, resolver_apply.apply_concept_resolver


def _conta_anchor(*a, **k):
    CHAMADAS["apply_anchor_engine"] += 1
    return _orig_anchor(*a, **k)


def _conta_concept(*a, **k):
    CHAMADAS["apply_concept_resolver"] += 1
    return _orig_concept(*a, **k)


motor_apply.apply_anchor_engine = _conta_anchor
resolver_apply.apply_concept_resolver = _conta_concept
dialogs.SubjectManagerDialog.grab_set = lambda self: None
POPUPS = []
dialogs.messagebox.showinfo = lambda *a, **k: POPUPS.append(a[1] if len(a) > 1 else k)

ORIG = REPO / ".frzero/pacote_fontes_15-09/TCC-Tutor"
perfil_in = json.loads((ORIG / "_inputs_15-09.json").read_text(encoding="utf-8"))["profile_input"]


def copia(nome):
    dst = T / nome / "TCC-Tutor"
    shutil.copytree(ORIG, dst)
    m = json.loads((dst / "manifest.json").read_text(encoding="utf-8"))
    for e in m["entries"]:
        for k in motor_apply.TEMPORAL_KEYS:
            e.pop(k, None)
    (dst / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst


def cria_pelo_dialogo(root, nome, repo_root):
    store = SubjectStore()
    dlg = dialogs.SubjectManagerDialog(root, store, ThemeManager(), config_obj={})
    dlg.withdraw()
    dlg._new()
    dlg._vars["name"].set(nome)
    dlg._vars["repo_root"].set(str(repo_root))
    dlg._syllabus_text.insert("1.0", str(perfil_in.get("syllabus") or ""))
    dlg._teaching_plan_text.insert("1.0", str(perfil_in.get("teaching_plan") or ""))
    dlg._save()
    dlg.destroy()


def edita_pelo_dialogo(root, nome):
    store = SubjectStore()
    dlg = dialogs.SubjectManagerDialog(root, store, ThemeManager(), config_obj={})
    dlg.withdraw()
    idx = list(dlg._listbox.get(0, "end")).index(nome)
    dlg._listbox.selection_set(idx)
    dlg._on_select()
    dlg._save()
    dlg.destroy()


def roda_ui(nome, repo):
    sp = SubjectStore().get(nome)
    opts = _build_options_from_config("auto", "por", {}, subject=sp)
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    antes = sum(1 for e in m["entries"] if e.get("temporal_block_id"))
    for k in CHAMADAS:
        CHAMADAS[k] = 0
    t0 = time.time()
    RepoBuilder(root_dir=repo, course_meta=m.get("course", {}), entries=[], options=opts,
                subject_profile=sp).incremental_build()
    m2 = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ents = [e for e in m2["entries"] if e.get("category")]
    razoes = [r for e in ents for r in (e.get("unit_match_reasons") or []) if "bloco" in str(r)]
    return {"feature_flags_do_perfil": sp.feature_flags,
            "use_anchor_engine_nas_opcoes": opts.get("use_anchor_engine", "(ausente → False no código)"),
            "use_concept_resolver_nas_opcoes": opts.get("use_concept_resolver", "(ausente → True no código)"),
            "chamadas": dict(CHAMADAS), "materiais": len(ents), "temporal_block_id_antes": antes,
            "temporal_block_id_depois": sum(1 for e in ents if e.get("temporal_block_id")),
            "computed_block_id_depois": sum(1 for e in ents if e.get("computed_block_id")),
            "razoes_de_unidade_por_bloco": len(razoes), "opcoes_gravadas_no_manifest": {
                k: v for k, v in (m2.get("options") or {}).items() if k in ("use_anchor_engine", "use_llm_voter", "compile_vocabulary")},
            "segundos": round(time.time() - t0, 1)}


root = tk.Tk()
root.withdraw()
res = {}
repo_a, repo_b = copia("a_sem_flag"), copia("b_com_flag")

# 1) disciplina nova criada pelo diálogo real
cria_pelo_dialogo(root, "ISO TCC criada pela UI", repo_a)
res["1_criada_pela_ui"] = roda_ui("ISO TCC criada pela UI", repo_a)

# 2) controle: mesma criação + flag gravada como faz scripts/build_course.py:181
cria_pelo_dialogo(root, "ISO TCC com flag", repo_b)
st = SubjectStore()
sp = st.get("ISO TCC com flag")
sp.feature_flags = {"use_anchor_engine": True}
st.add(sp)
res["2_com_flag_do_build_course"] = roda_ui("ISO TCC com flag", repo_b)

# 3) editar e salvar a matéria com flag pelo diálogo real
edita_pelo_dialogo(root, "ISO TCC com flag")
res["3_flags_depois_de_salvar_no_dialogo"] = SubjectStore().get("ISO TCC com flag").feature_flags
res["popups_registrados"] = POPUPS
root.destroy()
print(json.dumps(res, ensure_ascii=False, indent=1))
(T / "resultado.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
