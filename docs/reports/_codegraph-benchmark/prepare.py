"""Freeze real Python sources and a source-verified pilot answer key before indexing."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
SNAP = BASE / 'snapshot'


def main():
    assert not (BASE / 'gold.json').exists(), 'Snapshot already frozen'
    records = {}
    for source in sorted((ROOT / 'src').rglob('*.py')):
        rel = source.relative_to(ROOT)
        data = source.read_bytes()
        target = SNAP / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records[rel.as_posix()] = hashlib.sha256(data).hexdigest()
    (SNAP / '.gitignore').write_text('graphify-out/\n.graphify_cache/\n', encoding='utf-8')
    manifest = {'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'scope': 'current working-tree src/**/*.py, including untracked files; no docs/tests',
                'files': records}
    (BASE / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    # Each case has a bounded scope; impacts mean syntactic callers/references, not runtime proof.
    cases = [
      ('L1','location','Onde está definida unit_short_label?', ['unit_short_label'], ['src/builder/timeline/unit_labels.py:unit_short_label']),
      ('L2','location','Onde está definida load_docling_python_api?', ['load_docling_python_api'], ['src/builder/runtime/backend_runtime.py:load_docling_python_api']),
      ('L3','location','Onde está definida MaintenancePanel._detect_orphans?', ['_detect_orphans'], ['src/ui/maintenance_panel.py:MaintenancePanel._detect_orphans']),
      ('C1','calls','Em unit_labels.py, qual função chama diretamente unit_number?', ['unit_number'], ['src/builder/timeline/unit_labels.py:unit_short_label']),
      ('C2','calls','Em backend_runtime.py, qual função chama diretamente build_page_chunks?', ['build_page_chunks'], ['src/builder/runtime/backend_runtime.py:build_marker_page_chunks']),
      ('C3','calls','Em MaintenancePanel._build_ui, quais métodos são registrados como command dos dois botões? São callbacks, não chamadas imediatas.', ['MaintenancePanel','_build_ui'], ['src/ui/maintenance_panel.py:MaintenancePanel.refresh','src/ui/maintenance_panel.py:MaintenancePanel._on_sweep']),
      ('P1','path','Liste em ordem a cadeia de chamadas de MarkerCLIBackend._run_chunked_marker até build_page_chunks, resolvendo o alias importado.', ['_run_chunked_marker','build_marker_page_chunks','build_page_chunks'], ['src/builder/engine.py:MarkerCLIBackend._run_chunked_marker','src/builder/runtime/backend_runtime.py:build_marker_page_chunks','src/builder/runtime/backend_runtime.py:build_page_chunks']),
      ('P2','path','Liste em ordem o caminho de build_temporal_context_rows até unit_number via formatação do rótulo.', ['build_temporal_context_rows','unit_short_label','unit_number'], ['src/builder/artifacts/temporal_context.py:build_temporal_context_rows','src/builder/timeline/unit_labels.py:unit_short_label','src/builder/timeline/unit_labels.py:unit_number']),
      ('P3','path','Liste em ordem a cadeia iniciada em MaintenancePanel._on_sweep até a implementação sweep_orphans de lifecycle_ops. Inclua o worker aninhado e a fachada RepoBuilder; explicite a hipótese de tipo do builder.', ['_on_sweep','sweep_orphans'], ['src/ui/maintenance_panel.py:MaintenancePanel._on_sweep','src/ui/maintenance_panel.py:MaintenancePanel._on_sweep._worker','src/builder/engine.py:RepoBuilder.sweep_orphans','src/builder/ops/lifecycle_ops.py:sweep_orphans']),
      ('I1','impact','Quais funções/métodos de src chamam diretamente unit_short_label, inclusive pelo alias _unit_short_label? Não inclua transitivos ou imports sem chamada.', ['unit_short_label','_unit_short_label'], ['src/builder/artifacts/temporal_context.py:build_temporal_context_rows','src/builder/artifacts/temporal_context.py:build_unit_legend','src/ui/timeline_dashboard.py:TimelineDashboardView._populate']),
      ('I2','impact','Quais módulos externos load_docling_python_api carrega via importlib.import_module? Liste os cinco nomes completos; não afirme que estão instalados.', ['load_docling_python_api','import_module'], ['docling.document_converter','docling.datamodel.pipeline_options','docling.datamodel.base_models','docling.datamodel.accelerator_options','docling.datamodel.settings']),
      ('I3','impact','Dentro de MaintenancePanel, qual método chama diretamente _detect_orphans, e quais dois métodos registram/invocam esse consumidor (inclua o callback aninhado)? Liste consumidor primeiro.', ['_detect_orphans','refresh'], ['src/ui/maintenance_panel.py:MaintenancePanel.refresh','src/ui/maintenance_panel.py:MaintenancePanel._build_ui','src/ui/maintenance_panel.py:MaintenancePanel._on_sweep._worker._done']),
    ]
    definitions = {}
    def visit(node, prefix, file):
        for child in ast.iter_child_nodes(node):
            name = prefix
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                name = '.'.join(filter(None, [prefix, child.name]))
                definitions[file + ':' + name] = child.lineno
            visit(child, name, file)
    for rel in records:
        visit(ast.parse((SNAP / rel).read_text(encoding='utf-8-sig')), '', rel)
    questions, gold = [], []
    for id_, category, question, seeds, answers in cases:
        questions.append(dict(id=id_, category=category, question=question, seeds=seeds))
        evidence = []
        for answer in answers:
            if ':' in answer:
                assert answer in definitions, answer
                evidence.append(dict(symbol=answer, definition_line=definitions[answer]))
        gold.append(dict(id=id_, expected=answers, evidence=evidence))
    (BASE / 'questions.json').write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding='utf-8')
    (BASE / 'gold.json').write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Frozen {len(records)} Python sources; {len(cases)} questions; all answer symbols verified with AST')


if __name__ == '__main__':
    main()
