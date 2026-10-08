# Dependência do cru em heranças do produto

Concluído: sete cursos reconstruídos e comparados. O cru baseado em cópia do
produto não certifica construção do zero. A retirada conjunta das heranças
reduziu o placar nos quatro eixos, inclusive entre os materiais presentes.

## O que foi comparado

Baseline atual: `.frzero/implementacao_taxonomia_15-09`, motor cru aplicado a uma
cópia nova dos tutores-produto. Braço: importação local desde `stash_folder`, sem
manifest, queue salva, curadoria, Markdown, taxonomia ou timeline do produto.
Perfil salvo (plano, cronograma, identificação e configuração) permanece entrada
explícita. Este teste não certifica a captura original Moodle/SARC/plano.

Protocolo: `protocolo-herancas-cru_15-09.md`. Gold só na comparação posterior.
Entradas vinculadas por caminho de origem único, não pelo ID gerado. Ausentes
continuam no denominador completo; base comum separada. Novos arquivos sem gold
não contam como ganhos.

## Resultado completo

| Eixo | Base completa: baseline → novo | Base comum: baseline → novo | Ganhos / perdas completos |
|---|---|---|---|
| Bloco | 222→169/237 | 216→169/231 | 3 / 56 |
| Unidade | 253→234/284 | 244→234/271 | 7 / 26 |
| Sub aceito | 142→99/251 | 138→99/243 | 5 / 48 |
| Sub primário | 100→76/251 | 96→76/243 | 7 / 31 |

316 materiais na régua; 303 comuns e 13 ausentes, zero vínculos ambíguos.
As ausências explicam seis perdas de bloco, nove de unidade, quatro de aceito
e quatro de primário. O restante não desaparece ao restringir aos comuns.
Foram importadas 338 entradas; 12 origens novas não têm crédito de ganho na régua.

## Resultado por curso

Valores mostram acertos baseline → reconstrução / denominador completo.

| Curso | Bloco | Unidade | Sub aceito | Sub primário | Comuns / avaliados |
|---|---|---|---|---|---|
| MF | 59→45/66 | 61→59/66 | 46→29/58 | 25→25/58 | 62/66 |
| SO | 36→29/39 | 27→23/37 | 9→5/15 | 8→4/15 | 39/39 |
| IA | 41→25/42 | 42→39/42 | 5→5/39 | 4→4/39 | 40/42 |
| ES2 | 27→11/28 | 24→26/28 | 16→2/28 | 14→2/28 | 31/31 |
| TCC | 26→26/27 | 18→17/18 | 8→9/11 | 6→7/11 | 27/27 |
| CG | 33→33/35 | 81→70/93 | 51→42/82 | 37→28/82 | 86/93 |
| FR | sem gold | sem gold | 7→7/18 | 6→6/18 | 18/18 |

Em MF o saldo zero de primário esconde quatro ganhos e quatro perdas.
Em TCC um dos dois ganhos de subunidade
é abstenção correta, não identificação de um novo tópico.

## Mecanismos e limites do diagnóstico

- Todos os sete cursos preservaram IDs ordinais, datas e agrupamentos da timeline.
  Portanto, esses deltas não decorrem de comparar números de bloco incompatíveis.
- 342 hashes conferidos após o build: 338 entradas e quatro metadados locais.
- Sete PDFs registrados como `scanned-pages` (MF cinco, SO um, TCC um).
  Zero falhas de importação não significa que todo material tenha texto útil.
- `raw/moodle/contents.json` e `.moodle_nomes.json` locais existem só em CG/FR
  e foram consumidos. Verificados em `stash` e no diretório pai dos sete cursos;
  os outros cinco não têm esses arquivos nesses layouts. Não houve recaptura online.
- Nos sete cursos, zero tópicos sem alias antes e depois. Esse indicador não
  certifica qualidade: a cobertura mínima permanece enquanto o placar regride.
- `content_taxonomy.py:726` coleta títulos priorizando Markdown aprovado/curado;
  a linha 734 ignora caminhos `staging/`. `file_map.py:1298` passa esses títulos
  à taxonomia; `content_taxonomy.py:645` pode incorporá-los como aliases.
- TCC: 27/27 PDFs novos em staging, zero referências curadas. A função real
  retorna 54 títulos na baseline e zero na reconstrução; aliases 57→27.
  O título adicional “Apresentação da Disciplina e Revisão de Teoria de Conjuntos”
  está no Markdown curado herdado, não no vocabulário reconstruído.
- A coleta de evidência do glossário também lê somente `content/curated`
  (`repo.py:1220`). TCC tinha 37 arquivos nessa pasta; novo curso tem zero.
  Isso não prova que todos os documentos ou aliases herdados foram escritos por LLM.
- Há outras mudanças simultâneas: datas, rótulos Moodle, categorias, títulos,
  pinos manuais e texto extraído. Em MF diferem 13 pinos de unidade e 19 de bloco.
  O experimento mede a retirada conjunta das heranças, não o efeito causal isolado
  de cada uma. Não atribuir toda perda ao glossário ou aos títulos.

| Curso | Títulos coletados | Aliases na taxonomia |
|---|---|---|
| MF | 79→6 | 70→33 |
| SO | 79→7 | 68→36 |
| IA | 103→42 | 72→41 |
| ES2 | 47→0 | 49→21 |
| TCC | 54→0 | 57→27 |
| CG | 5→3 | 61→60 |
| FR | 0→0 | 32→32 |

Hipótese ainda não medida: recuperar metadados originais e permitir sinais
estruturais confiáveis do Markdown local pode reduzir essas perdas. Este teste
não autoriza aprovar automaticamente conteúdo em staging nem reintroduzir
curadoria do produto sob o nome de cru.

## Reprodução e arquivos

Diretório dos comandos/logs: `docs/reports/_harness-2026-09-04/c1-3`.
Executar a partir da raiz do projeto. Drivers rejeitam destinos/saídas existentes.

```powershell
python -B docs/reports/_harness-2026-09-04/c1-3/cru_fontes_15-09.py --curso CURSO --destino DESTINO --sem-descricao-html
python -B docs/reports/_harness-2026-09-04/c1-3/compara_herancas_15-09.py --cursos CURSO --novo DESTINO --saida herancas_CURSO_15-09.json
python -B docs/reports/_harness-2026-09-04/c1-3/compara_herancas_15-09.py --autoteste
python -B docs/reports/_harness-2026-09-04/c1-3/audita_herancas_15-09.py --saida auditoria_herancas_15-09.json
```

| Curso | Destino sob `.frzero/` | Log de build |
|---|---|---|
| MF | cru_fontes_serial_15-09 | cru_fontes_MF_serial_15-09.log |
| SO | cru_fontes_15-09 | cru_fontes_SO_adiantado_15-09.log |
| IA | cru_fontes_serial_15-09 | cru_fontes_IA_serial_15-09.log |
| ES2 | cru_fontes_15-09 | cru_fontes_ES2_15-09.log |
| TCC | cru_fontes_15-09 | cru_fontes_TCC_adiantado_15-09.log |
| CG | cru_fontes_semhtml_15-09 | cru_fontes_CG_semhtml_15-09.log |
| FR | cru_fontes_controle_15-09 | cru_fontes_FR_controle_15-09.log |

ES2 foi iniciado sem `--sem-descricao-html`, sem HTML na entrada e sem tentativas
de rede. Demais rodadas finais usam a flag. MF/IA originais e CG original foram
interrompidos; parciais e logs preservados, não avaliados. Versões antigas de ES2
e FR não têm campo `completed`; conclusão validada pelo exit code zero observado.
Nas demais, também há `completed=true` no resultado do build.

As rodadas finais de MF/SO/IA/TCC/CG/FR usam `OMP_NUM_THREADS=1`,
`OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`; ES2 manteve o ambiente inicial.
Mesmo backend preferido local PyMuPDF4LLM; nenhuma entrada retirada por custo de
extração. Backends efetivos por manifest ficam na auditoria consolidada.

Comparações individuais geram `herancas_CURSO_15-09.json`, CSV e log.
Inventário e hashes: `_inputs_15-09.json` em cada tutor reconstruído.
Conclusão do build e tentativas: `_build_result_15-09.json`.
Autoteste: reproduziu os quatro eixos dos 316 materiais da baseline.
Consolidado: `auditoria_herancas_15-09.json` e `auditoria_herancas_15-09.log`.
O arquivo `auditoria_herancas_parcial_15-09.json` permanece como registro da etapa
anterior, não como resultado final. Lint dos três scripts passou.

## Rede e preservação

Zero chamadas externas de LLM nesta medição. Sete rodadas finais concluídas com
zero tentativas de rede e zero entradas com falha de importação. O harness bloqueia chamadas de
clientes e conexões no processo Python; não é uma afirmação de sandbox de rede
do ambiente inteiro. CG original tentou Datalab para imagens HTML, mas o bloqueio
impediu a chamada; essa rodada foi descartada. CG final teve zero tentativas.
O defeito do modo HTML offline está registrado no tracker, sem correção em src.

Nenhuma alteração de src nesta medição, nenhum commit/push. Tutores-produto,
`.ablacao/` e `.motor3eixos/` fora dos destinos de escrita. Mudanças de implementação
anteriores permanecem no worktree; não foram revertidas.
