# Validação externa do regime VOCAB — etapa restrita: correções e aquisição de candidatos N0 (29/09/2026)

**Resultado: 8 disciplinas N0 adquiridas e congeladas; nenhuma entra na população pela regra v2 (mesmos limiares).**
Sem gold, build, replay, Gemini ou LLM; sem entrega a adjudicador; sem commit. O pré-registro NÃO foi assinado.
Esta etapa não é o Gate 1.

## 1. Preservação e errata

- ZIP, manifesto e resultados de 29/09 intactos (`../validacao_externa_29-09/`, `validacao_externa_29-09.zip`).
- `errata_relatorio_preparacao_29-09.md`: **três N0** em 29/09 (CALC1, FP, MC), não cinco; IC, MD e MSA são N1.
  Nenhum candidato reclassificado: a v2 do enumerador, aplicada aos mesmos 16, reproduz níveis, populações, motivos e
  menções da v1.

## 2. Correções dos defeitos demonstrados (`correcoes/`)

| defeito (revisão) | correção | prova |
|---|---|---|
| falha da busca Git virava N0 | git ausente, commit base inexistente, padrão inválido, raiz de evidência ausente no commit ou repositório que não é a raiz → INDETERMINADO, fora de qualquer população | 6 casos negativos + regressão |
| E4 com arredondamento | `local × 100 ≥ 90 × adjudicáveis`, só inteiros | 1800/2001 reprova, 1801/2001 passa, 21/28 reprova |
| candidatos no algoritmo | `candidatos_29-09.json` (dados) + validação de esquema; teste AST: nenhuma sigla, nome ou tutor no script | 2 testes |
| pacote cego copiava configuração, segredo e saída renomeada | recusa por nome de configuração/credencial, allowlist de extensões, assinatura por extensão, varredura de texto (motor e segredo), URLs sem parâmetros de autenticação; recusado não é copiado e fica registrado | 16 testes novos, incluindo o cenário da revisão |
| correspondência Moodle → arquivo ambígua | nome + tamanho; bytes diferentes só se decidem pela pasta da seção; senão a geração falha (`AmbiguidadeOrigem`) | 2 testes |
| procedência incompleta | manifesto com cada fonte lida (papel, sha256) e cada arquivo não usado (motivo); auditoria exige cobertura total | 1 teste + teste herdado ajustado |

Testes: enumerador 17/17; pacote cego 28/28 (12 herdados + 16 novos). Diffs contra 29/09:
`diff_enumera_v1_v2.patch` (+137/−131), `diff_gerador_v1_v2.patch` (+193/−78), `diff_testes_herdados_v1_v2.patch`
(+9/−4, só o teste que passou a aceitar os NOMES dos ignorados no registro de procedência).

**Defeito meu achado pela regressão:** a primeira versão da v2 apontava `REPO` para `docs/` (pasta um nível mais
funda); o `git grep` com pathspec inexistente saiu com "nada achado" e três candidatos viraram N0 — exatamente o
defeito da revisão. Corrigido por construção (raiz conferida por `rev-parse --show-toplevel` e raízes de evidência
exigidas no commit base) e coberto pelo caso `subpasta_do_repositorio`.

Não alterados (fora da lista autorizada): `src/`, compilador, prompt, aliases, pontuador, 2ª passada, harness genérico,
exceção do gitleaks.

## 3. Decisões pendentes (`decisoes_pendentes.md`)

D1 mínimos pós-gold e por curso; D2 bloco com gold ou dois eixos com estabilidade; D3 unidade amostral e duplicatas;
D4 `model_version` (política sem código); D5 âncora da exceção do gitleaks; D6 regra do lote; D7 E4 em cursos com
links; D8 downloads com falha na contagem; D9 alcance da busca de exposição. Todas com o aviso de que as contagens
já são conhecidas.

## 4. Aquisição

- **Manifesto** fixado antes da rede (`aquisicao/manifesto_aquisicao.json`, sha256 `e0c541cc…`): conta do usuário
  já configurada no produto (token nunca lido pelo executor nem impresso), instância `moodle.pucrs.br`; universo = os
  cursos da conta; campos permitidos; exclusões; ordem por hash; orçamento (10 cursos, 2 GB, 200 MB por arquivo);
  parada.
- **Detalhe de implementação decidido antes da consulta, fora do texto do manifesto:** "corresponde a curso
  conhecido" foi implementado como nome normalizado igual e, na falta, contido/contendo; a correspondência parcial
  exclui por cautela (1 caso: Engenharia de Software I).
- **Catálogo** (`catalogo.json`, só campos permitidos, sem professor): 28 cursos.

| classe | n | cursos |
|---|---:|---|
| N0 (baixados) | 8 | Organização e A. de Processadores, Álgebra Linear e Geometria Analítica, Programação de Baixo Nível, Fundamentos de P. P. e Distribuído, Programação Funcional, Métodos Numéricos, Laboratório de Games e N. Gráficas, Projeto e Otimização de Algoritmos (2025/1–2025/2) |
| N1 (menção no repositório; não baixados) | 6 | Fundamentos de D. de Software, Lógica para Computação, Infraestrutura para Gestão de Dados, Prática em Pesquisa, Simulação e Métodos Analíticos, Língua Inglesa IV |
| N1 já classificados (só piloto) | 2 | UX, LSO |
| conhecidos excluídos | 8 | MF, SO, IA, ES2, TCC, CG, FR, LR |
| excluído por correspondência parcial | 1 | Engenharia de Software I |
| não disciplina | 3 | espaços institucionais sem semestre |

Evidências de exposição de cada N1 em `triagem.json` (arquivos no commit base). Indeterminados: nenhum.

- **Downloads** (`inventario_downloads.json`): 8 cursos, 300.727.760 bytes; parada "fim das disciplinas N0". Cada
  arquivo listado pela API tem status (461 no total): 267 ok, 171 links externos (não baixados), 23
  `tipo_inesperado` (servidor devolveu HTML/JSON; um curso). 4 colisões de nome na mesma seção foram gravadas na
  pasta do módulo, sem sobrescrever. Nenhuma falha descartada.
- **Congelamento** (`fontes_congeladas.json`): árvore sha256 por curso; os 8 conferem com o inventário; nenhum arquivo
  extra; nenhum token nos arquivos gravados nem no `contents.json`. Fontes locais em
  `.frzero/validacao_externa_aquisicao_29-09/` (não publicadas).

## 5. População (regra v2, sem mudança de limiar)

| curso | adjudicáveis | com fonte local | plano | E2 | E3 | E4 | população |
|---|---:|---:|---|---|---|---|---|
| Laboratório de Games e N. Gráficas | 80 | 33 | não | F | V | F | inelegível |
| Fundamentos de P. P. e Distribuído | 57 | 42 | sim | V | V | F | inelegível |
| Álgebra Linear e Geometria Analítica | 7 | 7 | sim | V | F | V | inelegível |
| Programação de Baixo Nível | 76 | 28 | sim | V | V | F | inelegível |
| Métodos Numéricos | 55 | 20 | não | F | V | F | inelegível |
| Projeto e Otimização de Algoritmos | 33 | 25 | não | F | V | F | inelegível |
| Programação Funcional | 32 | 20 | sim | V | V | F | inelegível |
| Organização e A. de Processadores | 34 | 28 | sim | V | V | F | inelegível |

Generalização: nenhum curso; piloto: nenhum; mínimo não atingido. LR e os sete continuam fora.

## 6. Limites e o que NÃO se afirma

- N0 = nenhuma menção no commit `bf46d51f` e nenhuma pasta de download anterior. Outras branches, worktrees, memória
  de sessões e conversas não foram buscadas (D9). Não se afirma independência além disso.
- O usuário cursou essas disciplinas: conhece o conteúdo; isso não é exposição do motor, mas pesa no cegamento do
  adjudicador (limitação já registrada).
- Pacotes cegos reais não foram gerados (não autorizado nesta etapa e nenhum curso selecionado).

## 7. Estado

Sem commit. Novos, não versionados: esta pasta. Fontes adquiridas só em `.frzero/`. Tracker e estado local
atualizados depois do congelamento desta entrega.
