# Academic Tutor Repo Builder V3

Versão com **backends em camadas** para conversão de PDFs acadêmicos.

## O que a V3 adiciona
- seleção automática de backend por perfil do documento
- modos de processamento:
  - `quick`
  - `high_fidelity`
  - `manual_assisted`
  - `auto`
- camada base:
  - `PyMuPDF4LLM`
  - `PyMuPDF`
- camada avançada:
  - `Docling CLI`
  - `Marker CLI`
- extração de:
  - imagens embutidas
  - previews de páginas
  - tabelas em Markdown/CSV
  - detecção extra de tabelas via PyMuPDF
- geração de arquivos de política e arquitetura:
  - `system/BACKEND_ARCHITECTURE.md`
  - `system/BACKEND_POLICY.yaml`
  - `system/PDF_CURATION_GUIDE.md`

## Como rodar
```bash
python academic_tutor_repo_builder_v3.py
```

## Instalação de dependências
```bash
pip install -r requirements.txt
```

### Dependências mínimas recomendadas
```bash
pip install pymupdf pymupdf4llm pdfplumber
```

### Dependências avançadas opcionais
#### Docling CLI
Instale o Docling e garanta que o comando `docling` esteja disponível no terminal.

#### Marker CLI
```bash
pip install marker-pdf
```

## Desenvolvimento

### Configuração do ambiente
```bash
pip install -r requirements.txt
pip install pytest
```

### Executar testes
```bash
python -m pytest tests/ -v
```

## Como a decisão funciona
### `quick`
Usa preferencialmente:
- `pymupdf4llm`
- fallback `pymupdf`

### `high_fidelity`
Usa:
- camada base
- camada avançada quando disponível

### `manual_assisted`
Usa:
- camada base
- camada avançada para materiais difíceis
- revisão manual guiada obrigatória

### `auto`
Decide com base no perfil detectado:
- `general`
- `math_heavy`
- `layout_heavy`
- `scanned`
- `exam_pdf`

## Fluxo recomendado
1. criar o repositório pela GUI
2. revisar `manual-review/`
3. escolher a melhor saída entre base e avançada
4. corrigir fórmulas, tabelas e imagens importantes
5. promover o conteúdo para `content/`, `exercises/` e `exams/`
6. subir no GitHub

## Observação importante
A V3 foi feita para **preservar integridade**, não para “confiar cegamente” na extração.

Para materiais críticos de prova, a fonte final deve ser a versão curada após revisão manual.
