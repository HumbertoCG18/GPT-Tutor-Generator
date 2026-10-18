# Agent Skills: referências adaptadas

Pacote seletivo para as issues [#12](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/12),
[#13](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/13) e
[#17](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/17). Fonte:
[`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills/tree/a120596f6d7ff9b967a3f5e0331ea911376ee5ef),
MIT, revisão `a120596f6d7ff9b967a3f5e0331ea911376ee5ef`.

Adaptação documental; não instala plugin, dependência, hook ou gate. Os donos atuais
continuam: ponytail decide o que construir; MEX/Graphify localizam fatos; Fable executa;
Astra revisa uma vez, somente leitura; Gates 1/2 controlam plano e commit.

## Qualidade: baseline, ratchet e piso

Aplicar com #13. Cada regra precisa declarar comando exato, escopo e momento de execução.
Separar regra declarada de check realmente imposto. Medir o baseline antes de fixar números;
o ratchet impede regressão sem exigir limpar dívida histórica na mesma tarefa.

- Fast: diff/arquivo alterado durante a edição. Task: testes e contratos do escopo.
  Full: suíte ampla em PR/release. Custo medido define a posição.
- Não reduzir limite, remover teste/assertion, adicionar skip/supressão, esconder falha em
  `pass`/stub ou criar exceção sem dono, justificativa e validade.
- Mudança legítima no piso exige alteração explícita, revisão e Gate 2; nunca ajuste do check
  no mesmo diff apenas para obter verde.
- Saída inconclusiva do guard é falha de infraestrutura, não aprovação.

O `floor-guard` upstream é uma referência regex e não entra ativo antes do baseline de #13.
Ao automatizar, incluir arquivos rastreados, staged e untracked; reportar regra + localização,
sem imprimir valor sensível; testar falso positivo e os códigos limpo/violação/inconclusivo.

## Contexto: selecionar, proteger, checkpoint

Aplicar ao contrato de delegação e retomada em `.workflow/workflow.md`.

- Proteger sempre: objetivo, critérios, restrições, estado da tarefa, diff/HEAD, último erro,
  verificações e próximo passo. Referenciar corpus grande por path/linha; não colar histórico.
- Ler `ROUTER.md`, estado e handoff antes de reabrir fontes. Recuperar detalhe sob demanda;
  não repetir saída já preservada.
- Antes de compactação automática ou quando a sessão se aproximar de 75% da janela, atualizar
  `.workflow/local/active-task.md` (legado: `.workflow-local/`) e o handoff aplicável. Iniciar sessão nova quando o estado
  autocontido for menor e mais confiável que continuar acumulando contexto.
- Conflito entre instruções, estado e código deve ser registrado e resolvido pela precedência
  existente; não preencher lacuna material com suposição silenciosa.
- Brief externo inclui somente evidência decisiva e skills necessárias. O destino confirma
  instalada → descoberta → lida → aplicada; nenhuma dessas etapas implica a seguinte.

Checkpoint válido permite retomar sem transcript: tarefa/issue, branch/HEAD, arquivos permitidos,
donos, Gates 1/2, decisões, comandos/resultados, riscos, pendência e próximo passo concreto.

## Observabilidade: perguntas antes dos sinais

Aplicar com #12. Escrever de duas a quatro perguntas operacionais antes de instrumentar; cada
log, métrica ou span precisa responder uma delas. Métrica mostra que há problema, trace localiza,
log estruturado explica.

- Eventos estáveis e estruturados: `run_id`/correlation ID, `entry_point`, operação, duração,
  resultado e versão. Propagar o ID nas fronteiras assíncronas e externas.
- RED em operações/dependências relevantes: taxa, erros, duração. USE apenas em recursos reais:
  utilização, saturação, erros. Latência usa histograma/percentis, não média isolada.
- Labels têm conjunto pequeno e fixo. Proibidos IDs de usuário/run, URL bruta, email, texto de
  erro, conteúdo acadêmico, prompt, segredo ou corpo integral.
- Alertas, se houver operação monitorada, cobrem sintoma acionável, limiar baseado em baseline,
  destino e runbook. Desktop local sem plantão não ganha pager artificial.
- Validar com falha induzida: localizar pelo correlation ID, conferir campos/cardinalidade,
  seguir a operação e diagnosticar sem abrir o código. Coletor indisponível não quebra o produto.

## Condição de adoção

- Os três blocos foram comparados com #12/#13 e o contrato de contexto.
- Nenhum dono, Gate ou política de autorização foi substituído.
- Somente esta referência curta foi empacotada; os SKILL.md integrais permanecem upstream.
- Antes de ativar qualquer check: baseline reproduzível, comando documentado, caso de falha,
  falso positivo, custo e rollback aprovados no Gate 1; diff e resultados confirmados no Gate 2.

