# Pendências — tracker vivo

## [USER] Workflow de entrega e engenharia do produto (17/09)

- [#11](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/11): PR #40 aberto, commit `a29fc94`, check core verde. Progresso nativo + movimento reduzido + auditoria das oito jornadas; 19 testes direcionados e 1126 passed/1 deselected na regressão. Merge aguarda autorização. Cancelamento de importadores/fluxos auxiliares permanece gap conhecido fora da entrega.
- [#12](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/12): PR #39 aberto, HEAD `b5278dd`, check core verde. JSONL local com run_id, duração, status e rotação; teste corrigido para coexistência com handlers externos. Oito testes direcionados verdes. Exportação externa e instrumentação além de build/incremental/process_single continuam futuras; merge aguarda autorização.
- [#14](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/14): contrato documental preparado em `2026-09-19-contrato-qualidade-c6.md`; Gate 2 pendente. Não implementa os checks web.
- [#41](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/41): ativar os gates na primeira fatia vertical C6; stack, baseline de desempenho, schema e CI ainda pendentes. Gate 1 próprio antes de implementar.

## Concluído

- [#10](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/10): contrato e templates recuperados, validados e publicados no PR #31.
- [#13](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/13): check `core` obrigatório na `main`, com suíte, cobertura por plataforma, Ruff e contrato arquitetural, publicado no PR #30.
- [#17](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/17): três referências Agent Skills adaptadas sem plugin/dependência e publicadas no PR #31.
- [#16](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/16): deltas de Karpathy aplicados na fonte e nas três instruções pessoais; quatro arquivos com SHA-256 `acc834ac...`, `verify.py` verde (75 arquivos, zero divergências). Fechada com a limitação registrada: `agent-workflow-lab` sem remote para PR.
- [#22](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/22): medição concluída com 10/12 respostas corretas e 9/12 conformes; Context Mode não adotado e removido das três CLIs. Dados ativos movidos para backup recuperável; nova avaliação exige correção upstream e issue nova.
- [#33](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/33): auditoria HTML/JSON/Markdown corrigida e publicada pelo PR #34; issue fechada em 19/09/2026.
- Prova de retomada entre sessões: `RETOMADA_OK` em `main`/`c17e01f`, worktree limpa, nonce preservado e zero escaladas; nenhum trabalho ou chamada Astra repetidos.
