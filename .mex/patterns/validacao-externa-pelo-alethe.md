---
name: validacao-externa-pelo-alethe
description: Validação externa de um pacote congelado pelo worker validador-externo do Alethe, até 2 rodadas automáticas antes da rodada final do usuário no app.
triggers:
  - "validação externa"
  - "revisão independente"
  - "mandar para o GPT"
  - "pacote cego"
last_updated: 2026-10-01
---

# Validação externa pelo Alethe

Cada pacote de validação externa (`docs/reports/_harness-*/c1-3/validacao_externa_*`, `revisao_delta_*`)
ia ao GPT Pro no app pelo usuário, e a resposta voltava colada: em 29/09 foram cinco rodadas (v1 a v5).
As rodadas intermediárias passam a rodar como worker do Alethe. A final continua no app, porque o
modelo Pro não existe no Codex.

## Quando

Pacote congelado e pronto: ESCOPO (escopo, fora do escopo, perguntas), manifesto com hashes, diffs e
logs vermelho → verde. Sem pacote congelado, não delegar.

## Rodada automática (até 2)

1. Estado da tarefa antes da chamada: classificação, `status=delegando` e a rodada (1 ou 2).
2. `alethe_delegate` com `role: "validador-externo"` (Codex gpt-6-astra, high, somente leitura,
   1800 s) e cwd na raiz do repositório. O brief traz:
   - o caminho da pasta do pacote e do ESCOPO; conferir os hashes do manifesto antes de opinar;
   - as perguntas do ESCOPO, respondidas uma a uma;
   - achados CRITICAL/MAJOR/MINOR com arquivo:linha e cenário concreto; o que sair do escopo vira nota;
   - não ler `.workflow/local`, handoffs nem relatórios fora do pacote, e não alterar arquivos.
3. Salvar a entrega em `<pasta do pacote>/resposta_validador_r<N>.md`, com id do job, modelo, tempo e
   se houve timeout. O texto parcial que o Alethe entrega no timeout conta, marcado como parcial.
4. Corrigir só o que o escopo aprovado cobre e congelar a nova versão do pacote antes da rodada seguinte.
5. Sem CRITICAL/MAJOR na 1ª rodada, não fazer a 2ª.

## Rodada final (usuário, no app)

Depois das rodadas automáticas, parar no Gate e entregar ao usuário o caminho do pacote final, as
respostas `resposta_validador_r*.md` e um prompt pronto para colar no app: escopo, perguntas e pedido de
achados no mesmo formato. A resposta do app é salva como `resposta_app.md` e é ela que decide o Gate.

## Limites

- Uma rodada é uma chamada. Timeout não gera nova tentativa automática.
- O validador não substitui a aprovação metodológica nem o Gate 2.
- O delegate-gate não limita o número de arquivos no brief desse papel; o ESCOPO diz o que conferir primeiro.

Fonte: agent-workflow-lab `references/delegation.md` (papel e exceção de 1800 s, aprovada em 01/10).
