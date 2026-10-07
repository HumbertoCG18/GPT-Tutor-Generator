# Revisão do delta R-META/R-PAGE: escopo (29/09/2026)

Pacote para **uma única revisão independente** deste delta. Não é aprovação. Não substitui a aprovação metodológica.

## Escopo

1. **Corpos HTTP (`src/builder/sources/moodle.py`, `MoodleClient`):**
   - contagem e limite dos corpos lidos pela aplicação (não é todo o tráfego de rede);
   - verificação antes da requisição;
   - Content-Length acima do orçamento;
   - corpo truncado e término não confirmado sem sondar além do limite;
   - parciais nas exceções;
   - compatibilidade dos consumidores sem limite (`limite_bytes = None`).
2. **Persistência do consumo entre chamadas e execuções** (`adquire` v5: `catalogo`, `le_consumo_catalogo`,
   `baixa_curso`, `baixar`), incluindo falhas, JSON inválido, erro da API, interrupção e registro ilegível.
3. **R-PAGE, identificação provisória do HTML principal** (`adquire` v5 e gerador v5):
   - regra: `index.html`, `filepath "/"`, `filesize 0`, exatamente um;
   - zero ou vários candidatos ficam não cobertos, no denominador;
   - anexo `.html` e colisão com `index.html`.

   A regra foi inferida das respostas locais, inclusive o lote. Não é contrato confirmado do Moodle.
4. **Correspondência entre código, testes e evidências:** diffs, hashes do manifesto, logs vermelho → verde e JSON de
   resultados.

## Fora do escopo

- A auditoria anterior da etapa 3, já encerrada.
- R-VIS: não aprovada; o pacote cego não está liberado para uso real.
- R-CC e `gold-externo-2`: só propostas.
- P3.1 e a metodologia.
- Aquisição real, rede, gold, adjudicação, motor, build, replay e elegibilidade.

## Commit técnico proposto (Gate 2, não autorizado)

Somente `src/builder/sources/moodle.py` e `tests/test_moodle.py`. O `adquire` v5, o gerador v5, os testes de
harness, os diffs, os logs e os resultados ficam como evidência congelada por este manifesto, fora do commit.

## Reproduzir (sem rede)

- `python -B -m pytest tests/test_moodle.py -q -p no:cacheprovider`: 54 passam.
- `python -B roda_verificacao_v5.py`, a partir da pasta v5: vermelho contra a v4, verde na v5, produto e regressões.
  Os caminhos do repositório estão no manifesto.
- A falha preexistente e alheia da suíte do produto é `tests/test_caracterizacao_blocos_atual.py::test_divisao_de_blocos_atual[Fundamentos-de-Redes-Tutor]`.
  Aparece igual antes e depois.
