import json
import statistics
from pathlib import Path
from score import parse_result

BASE=Path(__file__).resolve().parent


if __name__=='__main__':
    summary=json.loads((BASE/'summary.json').read_text())
    scores=json.loads((BASE/'scores.json').read_text(encoding='utf-8'))
    graph=json.loads((BASE/'graphify-build.json').read_text())
    cbm=json.loads((BASE/'cbm-build.json').read_text())
    warm=json.loads((BASE/'warm-mcp.json').read_text())
    manifest=json.loads((BASE/'manifest.json').read_text())
    assert len(scores)==144 and all(r['valid'] for r in scores)
    text=['# Benchmark Graphify × codebase-memory-mcp — 15/09/2026','',
          '## Resultado e recomendação','',
          'Os quatro braços acertaram as 12 perguntas nas três repetições, com evidência',
          'de fonte suficiente. Combinar os dois grafos não resolveu nenhuma pergunta adicional.',
          'Este piloto não justifica adicionar permanentemente um segundo grafo nem substituir',
          'o Graphify por qualidade ou custo de consulta. O candidato ganhou em indexação.',
          'Manter Graphify como referência; MCP candidato instalado para avaliação, sem alterar',
          'AGENTS ou o roteamento do projeto. Nenhuma remoção/desativação automática foi feita.','',
          '| Condição | Respostas completas | Input mediano (tokens) | Consulta CLI fria mediana | Consulta + resposta mediana |',
          '|---|---:|---:|---:|---:|']
    for s in summary:
        rs=[r for r in scores if r['arm']==s['arm']]
        total=statistics.median(r['query_seconds']+r['seconds'] for r in rs)
        text.append(f'| {s["arm"]} | {s["passed"]}/36 | {s["median_input_tokens"]:.0f} | {s["median_query_seconds"]:.3f} s | {total:.3f} s |')
    text+=['','Input inclui overhead do Codex e tokens de cache; não é consumo líquido nem preço.',
           'Precisão/recall dos itens pedidos: 100% nos quatro braços. Isso não mede todas as',
           'arestas dos grafos. “Completa” exige conjunto correto, ordem quando pedida, ressalva',
           'de tipo em P3 e citações de cada fato; citar só o destino não prova seus chamadores.','',
           '## Índices e atualização','',
           f'- Graphify 0.9.42: {graph["nodes"]} nós, {graph["edges"]} relações; {graph["seconds"]:.2f} s para extrair AST e construir grafo dirigido.',
           f'- codebase-memory-mcp 0.10.8: 2.471 nós, 12.526 relações; {cbm["seconds"]:.2f} s, modo full. São esquemas distintos: contagem não é acurácia.',
           '- Alteração controlada: unit_short_label passou de unit_number para benchmark_new_target, apenas em segunda cópia. Ambos removeram a relação antiga e adicionaram a nova.',
           '- Atualização explícita: Graphify 10,19 s; candidato 8,74 s. Latência de watcher automático não foi medida.','',
           'Microteste com MCP persistente, uma consulta de símbolo/vizinhança e três repetições após aquecimento:']
    for w in warm:
        text.append(f'- {w["name"]}: inicialização {w["startup_seconds"]:.3f} s; consulta mediana {statistics.median(t["seconds"] for t in w["trials"])*1000:.2f} ms.')
    text+=['','Os MCPs retornam formatos e conteúdos diferentes. Esse microteste não substitui',
           'uma bateria de latência persistente. Os tempos CLI da tabela incluem partidas',
           'de subprocessos/daemon e números diferentes de consultas, portanto não demonstram',
           'que o motor interno do candidato seja 14 vezes mais lento.','',
           '## Desenho e limites','',
           f'- Corpus: 130 arquivos Python de src, copiados da árvore de trabalho; HEAD de referência `{manifest["git_head"]}`. Alterações locais e arquivos novos foram incluídos. Hash por arquivo em manifest.json.',
           '- 12 perguntas pré-definidas: três localizações, três chamadas/callbacks, três caminhos, três impactos/imports. Gabarito conferido nos fontes antes da instalação/consulta do candidato.',
           '- Graphify fixado em 0.9.42 do Python311. O ponteiro graphify-out/.graphify_python do projeto aponta para uma instalação UV 0.9.5; não foi alterado. O piloto não mede essa instalação antiga.',
           '- Mesmos arquivos, sem docs, testes, gabarito ou perguntas nos índices. Graphify sem extração semântica por LLM.',
           '- 144 sessões independentes, modelo gpt-6-astra, esforço medium, quatro workers, ordem dos braços alternada por repetição. Nenhuma ferramenta chamada pelo modelo durante a síntese.',
           '- Recuperação determinística com seeds conhecidos + leitura de fonte nos arquivos encontrados. Orçamento de 16.000 caracteres para descoberta e 16.000 para fonte; combinado divide descoberta em 8.000 por grafo.',
           '- Isto mede resposta a pacotes fixos, não planejamento autônomo de ferramentas. A leitura de fonte equalizou resultados; as perguntas são pequenas e não são holdout independente. Não generalizar para documentação semântica, repositórios maiores ou grafos sem fallback.',
           '- Critério de ganho complementar (>=2 perguntas adicionais): não atingido. Qualidade empatada e input total do candidato/combinado maior que Graphify; nenhuma redução de 20% em custo de consulta. Indexação inicial mais rápida não basta para justificar a troca neste uso.','',
           '## Auditoria do harness','',
           'Duas correções instrumentais foram aplicadas igualmente antes da conclusão:',
           'respeitar o arquivo delimitado em C1/C2 (24 pacotes), e resolver prefixos pontuados',
           'do CBM para arquivos reais (três pacotes I1/CBM alterados). Sem a segunda correção,',
           'o leitor ocultava a evidência dos chamadores e penalizava o candidato indevidamente.',
           'Gabarito permaneceu igual. Pacotes anteriores e respostas anteriores foram preservados.',
           'Somente hashes alterados ou falhas de execução foram repetidos. Quatro subprocessos',
           'expiraram ao encerrar apesar de emitir turn.completed; foram repetidos e não entraram',
           'como erro de qualidade. O smoke inicial sem rede também foi excluído.','',
           '## Instalação e reprodução','',
           '- Executável: ~/.local/bin/codebase-memory-mcp.exe; somente registro MCP global do Codex. Outros agentes não foram alterados.',
           '- Release v0.10.8; SHA-256 do ZIP verificado: b43ad982994c4d829670749e08d3b622a74bb20041fc0a7d02bef6113f81c34d.',
           '- Backup: ~/.codex/config.toml.bak-codegraph-benchmark-20260915. Graphify MCP continua disabled; nenhuma modificação em seus arquivos/configuração.',
           '- initialize/list_tools e consultas stdio reais responderam. Registro final verificado no TOML real e hash do executável instalado igual ao extraído. A sessão atual não ganha ferramentas novas automaticamente.',
           '- Snapshots, executáveis e caches estão ignorados pelo Git; não apagar enquanto consultar o índice do piloto.',
           '- Harness: [protocolo](../_codegraph-benchmark/PROTOCOL.md), [perguntas](../_codegraph-benchmark/questions.json), [gabarito](../_codegraph-benchmark/gold.json), [placar CSV](../_codegraph-benchmark/scores.csv), [resumo JSON](../_codegraph-benchmark/summary.json).',
           '- Com Python311, `score.py` regenera placar; `verify.py` confere hashes, respostas atuais, parser, atualização e instalação. `evaluate.py` só repete respostas ausentes, falhas ou pacotes com hash diferente; consome cota do Codex.',
           '- Para outro corpus, usar diretório de rodada novo; prepare.py recusa sobrescrever um gabarito congelado. Não reutilizar o gabarito se as fontes mudarem.','']
    path=BASE.parent/'Feitos/benchmark-codegraph_15-09.md'
    path.write_text('\n'.join(text),encoding='utf-8')
    usages=[]
    for p in (BASE/'answers').glob('*.json'):
        _,usage,_=parse_result(json.loads(p.read_text(encoding='utf-8')))
        if usage:usages.append(usage)
    audit=dict(attempts_with_usage=len(usages),input_tokens=sum(u.get('input_tokens',0) for u in usages),cached_input_tokens=sum(u.get('cached_input_tokens',0) for u in usages),output_tokens=sum(u.get('output_tokens',0) for u in usages),note='Includes superseded packets and retries; not a billing amount; smoke without usage excluded')
    (BASE/'usage-audit.json').write_text(json.dumps(audit,indent=2))
    print(path)
    print(audit)
