# Context Mode — medição real nas três CLIs

Issue: [#22](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/22)

Data: 2026-09-18

Base do corpus: `origin/main` em `2ba355f`

Versão avaliada: `mksglu/context-mode@c127f2fe8496fef36e0ebef36ded92d4fa8f570`
(`1.0.169`).

## Decisão

- **Claude Code:** manter somente como MCP manual para corpus grande, iniciado por
  `server.bundle.mjs`, com armazenamento exclusivo. Não instalar plugin nem hooks.
- **Codex:** remover. O modo `approval_policy = "never"` bloqueou ferramentas de execução;
  houve duas respostas incorretas, tempo muito maior e mais tokens de entrada.
- **AGY:** remover. As duas respostas ficaram corretas, mas o resultado foi inconsistente e
  sempre mais lento e verboso.
- Não generalizar economia de contexto: bytes, cache e tokens têm semânticas diferentes em
  cada CLI. Reavaliar apenas após correção concreta das incompatibilidades.

## Método

Foram executadas 12 sessões novas: três CLIs × duas tarefas × Context Mode desligado/ligado.
As tarefas usaram corpus real e saída estruturada: extração exata do JSON da auditoria e
inspeção de linhas/comportamento de `src/ui/app.py`. Critério: resposta completa e valores
pedidos corretos, além de exit code, duração, bytes, métricas de uso e chamadas MCP.

Versões: Claude Code `2.1.276`, Codex `0.155.0`, AGY `1.2.6`, Node `24.13.0` e npm
`11.17.0`. Preflights inválidos de permissão, schema e caminho relativo foram corrigidos e
sobrescritos antes da série final; não entram nos 12 registros.

| CLI | Tarefa | Correto OFF/ON | Tempo OFF → ON | Saída OFF → ON | Context Mode |
|---|---|---:|---:|---:|---:|
| Claude | auditoria | sim/sim | 73,040 → 31,800 s (-56,5%) | 156.971 → 100.300 B (-36,1%) | 2 chamadas, 0 falhas |
| Claude | UI | sim/sim | 33,942 → 28,509 s (-16,0%) | 118.296 → 110.711 B (-6,4%) | 2 chamadas, 0 falhas |
| Codex | auditoria | sim/**não** | 60,962 → 246,529 s (+304,4%) | 1.705.663 → 111.217 B (-93,5%) | 18 chamadas, 4 falhas |
| Codex | UI | sim/**não** | 33,533 → 161,392 s (+381,3%) | 52.198 → 73.952 B (+41,7%) | 14 chamadas, 3 falhas |
| AGY | auditoria | sim/sim | 97,763 → 108,012 s (+10,5%) | 48.273 → 70.337 B (+45,7%) | 18 chamadas, 1 falha |
| AGY | UI | sim/sim | 38,862 → 58,832 s (+51,4%) | 23.126 → 43.419 B (+87,7%) | 10 chamadas, 1 falha |

Resultado recalculado pela resposta final: 10/12 corretas; Codex/auditoria/ON e
Codex/UI/ON falharam no conteúdo. O avaliador original procurava termos no transcript inteiro
e marcou a auditoria incorretamente. Separadamente, 9/12 respostas obedeceram ao schema:
Claude/auditoria OFF e ON usaram array em `p0_items`, e Claude/UI/ON usou array em
`error_actions`, embora o schema aceitasse somente escalares. Conteúdo correto e conformidade
estrutural são medidas distintas.

## Uso reportado pelas CLIs

| CLI/tarefa | OFF | ON |
|---|---|---|
| Claude/auditoria | criação cache 56.014; leitura 344.134; saída 5.056; US$ 1,4603365 | criação 29.531; leitura 162.540; saída 2.356; US$ 0,750214 |
| Claude/UI | criação cache 27.256; leitura 160.179; saída 2.546; US$ 0,71360275 | criação 32.619; leitura 168.376; saída 1.877; US$ 0,789513 |
| Codex/auditoria | entrada 193.262 (147.840 em cache); saída 1.222 | entrada 853.198 (787.072 em cache); saída 6.956 |
| Codex/UI | entrada 64.380 (27.008 em cache); saída 665 | entrada 961.693 (899.456 em cache); saída 4.523 |
| AGY/auditoria | total 184.692; leitura cache 1.147.978; saída 19.440 | total 192.004; leitura cache 521.209; saída 13.725 |
| AGY/UI | total 113.711; leitura cache 361.307; saída 7.565 | total 88.805; leitura cache 316.564; saída 10.209 |

No Claude, `input_tokens` ficou entre 8 e 16 devido ao cache; por isso a tabela preserva
criação, leitura e saída separadas. No Codex, cache é subconjunto da entrada. No AGY, total e
leitura de cache são campos separados. Não somar campos entre fornecedores.

## Falhas e correções

Codex recusou `ctx_execute_file`, `ctx_execute` e `ctx_batch_execute`: a chamada MCP exigia
aprovação, mas a política era `never`. O fallback por índice/busca recuperou comportamento,
mas perdeu linhas exatas no caso UI. Na auditoria, a resposta final informou 10 candidatos em
vez de 29 e retornou a contagem de itens P0 em vez do nome pedido.

AGY primeiro chamou `ctx_execute` sem `language` e `code`; o schema rejeitou a chamada e o
modelo se recuperou. Isso ocorreu uma vez em cada tarefa ON.

O launcher `start.mjs` criou automaticamente
`~/.claude/hooks/context-mode-cache-heal.mjs`, registrou `SessionStart` e habilitou o plugin.
Esse efeito viola o piloto MCP-only e a decisão da issue #19. A configuração gerada foi
removida e o MCP Claude passou a iniciar o mesmo servidor por `server.bundle.mjs`. Smoke test:
conectado; hash de `~/.claude/settings.json` antes/depois idêntico
(`0536496025b8318dbb3f452d0a740c1ef6c615330a933c47ae54bb68cee5a0f8`); hook ausente.

Cada CLI usa armazenamento próprio. Após a decisão, Codex e AGY têm zero registro de
`context-mode`; Claude mantém somente o MCP manual. Nenhum hook Context Mode permanece.

## Limite do resultado

Duas tarefas não provam benefício geral. A melhora forte do Claude ocorreu no corpus maior;
na tarefa UI, o custo reportado aumentou apesar da redução de tempo e saída. A issue permanece
aberta porque o aceite literal exige 12 resultados corretos e houve duas falhas no Codex/ON.
