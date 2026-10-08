# Regime VOCAB — histórico consolidado

Síntese criada em 2026-10-08, na limpeza de Markdown. Não é estado vivo nem norma nova: as oito fontes citadas continuam
intactas e prevalecem sobre este texto. O estado vivo está no handoff
[2026-09-26-handoff-regime-vocab-claude.md](2026-09-26-handoff-regime-vocab-claude.md) e no bloco VOCAB de
`.workflow/campanhas.json` (`.workflow/campanhas.json:239-300`).

## Linha do tempo

| Data | Documento | Papel | O que estabeleceu | Superado por |
|---|---|---|---|---|
| 24/09 | [desenho](2026-09-24-regime-vocab-desenho.md) | desenho | Regime VOCAB separado, rotulado e opcional; fase 1 sem rede e sem `src` (`2026-09-24-regime-vocab-desenho.md:112-116`) | Não substituído; a fase 1 foi corrigida pelos adendos |
| 25/09 | [adendo v1](2026-09-25-regime-vocab-adendo-fase1.md) | adendo | Corrige a fase 1 sobre o commit `2589ed5a`; descarta o protocolo de 24/09 (`2026-09-25-regime-vocab-adendo-fase1.md:3`, `:16-21`) | v2 (`2026-09-25-regime-vocab-adendo-fase1-v2.md:3`) |
| 25/09 | [adendo v2](2026-09-25-regime-vocab-adendo-fase1-v2.md) | adendo | Harness corrigido; só o bloco NORMATIVO entra no hash (`2026-09-25-regime-vocab-adendo-fase1-v2.md:13-16`) | v3 (`2026-09-25-regime-vocab-adendo-fase1-v3.md:3`) |
| 25/09 | [adendo v3](2026-09-25-regime-vocab-adendo-fase1-v3.md) | adendo | Cadeia de congelamento fechada: código executado = código validado (`2026-09-25-regime-vocab-adendo-fase1-v3.md:66-74`) | v4 (`2026-09-25-regime-vocab-adendo-fase1-v4.md:3`) |
| 25/09 | [adendo v4](2026-09-25-regime-vocab-adendo-fase1-v4.md) | adendo / medição | Gate condicional: libera a CAPTURA dos sete braços, não a régua (`2026-09-25-regime-vocab-adendo-fase1-v4.md:211-212`) | Prevalece só para a medição de 25/09 (ver abaixo) |
| 26/09 | [recompilação limpa](2026-09-26-regime-vocab-recompilacao-limpa.md) | pré-registro / medição | Uma recompilação VOCAB_LIMPO com o compilador atual; parar antes do gold (`2026-09-26-regime-vocab-recompilacao-limpa.md:6-15`, `:170-173`) | Não substituído |
| 27/09 | [validação em cursos novos, desenho](2026-09-27-regime-vocab-validacao-cursos-novos-desenho.md) | desenho / validação | Proposta, nada executado (`2026-09-27-regime-vocab-validacao-cursos-novos-desenho.md:3`) | Pré-registro de 29/09 (`2026-09-29-regime-vocab-validacao-externa-preregistro.md:8`) |
| 29/09 | [validação externa, pré-registro](2026-09-29-regime-vocab-validacao-externa-preregistro.md) | pré-registro | Versão para revisão, não assinada; mínimo amostral não atingido (`2026-09-29-regime-vocab-validacao-externa-preregistro.md:3`, `:35-36`) | Não substituído nestas fontes |

## Resultados medidos

Réguas diferentes não são somadas nem comparadas entre si.

- 12/09 e 13/09, régua v1, base antiga, denominador 251 (aceita): VOCAB inteiro 220, contra 142 no cru da época
  (`2026-09-24-regime-vocab-desenho.md:14`). O próprio desenho declara que não se compara com o placar de 24/09
  (`2026-09-24-regime-vocab-desenho.md:15`).
- 13/09, régua v1, braço V no curso IA, denominador 39: 5 para 38, com 0 regressão (`2026-09-24-regime-vocab-desenho.md:12`).
- 13/09, régua v1, FR construído do zero, denominador 18: 6 para 16 (`2026-09-24-regime-vocab-desenho.md:13`).
- 23/09, ConceptNet (conhecimento externo sem LLM), régua e denominador não citados nesta fonte: 86 para 77, reprovado
  (`2026-09-24-regime-vocab-desenho.md:17`).
- 24/09, régua v2 congelada, base atual do cru, sete cursos: bloco 223, unidade 249, subunidade primária 86
  (`2026-09-24-regime-vocab-desenho.md:65`).
- Mesma referência (CRU, captura W-AB) com denominadores 237 (bloco), 284 (unidade) e 251 (primária)
  (`2026-09-25-regime-vocab-adendo-fase1-v3.md:160`) e valores por curso (`2026-09-25-regime-vocab-adendo-fase1-v3.md:163-164`).
  Reproduzida por ID nos 350 materiais, com 0 divergências, em 25/09 (`2026-09-25-regime-vocab-adendo-fase1-v4.md:229`).
- Fase 1, avaliação W-AD5, data de 26/09 ou anterior: veredicto "sinal exploratório observado; candidato reprovado para
  integração" (`2026-09-26-regime-vocab-recompilacao-limpa.md:3-4`). Nenhuma das oito fontes traz os números dessa avaliação.
- 26/09, recompilação limpa, 26 chamadas previstas: 26/26 unidades na 1ª tentativa, 0 falhas, 0 violações
  (`2026-09-26-regime-vocab-recompilacao-limpa.md:181-182`). Preflight 24/24 e CRU_LIMPO igual à referência por ID, 350/0
  (`2026-09-26-regime-vocab-recompilacao-limpa.md:185-186`). Seis capturas validadas, 14/14 condições
  (`2026-09-26-regime-vocab-recompilacao-limpa.md:187`). Gold não lido (`2026-09-26-regime-vocab-recompilacao-limpa.md:188`).
- 29/09, população da validação externa: generalização = nenhum curso; piloto externo = nenhum; smoke = LR
  (`2026-09-29-regime-vocab-validacao-externa-preregistro.md:35-36`).
- Verificações de harness (não medem acerto): suítes sintéticas 37/37 (`2026-09-25-regime-vocab-adendo-fase1-v2.md:161`),
  68/68 (`2026-09-25-regime-vocab-adendo-fase1-v3.md:193`) e 87/87 (`2026-09-25-regime-vocab-adendo-fase1-v4.md:226`); capturas
  dos sete braços da Fase 1 validadas, 14/14 (`2026-09-25-regime-vocab-adendo-fase1-v4.md:230-231`). Gold não lido
  (`2026-09-25-regime-vocab-adendo-fase1-v4.md:232`).

## Decisões e substituições

- **Cadeia de substituição.** v2 substitui v1 (`2026-09-25-regime-vocab-adendo-fase1-v2.md:3`), v3 substitui v2
  (`2026-09-25-regime-vocab-adendo-fase1-v3.md:3`) e v4 substitui v3 (`2026-09-25-regime-vocab-adendo-fase1-v4.md:3`). Cada
  adendo ficou preservado sem alteração. As normas das quatro versões não se fundem; a v4 prevalece apenas para a medição de
  25/09 ("para a medição", `2026-09-25-regime-vocab-adendo-fase1-v4.md:3`).
- **Autorização por versão.** v2 libera só o CRU, sem gold (`2026-09-25-regime-vocab-adendo-fase1-v2.md:77`); v3 mantém
  `CAPTURA_LIBERADA` = {CRU} (`2026-09-25-regime-vocab-adendo-fase1-v3.md:185`); v4 libera os sete braços
  (`2026-09-25-regime-vocab-adendo-fase1-v4.md:211-212`). Leitura da régua exige Gate próprio nas três
  (`2026-09-25-regime-vocab-adendo-fase1-v4.md:219`).
- **Decisões do usuário em 24/09.** Regime aceito como separado e opcional; sidecars manuais mantidos no produto e em
  quarentena no regime; validação em cursos novos não decidida (`2026-09-24-regime-vocab-desenho.md:113-117`).
- **Escopo declarado nos adendos.** O resultado vale para a cadeia de atribuição condicionada à timeline histórica congelada;
  os sete cursos são desenvolvimento contaminado; 279/300 não comprova generalização
  (`2026-09-25-regime-vocab-adendo-fase1-v4.md:33-38`).
- **VOCAB_LIMPO.** "Limpo" = geração nova, sem manual, sem reuso do sidecar histórico, sem seleção orientada pelo gold; não
  significa não contaminado (`2026-09-26-regime-vocab-recompilacao-limpa.md:24-32`). Uma geração oficial, sem semente
  (`2026-09-26-regime-vocab-recompilacao-limpa.md:49`).
- **Desenho de 27/09.** Recomenda não ajustar nada antes da validação, para medir o compilador congelado
  (`2026-09-27-regime-vocab-validacao-cursos-novos-desenho.md:68-70`). O pré-registro de 29/09 o substitui
  (`2026-09-29-regime-vocab-validacao-externa-preregistro.md:8`).
- **Pré-registro de 29/09.** Sem o mínimo (3 cursos N0 e 100 materiais adjudicáveis), a validação de generalização não
  começa e nenhum limiar muda (`2026-09-29-regime-vocab-validacao-externa-preregistro.md:30-41`). Bloco não é rotulado nos
  cursos novos; vale a invariância por ID (`2026-09-29-regime-vocab-validacao-externa-preregistro.md:50-52`).

## Divergências entre fontes

- Chamadas de recompilação: o desenho estima cerca de 50 para os 7 cursos (`2026-09-24-regime-vocab-desenho.md:100`); a
  rodada limpa prevê 26 (`2026-09-26-regime-vocab-recompilacao-limpa.md:181`).
- Numeração: os adendos v2, v3 e v4 chamam seus harnesses de v3, v4 e v5 (`2026-09-25-regime-vocab-adendo-fase1-v2.md:159-161`,
  `2026-09-25-regime-vocab-adendo-fase1-v3.md:191`, `2026-09-25-regime-vocab-adendo-fase1-v4.md:224`).
- Datas dos sidecars manuais: 12–13/09 (`2026-09-24-regime-vocab-desenho.md:31-33`) contra 07/09 a 12/09
  (`2026-09-25-regime-vocab-adendo-fase1.md:190`).
- Mínimo amostral: ~300 materiais em 6 cursos (`2026-09-24-regime-vocab-desenho.md:81`), ~100 por curso
  (`2026-09-27-regime-vocab-validacao-cursos-novos-desenho.md:64-65`) e 3 cursos N0 com 100 no total
  (`2026-09-29-regime-vocab-validacao-externa-preregistro.md:30`). Os critérios diferem.
- Veredito B: v2 não especifica os eixos (`2026-09-25-regime-vocab-adendo-fase1-v2.md:153`); v3 e v4 exigem os três eixos
  oficiais (`2026-09-25-regime-vocab-adendo-fase1-v3.md:177-179`).

## Onde continuar

1. Estado e próximos passos da campanha: [handoff de 26/09](2026-09-26-handoff-regime-vocab-claude.md), campanha aberta.
2. Estado vivo: bloco VOCAB de `.workflow/campanhas.json` (atualizado em 2026-10-05; VOCAB-02 concluída, VOCAB-03 bloqueada,
   VOCAB-04 proposta, VOCAB-05 pronta; `.workflow/campanhas.json:248-298`).
3. O pré-registro de 29/09 está marcado "NÃO assinado" (`2026-09-29-regime-vocab-validacao-externa-preregistro.md:3`);
   conferir no estado vivo se isso mudou.
4. Normas valem pelas fontes originais, não por esta síntese.
