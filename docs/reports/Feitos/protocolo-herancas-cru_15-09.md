# Dependência de heranças do produto: protocolo

Verificação autorizada pelo usuário após a correção da taxonomia direta.
Execução concluída; resultado em `herancas-cru_15-09.md`, neste diretório.
Baseline: `.frzero/implementacao_taxonomia_15-09`, fonte atual já medida nos 7 cursos.
Braço: `.frzero/cru_fontes_15-09/<Tutor>`, destino novo por curso.

## Entradas permitidas

- Arquivos locais da pasta `stash_folder` do perfil, importados por
  `scan_stash_cards` e `build_stash_entries`, mesma rota de import da UI.
- Plano, cronograma e identificação da matéria salvos em `SubjectProfile`.
- `.moodle_nomes.json` e `raw/moodle/contents.json` originais, quando presentes
  na árvore do download Moodle. Não são copiados do tutor-produto.
- Extração local `quick`, PyMuPDF4LLM; voter e compilação de vocabulário desligados.

Não entram manifest, queue salva, taxonomia, timeline, pinos, resumos, curadorias,
Markdown extraído ou cache do tutor-produto. O perfil salvo continua uma entrada
herdada explícita: este teste não certifica a captura original de plano/SARC.
URL sem cópia local é registrada como entrada ausente, sem chamada externa.

## Critérios definidos antes do placar

1. Construir os seis cursos e FR como controle, com inventário e hashes dos
   arquivos consumidos. Rede bloqueada e contada. Nenhum ajuste após ver o gold.
2. Associar materiais por caminho de origem local, único dos dois lados;
   ambiguidade não é resolvida usando o gold. IDs servem à régua depois do vínculo.
3. Publicar base completa e base comum. Entrada ausente não desaparece do
   denominador da base completa; sua perda é separada da falha de classificação.
4. Publicar ganhos/perdas em bloco, unidade, subunidade aceita e primária.
   O objetivo é diagnóstico, sem mínimo artificial de ganhos.
5. Rastrear diferenças observáveis de entrada, extração, estrutura e previsão.
   Diferenças simultâneas não provam causalidade isolada. Registrar essa limitação.

Cada curso recebe processo e destino exclusivos. Hashes são conferidos após o
build. O driver `cru_fontes_15-09.py` não importa a régua nem lê o produto; avaliação
é posterior e separada. Nenhuma alteração de `src/`, commit, push ou escrita nos
tutores-produto/.ablacao/.motor3eixos está incluída nesta medição.

## Achado de execução, antes de consultar placar

`core/html_material.py:_PageImages.replace` chama o transcritor Datalab para imagens
locais, mesmo com `image_description_source=none`. O tripwire conteve as tentativas
no CG. A rodada original fica registrada; execução limpa deve usar
`--sem-descricao-html`, que fixa `HTML_IMAGE_DATALAB_CAP=0` somente no processo.
Isso evidencia necessidade de configuração adicional para HTML offline. Não se
afirma que a UI já oferece esse comportamento. Não houve chamada externa efetiva.

A rodada original de CG foi interrompida após registrar o bloqueio, sem avaliação.
Arquivos parciais e log preservados. A reconstrução limpa usa destino novo
`.frzero/cru_fontes_semhtml_15-09` e log `cru_fontes_CG_semhtml_15-09.log`.
FR usa `.frzero/cru_fontes_controle_15-09`; TCC/SO usam o destino principal com
logs `cru_fontes_TCC_adiantado_15-09.log` e `cru_fontes_SO_adiantado_15-09.log`.

IA/MF originais foram interrompidos ainda na extração (50 threads por processo
observadas). Recomeçados sem reutilizar artefatos, em
`.frzero/cru_fontes_serial_15-09`, logs `cru_fontes_IA_serial_15-09.log` e
`cru_fontes_MF_serial_15-09.log`, com `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`
e `MKL_NUM_THREADS=1`. Mesmo extrator e entradas, sem consulta ao placar.
Os parciais originais permanecem preservados e não são avaliados.
