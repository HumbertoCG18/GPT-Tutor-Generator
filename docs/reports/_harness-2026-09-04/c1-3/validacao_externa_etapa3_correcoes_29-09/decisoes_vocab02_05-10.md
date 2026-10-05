# Decisões da VOCAB-02: D1–D9, R-CC e R-VIS (05/10/2026)

Decididas pelo usuário em 05/10/2026. Fecham `../validacao_externa_etapa2_29-09/decisoes_pendentes.md` (sha256
`766004b3…`) e as aprovações 1 e 3 do adendo 2 de `issue_correcoes_etapa3.md` (sha256 `8283e492…`, A7), exceto o
pré-registro, que só é assinado depois das implementações abaixo.

**Contaminação por contagens:** quem decidiu conhecia as contagens do universo local de 29/09 e do lote adquirido.
As regras 1 e 3 da P3.1 §13 foram informadas por contagens. Nenhuma escolha abaixo foi justificada por fazer um curso
específico entrar ou sair.

## Decisões

| ponto | decisão | situação |
|---|---|---|
| D1, D2, D3, D6, D7, D8 | **P3.1 aprovada** como redigida (`proposta_normativa_populacao_p3_1.md`, sha256 `54089d79…`, versionada em `a4bceda2`): D1-B (≥ 10 documentos por curso pós-gold; abaixo disso, descritivo), D2 (mede-se estabilidade de bloco; acurácia de bloco fora), D3-B (acerto só se todas as entries do documento acertam), D6 substituída pelo §14, D7 (alvo documental; links fora), D8 (falhas no denominador do E4) | aprovada; congelar por hash (P3.1 §7.5) |
| R-CC | **Aprovada** com a P3.1 §4.2 e a redação do adendo 2, A4; cria `gold-externo-2` (marcador `?`) e instruções do adjudicador v2 como arquivos novos | aprovada; arquivos a criar |
| D4 | **Implementar** a verificação de `model_version` (misto ou ausente invalida a geração) na sanidade pós-geração, sem nova geração; teste vermelho primeiro | a implementar |
| D5 | Resolvida: a exceção do gitleaks exige fechamento após o sha256 (`19cccf18`, piloto noturno) | feita |
| D9 | **Ampliar** a busca de exposição para todas as refs git e todas as worktrees do repositório. Memória de sessões e conversas ficam fora e entram como limitação declarada: "N0" = sem evidência nas fontes pesquisadas (P3.1 §7) | a implementar |
| R-VIS | **Opção b:** o usuário aceita expressamente o risco residual de pixels e vetores não examinados; examinam-se todas as estruturas textuais (metadados de imagem, XMP, JSON decodificado de notebooks). OLE legado solto e MP4 continuam recusáveis por conteúdo textual e ativo não examinado. Altera o contrato do Gate 1 ("sem OCR" continua: nenhum OCR é acrescentado) | a implementar (gerador v5) |

## Fora destas decisões

- Nada autoriza gold, aquisição, build, replay, LLM ou aplicação ao lote; cada fase segue com autorização própria.
- O pré-registro de 29/09 continua não assinado até D4, D9 e R-VIS estarem implementados, testados e revisados, e o
  conjunto (texto, políticas e scripts) estar congelado por hash.
- R-META e R-PAGE já foram implementadas (adendo 3); o commit delas segue com a MOODLE-V1.
