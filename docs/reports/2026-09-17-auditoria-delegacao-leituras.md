# Auditoria de delegação e leituras — 17/09/2026

Escopo: verificar skills e leituras na delegação Claude Code → Codex/AGY, corrigir
contratos existentes. Sem reinstalação, novas chamadas de LLM, alterações de produto
ou intervenção na tarefa ativa de outra sessão. Sem commit.

## Evidência medida

Rollout Codex: `rollout-2026-09-17T16-01-41-01a0b0be-fa38-70d1-8f47-2f54f430ce3c.jsonl`,
em `~/.codex/sessions/2026/09/17/`. A chamada externa foi `codex exec --profile astra
--sandbox read-only`, com brief via stdin e saída final via `-o`.

- 27 eventos de uso acumulado distintos; 26 `custom_tool_call`, não 26 chamadas
  shell necessariamente: um bloco code mode pode executar várias ferramentas.
- Input acumulado: 2.322.697; cache: 2.202.752; output: 15.412; total: 2.338.109.
  Input do primeiro turno: 30.414; último: 128.455. Total acumulado não é contexto
  simultâneo nem fórmula de consumo de assinatura.
- Saídas com aviso de truncamento nas linhas 19, 37, 49, 58 e 148 do rollout.
  A linha 19 contém o lote que tentou ler Graphify e troglodita. Isso não comprova
  leitura completa nem prova que truncamento causou cada omissão posterior.
- Catálogo e caminhos das skills estavam presentes. Graphify teve leitura de
  SKILL.md/referência e consulta direta ao JSON do grafo; não houve execução de
  `graphify explain` ou `graphify path` nessa sessão. Disponibilidade não prova uso correto.
- Duração registrada: 19:01:41.437Z → 19:12:34.554Z, 10m53s. O timeout previsto
  de 10 minutos não foi demonstrado como limite efetivo. Nenhum supervisor foi instalado.

`python verify.py` no agent-workflow-lab passou: `ok=true`, 75 arquivos gerenciados,
`errors=[]`. Verifica hashes/configuração; não prova aplicação das skills pelo modelo.

AGY: banco local mais recente encontrado, `d7ee58cc-a1ff-4af8-abcb-596fc4ef1f42.db`,
mtime 16/09/2026 04:31:49Z, 16 steps. Inspeção SQLite somente leitura encontrou
`view_file` com StartLine=1/EndLine=100. Trata-se de piloto Context7 anterior;
não prova comportamento de uma delegação de corpus atual nem que skills falharam.

## Navegação e releituras

Comandos locais sem inferência, uma execução por comando:

```text
graphify explain src_builder_artifacts_repo_load_glossary_curation
graphify path src_builder_artifacts_repo_seed_glossary_fields src_builder_artifacts_repo_load_glossary_curation
```

`explain`: exit 0, 1,076 s, 1.574 bytes, localização L1713 e 14 conexões.
`path`: exit 0, 1,217 s, 198 bytes, nenhum caminho dirigido encontrado.
O grafo orienta localização; arestas inferidas e ausência de caminho exigem confirmar
na fonte. Não foi comparada a latência contra outra estratégia equivalente.

`repo.py` já era lido por trechos. Nos intervalos explícitos das linhas 65, 72,
109, 123 e 190 do rollout: 374 linhas emitidas, 330 únicas. Deduplicação local:
19.623 → 16.836 bytes, redução de 14,2%, preservando exatamente o conjunto de
linhas. Não inclui resultados de rg nem todos os arquivos lidos. Não prova que
eliminar releituras basta para reduzir 14,2% dos tokens da sessão.

Reprodução a partir da raiz do GPT Tutor, Python stdlib; hash fixa a versão:

```python
from pathlib import Path
import hashlib

p = Path('src/builder/artifacts/repo.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == (
    '83d28d76dae40b529b7fa7d38a32e7ef598f9a1b7ed4aace3b9a8db4fa51b9aa'
), 'Fonte mudou: reavaliar intervalos antes de comparar'
lines = p.read_text(encoding='utf-8').splitlines()
ranges = [(1445,1507), (1630,1795), (1736,1766),
          (1510,1585), (1602,1626), (1612,1624)]
original = [i for a,b in ranges for i in range(a,b+1)]
unique = list(dict.fromkeys(original))
def render(indices):
    return ''.join(f'{i}: {lines[i-1]}\n' for i in indices).encode('utf-8')
assert set(original) == set(unique)
assert (len(original), len(unique)) == (374, 330)
assert (len(render(original)), len(render(unique))) == (19623, 16836)
print('mesmas linhas; 19.623 -> 16.836 bytes; -14,2%')
```

## Aplicação e limites

- Fonte `agent-workflow-lab/workflow.md`: contrato curto, classificação do pedido,
  skills com evidência de aplicação, consultas delimitadas, deduplicação, UTF-8,
  recuperação de truncamento e registro separado de uso/cache/tempo.
- Template de estado ganhou tipo de delegação e evidência de skills. Fonte e
  snapshot `.workflow/` sincronizados; hashes atualizados após conferir ausência
  de drift nos dois arquivos. Estado ativo de outra sessão não foi sobrescrito.
- Receita `.mex/patterns/delegar-codex-agy.md` alinhada: Astra uma revisão,
  AGY `structured_output`, sem troca automática por quota nem segundo revisor.
  Removidas generalizações de cobrança e de janelas primary/secondary.

Estas mudanças orientam o agente; não são hook de enforcement, teto de tokens ou
garantia de comportamento. Validação ponta a ponta e comparação CC versus Codex
direto com mesma tarefa/modelo/contexto ainda não executadas. A próxima delegação
real deve registrar skills aplicadas, truncamentos, turnos, contexto e tempo.
Outras branches não foram propagadas nesta tarefa; a sessão já aberta precisa
reler o workflow para usar o contrato atualizado.
