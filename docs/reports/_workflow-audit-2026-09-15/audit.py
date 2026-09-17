"""Read metadata and actual tool-call records; export no credentials or transcript text."""
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import tomllib
import yaml

BASE = Path(__file__).resolve().parent
HOME = Path.home()
REPO = BASE.parents[2]


def load(path):
    if not path.is_file():
        return {}
    text = path.read_text(encoding='utf-8-sig')
    return tomllib.loads(text) if path.suffix == '.toml' else json.loads(text)


def walk(root):
    seen = set()
    for current, dirs, files in os.walk(root, followlinks=True):
        real = os.path.normcase(os.path.realpath(current))
        if real in seen:
            dirs[:] = []
            continue
        seen.add(real)
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'sources']]
        yield Path(current), files


def main():
    codex = load(HOME / '.codex/config.toml')
    claude = load(HOME / '.claude/settings.json')
    agy = load(HOME / '.gemini/config/config.json')
    disabled = {os.path.normcase(str(Path(r['path']))) for r in codex.get('skills', {}).get('config', []) if r.get('enabled') is False}
    roots = []
    for rel in ['.agents/skills', '.codex/skills', '.claude/skills', '.gemini/skills',
                '.gemini/antigravity/skills', '.gemini/antigravity-cli/skills']:
        roots.append((HOME / rel, rel, 'local-discovery', ''))
    for product in ['.claude', '.codex']:
        registry = load(HOME / product / 'plugins/installed_plugins.json')
        if registry:
            for name, records in registry.get('plugins', {}).items():
                for r in records:
                    enabled = claude.get('enabledPlugins', {}).get(name, 'not-explicit')
                    roots.append((Path(r['installPath']), product + ':plugin:' + name, str(enabled), name.split('@')[0]))
        else:
            cache = HOME / product / 'plugins/cache'
            for market in cache.iterdir() if cache.exists() else []:
                for package in market.iterdir() if market.is_dir() else []:
                    for version in package.iterdir() if package.is_dir() else []:
                        if version.is_dir():
                            name = package.name + '@' + market.name
                            enabled = codex.get('plugins', {}).get(name, {}).get('enabled', 'not-explicit')
                            roots.append((version, product + ':plugin:' + name, str(enabled), package.name))
    for plugin in (HOME / '.gemini/config/plugins').iterdir():
        roots.append((plugin, 'agy:plugin:' + plugin.name,
                      str(agy.get('plugins', {}).get(plugin.name, {}).get('enabled', 'not-explicit')), plugin.name))
    # Workspace roots only: do not inspect arbitrary application data directories.
    projects = [p for p in REPO.parent.iterdir() if p.is_dir() and (p / '.git').exists()]
    for project in projects:
        for folder in ['.agents/skills', '.claude/skills', '.codex/skills', '.gemini/skills']:
            roots.append((project / folder, 'project:' + project.name + ':' + folder, 'local-discovery', ''))
    rows, seen = [], set()
    for root, origin, enabled, namespace in roots:
        for folder, files in walk(root):
            if 'SKILL.md' not in files:
                continue
            p = folder / 'SKILL.md'
            key = (str(p), origin)
            if key in seen:
                continue
            seen.add(key)
            raw = p.read_bytes()
            text = raw.decode('utf-8-sig', errors='replace')
            try:
                front = yaml.safe_load(text.split('---', 2)[1]) if text.startswith('---') else {}
            except (yaml.YAMLError, IndexError):
                front = {}
            front = front if isinstance(front, dict) else {}
            name = str(front.get('name', folder.name))
            desc = str(front.get('description', ''))
            override = claude.get('skillOverrides', {}).get((namespace + ':' if namespace else '') + name, '') if origin.startswith('.claude') else ''
            rows.append(dict(origin=origin, plugin_enabled=enabled, path=str(p), real_path=str(p.resolve()),
                             name=name, description_chars=len(desc), description=desc,
                             sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                             codex_disabled=os.path.normcase(str(p)) in disabled, claude_override=override,
                             disable_model_invocation=front.get('disable-model-invocation', False)))
    with (BASE / 'skills-inventory.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {}
    for origin in sorted({r['origin'] for r in rows}):
        group = [r for r in rows if r['origin'] == origin]
        summary[origin] = dict(files=len(group), description_chars=sum(r['description_chars'] for r in group),
                               plugin_enabled=group[0]['plugin_enabled'],
                               overrides=dict(collections.Counter(r['claude_override'] for r in group)))
    duplicates = collections.defaultdict(list)
    for r in rows:
        if ':plugin:' not in r['origin']:
            duplicates[r['name']].append({'path': r['path'], 'sha256': r['sha256'], 'codex_disabled': r['codex_disabled']})
    configs = {}
    for path in [HOME/'.claude/settings.json', HOME/'.codex/config.toml', HOME/'.gemini/config/config.json',
                 HOME/'.gemini/config/hooks.json', HOME/'.gemini/config/mcp_config.json',
                 REPO/'.claude/settings.local.json', REPO/'.claude/settings.json', REPO/'.codex/config.toml']:
        d = load(path)
        configs[str(path)] = {k:d[k] for k in ['enabledPlugins','skillOverrides','plugins','skills'] if k in d}
        configs[str(path)]['hook_events'] = list(d.get('hooks', {}))
        configs[str(path)]['mcp'] = {k:{'enabled':v.get('enabled',not v.get('disabled',False))} for k,v in d.get('mcp_servers',d.get('mcpServers',{})).items()}
    memory = HOME / '.codex/memories'
    report = dict(scope='personal skill roots, installed Claude registry, Codex cache (all versions), AGY config plugins, sibling Git repositories; installed != loaded',
                  projects=[str(p) for p in projects], summary=summary,
                  duplicate_names={k:v for k,v in duplicates.items() if len(v)>1}, configs=configs,
                  codex_memory_files=[{'name':str(p.relative_to(memory)), 'bytes':p.stat().st_size} for p in memory.rglob('*') if p.is_file()])
    (BASE / 'inventory-summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    print('Projects:',len(projects),'skill records:',len(rows),'memory files:',len(report['codex_memory_files']))


if __name__ == '__main__':
    main()
