# Brief para segunda opinião (Codex astra, read-only) — estado da campanha C1 TRAVESSIA, 2026-09-11 (noite)

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator. Sandbox read-only: não edite, não rode nada que chame
Gemini. Você JULGA os dados abaixo, que já estão prontos; só abra arquivo se um trecho aqui não bastar, e leia por trecho
(`sed -n a,b`), agrupando leituras num comando só. Responda em português, no máximo 1 página mais tabelas; cada achado com
evidência (linha desta página ou arquivo:linha) e marcado MEDIDO ou HIPÓTESE. Abreviação: `c1-3/` =
`docs/reports/_harness-2026-09-04/c1-3/`. Suas três revisões de hoje (camada 3, Fase 1, Fase 2, gold do CG) já estão incorporadas.

## 1. A campanha e o critério

C1 TRAVESSIA é a única campanha aberta; o plano `docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md` é o conteúdo
dela. Tese do plano: "confiança antes de acurácia" — primeiro o motor tem de saber quando está inseguro (Fase 1, gate:
precisão do confiante na subunidade ≥ 90% sem regressão em bloco e unidade), depois acurácia (Fase 2), depois cobertura da
régua (Fase 3). Critério do usuário (03/09): **campanha só fecha com 100% dos itens.** Próxima decidida em 08/09: C5
DÍVIDAS DE DADOS (não C3), porque C3 tem 14% de erro contra 34% do resto, e a C5 tem defeitos com tamanho medido: 32/35
zips com colisão de nome, 122 materiais sem gold de unidade (CG 93, FR 22, LR 7), insumo pdf 94% · zip 66% · html 62% ·
vídeo 57%. Ressalva do plano: "o ganho de acurácia que corrigi-los traz não foi medido".

## 2. Estado item a item (MEDIDO, tracker `docs/reports/pendencias.md` e handoff `docs/reports/_archive/2026-09-11-handoff-camada3.md`)

| item | estado | número |
|---|---|---|
| 1.1 diagnosticar os 64 erros confiantes | fechado 11/09 tarde | 64 → 18 erros confiantes pelo trabalho de acurácia (2.4, camada 3, zips, rótulo meta, M1) |
| 1.2 calibrar o limiar | medido, refutado | limiar de conf não generaliza por curso (leave-one-out); abstenção por piso refutada 3× (hoje: score<1,5 ganha 4 perde 20) |
| 1.3 decisão fraca cai na fila | NÃO entrou, por decisão | gate batido sem regra nova: 90,6% (174/192) à tarde; **90,1% (173/192) agora**, ver §3 |
| 2.1 propagação por similaridade | medido, sem código | +5 estimado (08/09, régua 233) → +1 candidato no produto (base 201 do simulador ≠ 216) |
| 2.2 filtro do vocabulário | regra 1 aplicada, regra 2 descartada | rótulo meta +9 (SO 8→15, CG +2); núcleo em outra unidade 212 → 206/251 no replay |
| 2.3 conflito | medido, regra mantida | bloco vence 20/22 (5 cursos) → **32/36 com o CG** (texto certo 3) |
| 2.4 compilador nos 4 cursos | executado 11/09 manhã | 16 chamadas; subunidade 161 → 214 junto com camada 3 e zips |
| 3.1 FR na régua | fechado | régua 251 |
| 3.2 gold de unidade do CG | fechado hoje | 93 rotulados pela seção do Moodle + plano de ensino, revisado por você, aprovado pelo user; produto 84/93 (79/88 na régua, 5 linhas com `|` fora) |
| `_load_truth` cai para `material_gt` | código verde, **Gate 2 aberto, não commitado** | +8 linhas, 1 teste; suite 2346 passed; CG entra na régua de unidade |

Decisões abertas do plano §3 hoje: camada LLM a cortar → resolvida 11/09 (camada 3 cortada, determ 138 × Gemini 137 em 151);
zips → resolvidos 11/09 (id do membro = zip + caminho); push/merge de **1000 commits locais** → aberta; posição da C7 → aberta;
revisão da fila do CG (`revisar_queue.md`) → aberta, humana. Artefatos publicados (Placar do Motor, Matriz de Atribuição)
**ainda mostram 08/09 (161/251)**.

## 3. Régua hoje (MEDIDO, `c1-3/calibra_fila_como_regua.py`, produto em disco, gold do CG incluído)
```
eixo               n  confiante&certo  confiante&ERRADO  fila&errado  fila&certo
bloco            237              186                 1            1          49
unidade          278              206                 4            9          59
subunidade       251              173                19           18          41
qualquer eixo    311              216                23           24          48

eixo             PRECISAO do confiante   RECALL da fila   alarme falso
bloco             186/187     99.5%    1/2      50%   49/50    98%
unidade           206/210     98.1%    9/13     69%   59/68    87%
subunidade        173/192     90.1%   18/37     49%   41/59    69%
qualquer eixo     216/239     90.4%   24/47     51%   48/72    67%
```
Em 08/09 (início da campanha): subunidade 161/251, precisão do confiante 117/181 = 64,6%, 64 erros confiantes; unidade
157/157 (5 cursos). Subunidade no produto: 216/251 à tarde → **214/251 agora, por mudança de GOLD**, não de produto: o user
decidiu hoje que os 5 materiais de OpenGL do CG têm subunidade 1.4 "Aplicações" (era vazio); o produto prevê vazio em 2 e
`entidades-geometricas` em 3. Os 5 viraram erro; 1 deles confiante (o vídeo, `revisar=ok`), daí 19 erros confiantes e 90,1%.
Os 35 → 37 erros de subunidade restantes: CG 27, MF 3, IA 3, ES2 3, TCC 1, SO 0, FR 0.

## 4. O que a Fase 3 deixou para a C5 (MEDIDO)
- 16 materiais em que `material_gt_<sig>.csv` (rulings do user de 19/08) contradiz o gold de unidade por bloco (MF 4, SO 8,
  ES2 4): por isso `_load_truth` só cai para `material_gt` em curso SEM gold por bloco. Não adjudicado.
- FR (22) e LR (7) continuam sem gold de unidade. FR tem 18 de subunidade (18/18 no produto).
- Cópias `.ablacao/` do replay: a do CG é pré-M1 (replay 53 × produto 57 na subunidade, 4 materiais, todos certos no produto).
- Gold do CG (subunidade 05/09 e unidade 11/09) foi PROPOSTO por mim e adjudicado pelo user; o oráculo é a estrutura do
  professor (seção do Moodle, plano de ensino, cronograma). Não há confirmação do professor em pessoa.
- Diff pendente (Gate 2): `scripts/eval_entry_unit.py` (+8), `tests/test_eval_ground_truth.py` (+16),
  `c1-3/calibra_fila_como_regua.py` (UNI += CG), `c1-3/mede_conflito_unidade.log` regravado, tracker e handoff.

## 5. Perguntas, em ordem

1. **Fechamento.** Pelo critério "100% dos itens", a C1 fecha? Diga item a item o que NÃO está honestamente fechado (1.3 que
   não entrou; 2.1 "+1 candidato"; 3.2 com 5 linhas `|` fora da régua; Gate 2 sem commit) e o que basta para fechar cada um.
2. **Gate da Fase 1 a 90,1%.** O gate era ≥ 90% "sem regressão em bloco e unidade". A queda de 90,6 → 90,1 veio de gold, não de
   produto. O gate segue batido? Que margem é honesta declarar, e o que derrubaria o gate amanhã (próximo gold, próximo curso)?
3. **Próxima campanha.** Com zips corrigidos e gold do CG feito, a lista da C5 encolheu. Ordene o que sobra com gate medível
   por item: gold de unidade FR/LR (29 materiais), 16 contradições `material_gt` × bloco, fila do CG (humana), insumo html/
   vídeo (62%/57%), reconciliar `.ablacao/` do CG, artefatos publicados desatualizados. Ou os dados de hoje mudam a decisão
   C5 > C3 de 08/09?
4. **Riscos do estado.** 1000 commits locais sem push; gold proposto por mim e adjudicado pelo user, sem professor; 27 dos 37
   erros de subunidade no CG; `|` fora da régua de unidade; artefatos públicos com números de 08/09. Ordene por dano e diga
   qual é barato de fechar agora.
5. **Handoff de fechamento.** Em 5 linhas, o que o handoff da C1 tem de dizer para quem abrir a C5 amanhã sem ler o resto.
