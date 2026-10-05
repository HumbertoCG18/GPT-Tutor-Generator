# Avaliação P1 — 2026-10-02 (job-31, tentativa única)

Estado: INTERROMPIDO; tentativa consumida, sem retry automático; não há consolidado.json. Braços:
- base: replay_base.json (cru05, e024d396, evidência existente; identidade P1-desligado herdada 350/350).
- A: replay_candidato.json (cru05, evidência existente; não rerodado).
- P1: worktree job-31 (bf46d51f) + index.py 28894d0a, file_map.py 6ad4f70b copiados da p1; runner replay_p1.py = replay_cru05.py + ru.auto_sub=partial(divisores_de_frase=_divisores_de_frase) (P1 nas duas passadas) + sha dos módulos carregados.
- A+P1: braco_ap1/src = src P1 + normalize.py cru05 (f5b9581a).
O runner previa registrar sha256_mudancas_pre_gold; nenhum JSON de decisão foi produzido nesta tentativa.
Herdado (não rerodado): testes 14/14, mutação, suíte 2461/4 skip/2 falhas baseline, identidade P1 desligado vs base. NÃO verificado: A+P1 desligado vs A e suíte em árvore A+P1.
Consolidação: python consolida.py → consolidado.json; logs log_p1.txt, log_ap1.txt.

## Resultado: INTERROMPIDO POR TEMPO (sem placar)
Correção do coordenador: o job terminou em 232,166 s, abaixo do limite de 600 s. O executor interrompeu antecipadamente por estimativa de tempo. Logs: P1 até ES2 (137 s), A+P1 até IA (130 s). Nenhum JSON de saída foi gravado; não foi timeout.
Nenhum gold aberto, nenhuma decisão de aceite. Aceite P1 vs base e A+P1 vs base: SEM EVIDÊNCIA.
Os comandos abaixo são referência técnica, NÃO autorização de execução. Uma nova tentativa exige decisão explícita do usuário; sem retry automático. A consolidação ainda está incompleta.
python -B replay_p1.py --worktree <job-31> --saida replay_p1.json --referencia <cru05>/replay_base.json
python -B replay_p1.py --worktree braco_ap1 --saida replay_ap1.json --referencia <cru05>/replay_base.json
Pendente em consolida.py: contraste A+P1 vs A no eixo sub (escopo bloco/unidade vs A já incluído).
