# Errata do relatório de preparação de 29/09

Corrige `../validacao_externa_29-09/relatorio_preparacao.md` e a mensagem final da sessão de 29/09. O relatório, o
ZIP (`validacao_externa_29-09.zip`, sha256 `e5de322d…`) e o `manifesto_preparacao.json` ficam intactos; esta errata
prevalece sobre eles nos pontos abaixo. Nenhum candidato foi reclassificado.

## E1. Três N0, não cinco

O relatório (§1) diz "os 5 candidatos N0 são pastas do aluno no OneDrive, sem plano de ensino". O registro
(`populacao_candidata.json`) tem **três N0**: CALC1 (Cálculo 1), FP (Fundamentos da Programação) e MC (Metodologia
Científica). IC (Introdução à Computação) e MD (Matemática Discreta), também pastas do aluno no OneDrive, estão
registrados como **N1**, por menções incidentais no commit base; MSA (projeto do aluno) também é N1. Os seis falham
em E2 (sem plano), então a conclusão não muda: nenhum curso para generalização.

## E2. Defeitos do enumerador e do gerador apontados pela revisão

A revisão independente demonstrou defeitos na v1 (falha do git virava N0; E4 com arredondamento; candidatos dentro do
algoritmo; pacote cego copiando configuração, segredo e saída renomeada no formato de pastas; correspondência
Moodle → arquivo ambígua; procedência incompleta). Nenhum deles alterou o resultado de 29/09 (a v2, aplicada aos
mesmos 16 candidatos, reproduz níveis, populações, motivos e menções da v1), mas as afirmações do relatório sobre o
cegamento e sobre a robustez da busca de exposição valiam só para os casos testados. Correções em `correcoes/`.

## E3. Afirmações do pré-registro de 29/09 que eram decisões e voltaram a pendentes

Mínimo pós-gold (§2.2), bloco não rotulado com invariância (§3.2, §11.2) e replicação da linha do gold por entry
(§4.4) foram apresentados como regras. Passam a ser decisões pendentes (`decisoes_pendentes.md`); o pré-registro não
será assinado enquanto estiverem abertas.
