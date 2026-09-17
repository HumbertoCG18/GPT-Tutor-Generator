import hashlib
import json
import tomllib
from pathlib import Path
from collect import BASE, SNAP, graph_files
from score import grade


def main():
    manifest=json.loads((BASE/'manifest.json').read_text())
    assert len(manifest['files'])==130
    for file,digest in manifest['files'].items():
        assert hashlib.sha256((SNAP/file).read_bytes()).hexdigest()==digest,file
    assert 'src/ui/maintenance_panel.py' in graph_files('src/ui/maintenance_panel.py:L77')
    assert 'src/ui/timeline_dashboard.py' in graph_files('project.src.ui.timeline_dashboard.TimelineDashboardView:')
    assert grade(['a'],['b'])['fp']==1
    assert not grade(['a','b'],['b','a'],True)['exact']
    scores=json.loads((BASE/'scores.json').read_text(encoding='utf-8'))
    assert len(scores)==144 and all(r['valid'] for r in scores)
    for row in scores:
        ident=f'{row["rep"]}-{row["id"]}-{row["arm"]}'
        data=json.loads((BASE/'answers'/f'{ident}.json').read_text(encoding='utf-8'))
        assert hashlib.sha256((BASE/'raw'/f'{ident}.txt').read_text(encoding='utf-8').encode()).hexdigest()==data['evidence_sha256']
    update=json.loads((BASE/'update-results.json').read_text())
    assert 'unit_number()' in str(update['before_graphify']['edges'])
    assert 'unit_number()' not in str(update['after_graphify']['edges'])
    assert 'benchmark_new_target()' in str(update['after_graphify']['edges'])
    assert '.unit_number' in update['before_cbm']['stdout']
    assert '.unit_number' not in update['after_cbm']['stdout']
    assert '.benchmark_new_target' in update['after_cbm']['stdout']
    config=tomllib.loads((Path.home()/'.codex/config.toml').read_text(encoding='utf-8-sig'))
    entry=config['mcp_servers']['codebase-memory-mcp']
    assert entry.get('enabled',True)
    executable=Path(entry['command'])
    assert executable.is_file()
    assert hashlib.sha256(executable.read_bytes()).digest()==hashlib.sha256((BASE/'tools/cbm-v0.10.8/codebase-memory-mcp.exe').read_bytes()).digest()
    status=dict(command=entry['command'],enabled=entry.get('enabled',True),graphify_mcp_enabled=config['mcp_servers']['graphify'].get('enabled',True))
    (BASE/'installed-config.json').write_text(json.dumps(status,indent=2))
    print('PASS: frozen corpus, dotted/slash paths, grader checks, 144 current responses, index updates, installed binary and config')


if __name__=='__main__':main()
