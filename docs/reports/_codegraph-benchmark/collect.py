"""Collect equal-budget evidence without consulting gold.json."""
import ast
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
SNAP = BASE / 'snapshot'
CBM = Path.home() / '.local/bin/codebase-memory-mcp.exe'
ENV = dict(os.environ, PYTHONIOENCODING='utf-8', CBM_WORKERS='4', CBM_MEM_BUDGET_MB='2048')
PROJECT = 'codegraph-pilot-20260915'


def run(args, timeout=180):
    start = time.perf_counter()
    p = subprocess.run([str(a) for a in args], cwd=SNAP, env=ENV, capture_output=True, encoding='utf-8', errors='replace', timeout=timeout)
    return dict(command=[str(a) for a in args], seconds=time.perf_counter()-start,
                returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)


def cbm(tool, args):
    return run([CBM, 'cli', '--json', tool, json.dumps(args)], timeout=240)


def snippets(seeds, files, class_scope=None):
    out = []
    for rel in sorted(set(files)):
        path = SNAP / rel
        if not path.is_file() or path.suffix != '.py':
            continue
        text = path.read_text(encoding='utf-8-sig')
        lines = text.splitlines()
        matches = [i for i, line in enumerate(lines) if any(seed in line for seed in seeds)]
        selected = set()
        tree = ast.parse(text)
        if class_scope and not any(isinstance(n, ast.ClassDef) and n.name==class_scope for n in ast.walk(tree)):
            continue
        scopes = [n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
        for n in scopes:
            if n.name in seeds:
                selected.update(range(n.lineno-1,min(n.end_lineno,n.lineno+119)))
        for i in matches:
            selected.update(range(max(0,i-5),min(len(lines),i+9)))
            for n in scopes:
                if n.lineno <= i+1 <= n.end_lineno:
                    selected.add(n.lineno-1)
        if selected:
            out.append('\n'.join(f'{rel}:{i+1}: {lines[i]}' for i in sorted(selected)))
    return '\n\n'.join(out)


def graph_files(text):
    files=[p.replace('\\','/') for p in re.findall(r'src[/\\][\w./\\-]+\.py', text)]
    # CBM trace rows group symbols under dotted qualified names, without a file column.
    for qualified in re.findall(r'\bsrc\.[\w.]+', text):
        parts=qualified.rstrip('.').split('.')
        for size in range(len(parts),1,-1):
            rel='/'.join(parts[:size])+'.py'
            if (SNAP/rel).is_file():
                files.append(rel)
                break
    return files


def main():
    raw = BASE / 'raw'
    raw.mkdir(exist_ok=True)
    if not (BASE/'cbm-build.json').exists():
        result = cbm('index_repository', {'repo_path':str(SNAP), 'name':PROJECT, 'mode':'full'})
        (BASE/'cbm-build.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('CBM index:',result['stdout'][:1400],result['stderr'][-400:],flush=True)
        assert result['returncode']==0
    questions=json.loads((BASE/'questions.json').read_text(encoding='utf-8'))
    timings=[]
    for rep in range(3):
        for q in questions:
            outputs={}
            order=['baseline','graphify','cbm']
            order=order[rep:]+order[:rep]
            for arm in order:
                start=time.perf_counter()
                calls=[]
                if arm=='baseline':
                    calls.append(run(['rg','-n','-F',*[v for seed in q['seeds'] for v in ['-e',seed]],'src']))
                elif arm=='graphify':
                    for seed in q['seeds']:
                        calls.append(run([sys.executable,'-m','graphify','explain',seed,'--graph',SNAP/'graphify-out/graph.json']))
                    if q['category']=='path':
                        calls.append(run([sys.executable,'-m','graphify','path',q['seeds'][0],q['seeds'][-1],'--graph',SNAP/'graphify-out/graph.json']))
                else:
                    for seed in q['seeds']:
                        calls.append(cbm('search_graph',{'project':PROJECT,'name_pattern':'.*'+re.escape(seed)+'.*','include_connected':True,'limit':30}))
                        if q['category']!='location':
                            calls.append(cbm('trace_path',{'project':PROJECT,'function_name':seed,'direction':'both','depth':2,'limit':40,'include_evidence':True}))
                text='\n'.join(c['stdout'] for c in calls)
                source=snippets(q['seeds'],graph_files(text))
                outputs[arm]=(text,source,calls)
                timings.append(dict(rep=rep,id=q['id'],arm=arm,seconds=time.perf_counter()-start,calls=len(calls),raw_chars=len(text),source_chars=len(source)))
                (raw/f'{rep}-{q["id"]}-{arm}.json').write_text(json.dumps(calls,ensure_ascii=False,indent=2),encoding='utf-8')
            for arm in ['baseline','graphify','cbm','both']:
                if arm=='both':
                    g,s1,_=outputs['graphify']; c,s2,_=outputs['cbm']
                    text='GRAPHIFY\n'+g[:8000]+'\nCBM\n'+c[:8000]
                    source=snippets(q['seeds'],graph_files(g+'\n'+c))
                else:
                    text,source,_=outputs[arm]
                packet='DISCOVERY\n'+text[:16000]+'\nSOURCE VERIFICATION\n'+source[:16000]
                (raw/f'{rep}-{q["id"]}-{arm}.txt').write_text(packet,encoding='utf-8')
            print('collected',rep,q['id'],flush=True)
            (BASE/'retrieval-metrics.json').write_text(json.dumps(timings,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
