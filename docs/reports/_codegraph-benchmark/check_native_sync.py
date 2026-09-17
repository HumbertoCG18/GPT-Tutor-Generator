"""Exercise installed Git hooks and the CBM watcher on a copy of real source."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ListRootsResult, Root

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
RUN = BASE / 'native-sync' / time.strftime('%Y%m%d-%H%M%S')
PROJECT = 'native-sync-' + RUN.name
EXE = str(Path.home() / '.local/bin/codebase-memory-mcp.exe')
ENV = dict(os.environ, GRAPHIFY_MAX_WORKERS='1', PYTHONHASHSEED='0',
           CBM_WORKERS='4', CBM_MEM_BUDGET_MB='2048')
RESULT = {'project': PROJECT, 'root': str(RUN), 'events': []}


def git(*args, skip=False):
    env = dict(ENV, GRAPHIFY_SKIP_HOOK='1') if skip else ENV
    return subprocess.run(['git', *args], cwd=RUN, env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


def graph_names():
    try:
        data = json.loads((RUN / 'graphify-out/graph.json').read_text('utf-8'))
        return {n.get('label', '').removesuffix('()') for n in data['nodes']}
    except (OSError, ValueError):
        return set()


async def main():
    RUN.mkdir(parents=True)
    git('init', '-b', 'base')
    git('config', 'user.email', 'native-sync@example.invalid')
    git('config', 'user.name', 'Native sync test')
    for name in ['.graphifyignore', '.cbmignore']:
        shutil.copy2(REPO / name, RUN / name)
    (RUN / '.gitignore').write_text('graphify-out/\n.codebase-memory/\n', encoding='utf-8')
    source = REPO / 'src/builder/timeline/unit_labels.py'
    text = source.read_text('utf-8')
    RESULT['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    (RUN / 'unit_labels.py').write_text(text, encoding='utf-8')
    # Keep genuine source in the repository when the target file is deleted.
    retained = text
    for symbol in ['unit_number', 'unit_short_label', 'unit_name_from_slug']:
        retained = retained.replace(symbol, 'stable_' + symbol)
    (RUN / 'retained_labels.py').write_text(retained, encoding='utf-8')
    for folder in ['graphify-out', '.codebase-memory', '.cache', '__pycache__',
                   'docs/reports/_codegraph-benchmark', 'docs/vendor']:
        target = RUN / folder / 'ignored_probe.py'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('def excluded_graph_probe():\n    return 1\n', encoding='utf-8')
    git('add', '.')
    git('commit', '-m', 'baseline', skip=True)
    for hook in ['post-commit', 'post-checkout']:
        shutil.copy2(REPO / '.git/hooks' / hook, RUN / '.git/hooks' / hook)
    build = 'from pathlib import Path; from graphify.watch import _rebuild_code; assert _rebuild_code(Path.cwd())'
    p = subprocess.run([sys.executable, '-c', build], cwd=RUN, env=ENV,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    (RUN / 'initial-graphify.log').write_text(p.stdout + p.stderr, encoding='utf-8')
    assert p.returncode == 0, p.stderr
    assert 'unit_short_label' in graph_names(), graph_names()
    assert 'excluded_graph_probe' not in graph_names()
    (RUN / '.git/info/exclude').write_text('*.log\n', encoding='utf-8')
    params = StdioServerParameters(command=EXE, env=ENV, cwd=str(RUN))
    async def roots(*args):
        return ListRootsResult(roots=[Root(uri=RUN.as_uri(), name=PROJECT)])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w, list_roots_callback=roots) as session:
            await session.initialize()

            async def call(name, args):
                response = await session.call_tool(name, args)
                assert not response.is_error, response
                return '\n'.join(c.text for c in response.content if hasattr(c, 'text'))

            result = await call('index_repository', {'repo_path': str(RUN),
                                                    'mode': 'full', 'persistence': False})
            RESULT['initial_index'] = result
            project = json.loads(result)['project']
            RESULT['project'] = project

            async def cbm_names():
                raw = await call('query_graph', {'project': project,
                    'query': 'MATCH (n:Function) RETURN n.name'})
                assert raw.startswith('rows:'), raw
                return {line.strip() for line in raw.splitlines() if line.startswith('  ')}

            before = await cbm_names()
            assert 'unit_short_label' in before and 'excluded_graph_probe' not in before, before
            await asyncio.sleep(7)  # Allow the native watcher's initial baseline poll.

            async def wait_for(event, present, absent, timeout=100):
                start = time.monotonic()
                times = {}
                while time.monotonic() - start < timeout:
                    gn = graph_names()
                    cn = await cbm_names()
                    if all(n in gn for n in present) and all(n not in gn for n in absent):
                        times.setdefault('graphify_seconds', round(time.monotonic() - start, 2))
                    if all(n in cn for n in present) and all(n not in cn for n in absent):
                        times.setdefault('cbm_seconds', round(time.monotonic() - start, 2))
                    if len(times) == 2:
                        break
                    await asyncio.sleep(2)
                row = {'event': event, **times, 'passed': len(times) == 2}
                RESULT['events'].append(row)
                print(json.dumps(row), flush=True)
                (RUN / 'result.json').write_text(json.dumps(RESULT, indent=2), encoding='utf-8')
                (BASE / 'native-sync-results.json').write_text(json.dumps(RESULT, indent=2), encoding='utf-8')
                assert row['passed'], {'event': event, 'times': times, 'graphify': sorted(gn), 'cbm': cn}

            # Rename a real function and its call; native post-commit refresh only.
            (RUN / 'unit_labels.py').write_text(text.replace('unit_number', 'renamed_unit_number'), encoding='utf-8')
            git('add', 'unit_labels.py')
            git('commit', '-m', 'rename function')
            await wait_for('edit_commit', ['renamed_unit_number'], ['unit_number'])
            git('branch', 'edited')
            # Delete the copied source; no recursive delete, production is untouched.
            (RUN / 'unit_labels.py').unlink()
            git('add', 'unit_labels.py')
            git('commit', '-m', 'delete source')
            await wait_for('delete_commit', [], ['renamed_unit_number', 'unit_short_label'])
            git('checkout', 'edited')
            await wait_for('branch_checkout', ['renamed_unit_number', 'unit_short_label'], ['unit_number'])


if __name__ == '__main__':
    asyncio.run(main())
