"""Real-source mutation: replace exactly one call, then verify old/new edges."""
import json
import shutil
import time
from pathlib import Path
from graphify.extract import extract
from graphify.build import build
from collect import BASE, SNAP, cbm


def graphify_edges(root):
    start=time.perf_counter()
    data=extract(sorted((root/'src').rglob('*.py')),root=root,cache_root=root,max_workers=4)
    graph=build([data],directed=True,root=root)
    edges=[(graph.nodes[a].get('label'),graph.nodes[b].get('label')) for a,b,d in graph.edges(data=True)
           if 'unit_short_label' in a and d.get('relation')=='calls']
    return dict(seconds=time.perf_counter()-start,edges=edges)


def cbm_edges(project):
    return cbm('query_graph',{'project':project,'query':"MATCH (a)-[r:CALLS]->(b) WHERE a.name = 'unit_short_label' RETURN a.qualified_name, b.qualified_name"})


if __name__=='__main__':
    root=BASE/'mutation'
    assert not root.exists(), 'Do not overwrite mutation evidence'
    shutil.copytree(SNAP/'src',root/'src')
    (root/'.gitignore').write_text('graphify-out/\n')
    project='codegraph-update-20260915'
    before_g=graphify_edges(root)
    before_index=cbm('index_repository',{'repo_path':str(root),'name':project,'mode':'full'})
    before_c=cbm_edges(project)
    p=root/'src/builder/timeline/unit_labels.py'
    text=p.read_text(encoding='utf-8')
    assert text.count('n = unit_number(s)')==1
    p.write_text(text.replace('n = unit_number(s)','n = benchmark_new_target(s)')+'\n\ndef benchmark_new_target(slug: str) -> int:\n    return 1\n',encoding='utf-8')
    after_g=graphify_edges(root)
    after_index=cbm('index_repository',{'repo_path':str(root),'name':project,'mode':'full'})
    after_c=cbm_edges(project)
    report=dict(before_graphify=before_g,after_graphify=after_g,before_cbm_index=before_index,after_cbm_index=after_index,before_cbm=before_c,after_cbm=after_c,
                mode='Explicit refresh; automatic watcher latency not measured')
    (BASE/'update-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(graphify_before=before_g,graphify_after=after_g,cbm_before=before_c['stdout'],cbm_after=after_c['stdout']),indent=2))
