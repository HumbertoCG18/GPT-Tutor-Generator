# Taxonomia direta: implementação e evidência

Plano: [plano-taxonomia-direta_15-09.md](plano-taxonomia-direta_15-09.md).
Gate 1 aprovado pelo usuário. Implementação concluída em 15/09/2026, sem commit/push.
Artefatos abaixo estão em `docs/reports/_harness-2026-09-04/c1-3/`.

## Mudança

`src/builder/core/course_vocabulary.py` monta termos integrais usando as mesmas
fontes e regras existentes. Taxonomia e índice de unidades recebem os registros
diretamente. Catálogo e perfil semântico usam uma projeção textual integral,
compatível com seus consumidores legados. `GLOSSARY.md` continua renderizado com
orçamento de apresentação; o corte deixa de apagar aliases do motor.

`sync_fresh` e `motor_copia_nova_15-09.py` exigem destino experimental novo sob
`.frzero/`. O sincronizador incremental permanece legado; não foi transformado
em espelhamento destrutivo. `.motor3eixos/` permaneceu com a baseline limpa.

## TDD e revisão

- Vermelho: `python -m pytest tests/test_glossary_structured.py -q`:
  3 falhas, incluindo alias final perdido e ausência de `sync_fresh`.
- Verde final: mesmo arquivo, 9 testes. Cobrem teto, independência do renderizador,
  atualização de curadoria, plano vazio, placeholders, tópico repetido em unidades
  distintas, tags manuais, perfil semântico e destinos inválidos/ocupados.
- `python -m pytest tests/test_glossary_structured.py --cov=src.builder.core.course_vocabulary --cov-report=term-missing -q`:
  9 passaram; módulo novo com 18 statements, 0 ausentes, 100% de cobertura de linhas.
- Suite completa via `pytest.main(['tests','-q','--disable-warnings','--tb=short'])`,
  em processo com `socket.socket.connect` e `socket.create_connection` bloqueados:
  **2357 passed, 4 skipped**, 37,25 s. Log `suite_taxonomia_final_15-09.log`.
- `python -m ruff check src/ tests/ scripts/`: 154 alertas existentes. Comparação
  dos arquivos alterados contra `git show HEAD:<arquivo>`: 12 alertas, 0 novos.
  Módulo, testes e drivers novos passam sem alertas. `git diff --check` passou.
- Revisão local do diff: assinaturas legadas preservadas, sinônimos continuam fora
  do sinal de unidade, cópia falha antes de sobrescrever destino existente,
  erros de cópia propagados. Sem revisão independente por outro LLM, conforme
  restrição de zero chamadas adicionais.

## Medição

Comandos, a partir da raiz:

```powershell
python -B docs/reports/_harness-2026-09-04/c1-3/motor_copia_nova_15-09.py --destino .frzero/implementacao_taxonomia_15-09
python -B docs/reports/_harness-2026-09-04/c1-3/snapshot_3eixos_14-09.py --raiz .frzero/implementacao_taxonomia_15-09 --saida snapshot_implementacao_taxonomia_15-09.csv
python -B docs/reports/_harness-2026-09-04/c1-3/compara_snapshots_14-09.py --base snapshot_fluxo_base_15-09.csv --braco snapshot_implementacao_taxonomia_15-09.csv
python -B docs/reports/_harness-2026-09-04/c1-3/verifica_taxonomia_impl_15-09.py --base .frzero/fluxo_base_15-09 --novo .frzero/implementacao_taxonomia_15-09
```

O destino já existe: para repetir o motor, usar outro nome novo e outra saída de log.
Logs: `implementacao_taxonomia_15-09.log`, `compara_implementacao_taxonomia_15-09.log`,
`derivados_implementacao_taxonomia_15-09.log`.

| Eixo | Baseline | Implementação | Ganhos/perdas |
|---|---:|---:|---:|
| Bloco | 222/237 | 222/237 | 0/0 |
| Unidade | 253/284 | 253/284 | 0/0 |
| Subunidade aceita | 142/251 | 142/251 | 0/0 |
| Subunidade primária | 100/251 | 100/251 | 0/0 |

316 materiais comparados; zero perdas em cada curso/eixo. O corte de ganho do
comparador imprime ENCERRA por não haver aumento de acurácia; o aceite estrutural
aprovado exige zero perdas e cobertura recuperada, ambos satisfeitos.

Cobertura: MF 23/23, SO 36/36, IA 20/20, ES2 21/21, TCC 26/26, CG 59/59, FR 32/32.
CG recuperou os 8 tópicos sem alias. Nos sete cursos, catálogo de tags, perfil
semântico gerado, auto-tags e campos de atribuição de todos os materiais ficaram
idênticos à cópia de baseline. Motor: **0 tentativas de rede**, 295 s de reprocessamento.

## Limites e manutenção

O corpus é de desenvolvimento. Não certifica cursos inéditos ou criação completa
do zero. Testes cobrem releitura de curadoria; a medição executa regeneração real
nos sete cursos. Qualidade pedagógica do glossário visual não foi avaliada.
Nenhum ganho de acurácia foi demonstrado.

Overview e tracker atualizados. `graphify update . --no-cluster` atualizou o grafo
de código pelo caminho AST local, sem chamada de LLM. Os drivers congelados,
`.ablacao/`, tutores-produto e logs/snapshots anteriores foram preservados.
