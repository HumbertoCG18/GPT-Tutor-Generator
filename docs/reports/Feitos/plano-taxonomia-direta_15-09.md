# Gate 1: cópia reproduzível e vocabulário estruturado

Status: implementado e verificado. Gate 1 aprovado pelo usuário; sem commit/push.
Evidência final: `taxonomia-direta-implementacao_15-09.md`, nesta pasta.
Porte: large, por atravessar geração, fachadas, consumidores semânticos e harness.

## Evidência e limite

O experimento `c1-3/fluxo_taxonomia_direta_15-09.py` comparou duas cópias novas:
316 materiais, 0 ganhos e 0 perdas nos quatro eixos. Log:
`_harness-2026-09-04/c1-3/compara_fluxo_direto_x_base_15-09.log`.
O CG recuperou cobertura de aliases de 51/59 para 59/59.
Isso sustenta viabilidade neste corpus de desenvolvimento, não aumento de acurácia,
equivalência completa de todos os artefatos ou certificação de build/resync do zero.

O protótipo usa monkeypatch e JSON no argumento textual do catálogo. Não copiar
esses atalhos para produção. `write_tag_catalog` também gera perfil semântico:
tags e perfil precisam de verificação própria.

## Plano de execução

1. **Cópia limpa, teste vermelho primeiro.** Reproduzir arquivo residual ausente na
   origem que sobrevive a `scripts/ablacao_rapida.py:sync`. Acrescentar modo explícito
   de cópia de experimento que exige destino novo sob `.frzero/`, com erro antes de
   qualquer escrita quando o destino existe ou está fora da área autorizada.
   Usar driver novo em `c1-3/` para chamar o motor congelado nesse modo. Preservar o
   contrato incremental existente, inclusive `material_curation.json`; não trocar
   `/E` por `/MIR` globalmente. Testar também erro de cópia e isolamento da origem.
2. **Produtor único de termos.** Extrair a montagem já existente em
   `src/builder/artifacts/repo.py:glossary_md` para função focada em submódulo de
   vocabulário, conectada por `src/builder/facade/glossary.py`. Reutilizar seeds,
   evidências, curadoria e normalização. Preservar termo, unidade, sinônimos,
   definição e não-confundir; não inventar aquisição nem usar gold. `glossary_md`
   renderiza esses dados e aplica seu orçamento de apresentação depois.
3. **Consumidores diretos.** Em `src/builder/routing/file_map.py` e
   `src/builder/extraction/content_taxonomy.py`, fornecer termos diretamente à
   taxonomia e ao índice de unidades. Ajustar ligações de fachada e
   `src/builder/ops/pedagogical_regeneration.py` para catálogo e perfil semântico
   receberem os dados integrais. Preservar o escopo dos sinais: sinônimos não passam
   a pontuar unidade. Manter compatibilidade dos leitores legados onde necessária;
   build/resync não podem voltar ao Markdown truncado. `engine.py` só liga funções.
4. **Verificação do contrato.** Testes vermelhos para termo no fim de glossário
   maior que 14.000 caracteres e para independência do consumidor em relação ao
   renderizador. Cobrir plano vazio, tópicos repetidos em unidades diferentes,
   ausência de sidecar, placeholders do template, tags manuais e atualização de
   termos no resync. Comparar tags e perfil semântico separadamente, além das
   atribuições. Reutilizar fixtures reais existentes, com proveniência.
5. **Gate de entrega.** Rodar testes direcionados de glossário, taxonomia,
   unidade, catálogo e regeneração; depois a suite. Executar o motor em destino
   novo com rede bloqueada, comparar os 316 materiais contra a baseline limpa e
   registrar cobertura dos sete cursos. Revisar diff, atualizar tracker e overview.
   Atualizar grafo somente em modo compatível com 0 chamadas de LLM.

## Aceite congelado

- 0 perdas por material em bloco, unidade, subunidade aceita e primária.
- Referência: 222/237, 253/284, 142/251 e 100/251. Ganho não é requisito desta correção.
- CG: 59/59 tópicos com alias; demais cursos preservam cobertura.
- Nenhum consumidor do motor depende do corte ou da formatação de `GLOSSARY.md`.
- Glossário continua disponível para prompts e DeepTutor; qualidade do tutor não
  pode ser declarada validada apenas pelo placar do motor.
- 0 chamadas externas de LLM, nenhuma nova dependência e gold exclusivamente na avaliação.
- Logs/snapshots novos terminam em `_15-09`, com nome adicional quando já existe.

## Escopo e autorização

A aprovação autoriza os ajustes de fonte listados acima, testes, novo driver e
documentação associada. Não autoriza escrever nos tutores-produto, em `.ablacao/`,
editar `motor_3eixos_12-09.py` ou `extrator_relacoes_14-09.py`, remedir A/C,
commit ou push. A baseline limpa existente em `.motor3eixos/` fica preservada;
medições novas usam destinos novos em `.frzero/`.

A correção da cópia fica explícita no novo caminho de experimento: o comando
histórico incremental permanece legado e não certifica limpeza por si só.

Sem delegação nesta preparação: preservada a restrição de 0 chamadas adicionais
de LLM. Na implementação, aplicar o fluxo TDD local e registrar limites da revisão.
