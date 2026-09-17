import json
import time
from pathlib import Path

from graphify.extract import extract
from graphify.build import build
from networkx.readwrite import json_graph


if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    root = base / 'snapshot'
    start = time.perf_counter()
    result = extract(sorted((root / 'src').rglob('*.py')), root=root, cache_root=root, max_workers=4)
    graph = build([result], directed=True, root=root)
    out = root / 'graphify-out'
    out.mkdir(exist_ok=True)
    (out / 'graph.json').write_text(json.dumps(json_graph.node_link_data(graph, edges='links'), ensure_ascii=False), encoding='utf-8')
    stats = dict(version='0.9.42', seconds=time.perf_counter()-start, nodes=graph.number_of_nodes(), edges=graph.number_of_edges(), directed=graph.is_directed(), mode='AST only; no semantic LLM calls')
    (base / 'graphify-build.json').write_text(json.dumps(stats, indent=2))
    print(stats)
