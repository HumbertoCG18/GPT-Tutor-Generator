# W-AD2 — preflights sem gold (25/09)

Script `wad2_regime_vocab_fase1_25-09.py` sha256 `18e4155349736bf5…`.
Preflight **APROVADO**.

## Condições

- ✅ P0 src/tests sem diff
- ✅ P2 A em todos os cursos
- ✅ P2 delta não vazio nos braços com sidecar
- ✅ P4 CRU = referência por ID
- ✅ P4 unidade da 1a passada = final
- ✅ P4 sem gold, rede, compilador
- ✅ P3 identidade reproduz VOCAB_LLM
- ✅ P3 controles idênticos ao pretendido pós-carregador
- ✅ P5 manual só no VOCAB_ATUAL
- ✅ P5 nenhuma leitura de outro braço
- ✅ P5 sem gold, rede, compilador
- ✅ P5 unidades do motor iguais em todos os braços
- ✅ P5 taxonomia dos braços históricos = P2

## Equivalências por curso

| curso | A | B VOCAB_ATUAL | B VOCAB_LLM | aliases +LLM | +ATUAL |
|---|---|---|---|---:|---:|
| MF | True | False | False | 80 | 80 |
| SO | True | True | True | 98 | 107 |
| IA | True | False | False | 79 | 100 |
| ES2 | True | True | True | 58 | 80 |
| TCC | True | False | False | 96 | 103 |
| CG | True | False | False | 80 | 85 |
| FR | True | True | True | 55 | 55 |

## Controles por curso

| curso | identidade | MAIOR pós-carregador | colisões MAIOR | ALEAT 1/2/3 pós-carregador | fração mudou (1/2/3) | unidades inviáveis ou sem embaralhamento |
|---|---|---|---:|---|---|---|
| MF | True | True | 0 | True/True/True | 0.887/0.713/0.762 | {'pareado': 9} |
| SO | True | True | 0 | True/True/True | 0.561/0.694/0.602 | {'pareado': 15} |
| IA | True | True | 1 | True/True/True | 0.684/0.608/0.709 | {'pareado': 9, 'sem_embaralhamento_informativo': 3} |
| ES2 | True | True | 0 | True/True/True | 0.707/0.759/0.828 | {'pareado': 6} |
| TCC | True | True | 0 | True/True/True | 0.667/0.688/0.656 | {'pareado': 12} |
| CG | True | True | 0 | True/True/True | 0.637/0.637/0.675 | {'sem_embaralhamento_informativo': 3, 'pareado': 12} |
| FR | True | True | 0 | True/True/True | 0.691/0.6/0.655 | {'pareado': 6} |

## CRU

- Igual à referência por ID: True (sha canônico `2bf79173d213eda2` × referência `2bf79173d213eda2`); 350 materiais; 1ª passada registrada em 341.
- Unidade da 1ª passada diferente da final: 0.

