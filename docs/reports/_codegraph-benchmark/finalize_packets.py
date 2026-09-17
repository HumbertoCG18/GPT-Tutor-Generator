"""Resolve explicit ambiguity hints and unwrap MCP text before equal-budget synthesis."""
import json
import re
import sys
from collect import BASE, SNAP, run, snippets, graph_files


def unwrap(text):
    try:
        data=json.loads(text)
        if isinstance(data,dict) and 'content' in data:
            return '\n'.join(c.get('text','') for c in data['content'])
    except ValueError:
        pass
    return text


if __name__=='__main__':
    questions=json.loads((BASE/'questions.json').read_text(encoding='utf-8'))
    metrics=[]
    for rep in range(3):
        for q in questions:
            results={}
            for arm in ['baseline','graphify','cbm']:
                p=BASE/'raw'/f'{rep}-{q["id"]}-{arm}.json'
                final_path=BASE/'raw'/f'{rep}-{q["id"]}-{arm}-final.json'
                already_final=final_path.exists()
                calls=json.loads((final_path if already_final else p).read_text(encoding='utf-8'))
                if arm=='graphify' and not already_final:
                    ids=[]
                    for c in calls:
                        if 'Ambiguous:' in c['stdout']:
                            ids+=re.findall(r'id: (\S+)',c['stdout'])
                    if 'MaintenancePanel' in q['question']:
                        ids=[i for i in ids if 'maintenance_panel' in i or 'sweep_orphans' in i]
                    for id_ in sorted(set(ids)):
                        calls.append(run([sys.executable,'-m','graphify','explain',id_,'--graph',SNAP/'graphify-out/graph.json']))
                final_path.write_text(json.dumps(calls,ensure_ascii=False,indent=2),encoding='utf-8')
                text='\n'.join(unwrap(c['stdout']) for c in calls)
                results[arm]=(text,calls)
            for arm in ['baseline','graphify','cbm','both']:
                if arm=='both':
                    g,gc=results['graphify'];c,cc=results['cbm']
                    text='GRAPHIFY\n'+g[:8000]+'\nCBM\n'+c[:8000]
                    files=graph_files(g+'\n'+c);calls=gc+cc
                else:
                    text,calls=results[arm];files=graph_files(text)
                class_scope='MaintenancePanel' if q['question'].startswith(('Em MaintenancePanel.', 'Dentro de MaintenancePanel,')) else None
                explicit_files=re.findall(r'\b\w+\.py\b',q['question'])
                if explicit_files:
                    files=[f for f in files if f.replace('\\','/').split('/')[-1] in explicit_files]
                source=snippets(q['seeds'],files,class_scope)
                packet='DISCOVERY\n'+text[:16000]+'\nSOURCE VERIFICATION\n'+source[:16000]
                packet_path=BASE/'raw'/f'{rep}-{q["id"]}-{arm}.txt'
                if packet_path.exists() and packet_path.read_text(encoding='utf-8')!=packet:
                    version=1
                    backup=packet_path.with_suffix(f'.v{version}.txt')
                    while backup.exists():
                        version+=1
                        backup=packet_path.with_suffix(f'.v{version}.txt')
                    backup.write_bytes(packet_path.read_bytes())
                packet_path.write_text(packet,encoding='utf-8')
                metrics.append(dict(rep=rep,id=q['id'],arm=arm,query_seconds=sum(c['seconds'] for c in calls),calls=len(calls),packet_chars=len(packet),discovery_truncated=len(text)>16000,source_truncated=len(source)>16000))
    (BASE/'packet-metrics.json').write_text(json.dumps(metrics,indent=2))
    print('144 evidence packets finalized; answer key not accessed')
