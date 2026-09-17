"""Deterministic scoring against the frozen key, after synthesis has finished."""
import csv
import hashlib
import json
import re
import statistics
from pathlib import Path

BASE=Path(__file__).resolve().parent

# Accept either the enclosing definition or an exact callsite. Each group
# corresponds to a distinct fact, so citing only the target cannot prove callers.
U='src/builder/timeline/unit_labels.py'
B='src/builder/runtime/backend_runtime.py'
M='src/ui/maintenance_panel.py'
E='src/builder/engine.py'
T='src/builder/artifacts/temporal_context.py'
D='src/ui/timeline_dashboard.py'
SUPPORT={
 'L1':[(U,{21})], 'L2':[(B,{222})], 'L3':[(M,{102})],
 'C1':[(U,{21,26})], 'C2':[(B,{28,29})],
 'C3':[(M,{77}),(M,{80})],
 'P1':[(E,{1447,1454}),(B,{28,29})],
 'P2':[(T,{56,77,80}),(U,{21,26})],
 'P3':[(M,{168,184}),(M,{174}),(E,{2218,2219}),('src/builder/ops/lifecycle_ops.py',{263})],
 'I1':[(T,{56,77,80}),(T,{146,165}),(D,{757,789,794})],
 'I2':[(B,{n}) for n in range(229,234)],
 'I3':[(M,{127,137}),(M,{35,77}),(M,{179,181})],
}


def parse_result(data):
    events=[]
    for line in (data.get('stdout') or '').splitlines():
        try: events.append(json.loads(line))
        except ValueError: pass
    tools=[e for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type') not in ('agent_message','reasoning')]
    texts=[e['item']['text'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
    usage=next((e['usage'] for e in reversed(events) if e.get('type')=='turn.completed'),{})
    if not texts: return None,usage,tools
    text=texts[-1].strip()
    text=re.sub(r'^```(?:json)?\s*|\s*```$','',text)
    try:return json.loads(text),usage,tools
    except ValueError:return None,usage,tools


def grade(expected, answers, ordered=False):
    actual=[str(a).replace('\\','/').removesuffix('()') for a in answers]
    tp=len(set(expected)&set(actual));fp=len(set(actual)-set(expected));fn=len(set(expected)-set(actual))
    precision=tp/(tp+fp) if tp+fp else 0
    recall=tp/(tp+fn)
    return dict(tp=tp,fp=fp,fn=fn,precision=precision,recall=recall,exact=set(expected)==set(actual) and (not ordered or actual==expected))


def main():
    gold={x['id']:x['expected'] for x in json.loads((BASE/'gold.json').read_text(encoding='utf-8'))}
    packets={(x['rep'],x['id'],x['arm']):x for x in json.loads((BASE/'packet-metrics.json').read_text())}
    rows=[]
    for rep in range(3):
        for qid,expected in gold.items():
            for arm in ['baseline','graphify','cbm','both']:
                p=BASE/'answers'/f'{rep}-{qid}-{arm}.json'
                if not p.exists():continue
                d=json.loads(p.read_text(encoding='utf-8'))
                response,usage,tools=parse_result(d)
                packet=(BASE/'raw'/f'{rep}-{qid}-{arm}.txt').read_text(encoding='utf-8')
                fresh=d.get('evidence_sha256')==hashlib.sha256(packet.encode()).hexdigest()
                row=dict(rep=rep,id=qid,arm=arm,valid=d.get('returncode')==0 and response is not None and not tools and fresh,seconds=d['seconds'],**usage)
                row.update(packets[(rep,qid,arm)])
                if row['valid']:
                    row.update(grade(expected,response.get('answers',[]),qid.startswith('P')))
                    row['answers']=response.get('answers',[])
                    row['caveat']=response.get('caveat','')
                    citations=response.get('evidence',[])
                    valid_citations=[]
                    cited=set()
                    for e in citations:
                        m=re.search(r'(src/[\w/.-]+\.py):(?:L)?(\d+)',str(e))
                        if m:
                            file=BASE/'snapshot'/m[1]
                            if file.exists() and 1<=int(m[2])<=len(file.read_text(encoding='utf-8-sig').splitlines()):
                                valid_citations.append(e)
                                cited.add((m[1],int(m[2])))
                    row['evidence_in_bounds']=bool(valid_citations)
                    row['evidence_complete']=all(any((file,line) in cited for line in lines) for file,lines in SUPPORT[qid])
                    row['evidence']=citations
                    # P3 requires acknowledgement that the runtime factory type is an assumption.
                    row['pass']=row['exact'] and row['evidence_complete'] and (qid!='P3' or bool(row['caveat']))
                rows.append(row)
    (BASE/'scores.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    summary=[]
    for arm in ['baseline','graphify','cbm','both']:
        rs=[r for r in rows if r['arm']==arm and r['valid']]
        if not rs:continue
        total=lambda k:sum(r.get(k,0) for r in rs)
        summary.append(dict(arm=arm,valid=len(rs),passed=total('pass'),tp=total('tp'),fp=total('fp'),fn=total('fn'),
                            precision=total('tp')/(total('tp')+total('fp')) if total('tp')+total('fp') else 0,
                            recall=total('tp')/(total('tp')+total('fn')),
                            median_query_seconds=statistics.median(r['query_seconds'] for r in rs),
                            median_answer_seconds=statistics.median(r['seconds'] for r in rs),
                            median_input_tokens=statistics.median(r.get('input_tokens',0) for r in rs),
                            total_input_tokens=total('input_tokens'),total_cached_input_tokens=total('cached_input_tokens'),total_output_tokens=total('output_tokens')))
    (BASE/'summary.json').write_text(json.dumps(summary,indent=2))
    with (BASE/'scores.csv').open('w',newline='',encoding='utf-8') as f:
        keys=['rep','id','arm','valid','pass','precision','recall','fp','fn','query_seconds','seconds','input_tokens','cached_input_tokens','output_tokens','packet_chars']
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(json.dumps(summary,indent=2))
    print('answers',len(rows),'expected',144)


if __name__=='__main__':
    assert grade(['a'],['a'])['exact']
    assert grade(['a'],['b'])['fp']==1
    assert not grade(['a','b'],['b','a'],True)['exact']
    assert grade(['a','b'],['a'])['recall']==0.5
    main()
