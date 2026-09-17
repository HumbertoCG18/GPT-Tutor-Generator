**Executado pelo Astra LOW, somente leitura: 25 candidatos → 3 relações novas admissíveis após auditoria. IA: nenhuma.**

1. **Protocolo congelado**

   - Fontes: os oito diretórios autorizados; taxonomia somente `label/code/kind/unit_slug`; `COURSE_MAP.md`; campos Moodle permitidos; primeiro markdown existente em `approved_markdown/curated_markdown/base_markdown`.
   - Markdown escolhido para dispensar PDF e dependências. Remover `IMAGE_DESCRIPTION`, preservando linhas; bloco sem fechamento invalida a leitura do documento.
   - Âncora: igualdade normalizada com rótulo completo ou prefixo anterior a parêntese final contendo enumeração. Sem equivalências semânticas.
   - Padrões: `categoria: itens`, `categoria (itens)` e bullets após heading correspondente. Vírgula/ponto-e-vírgula delimitam as duas primeiras formas.
   - Item: 2–80 caracteres, 1–8 palavras; rejeitar genéricos, negação, verbos e sintaxes definidos no código. Âncora ambígua rejeitada. Auditoria descarta prosa, citações, definições e itens não atomizados. Nenhum padrão ajustado após observar candidatos.

2. **Código completo executado**

   **Ressalva:** `admissivel` no JSON representa o filtro automático, que produziu falsos positivos. A auditoria do item 3 prevalece; o código congelado não deve alimentar o motor sem essa revisão.

```python
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path("C:/Users/Humberto/Documents/GitHub")
COURSES = [
    ("MF", ROOT / "Metodos-Formais-Tutor"),
    ("SO", ROOT / "Sistemas-Operacionais-Tutor"),
    ("IA", ROOT / "Inteligencia-Artifical-Tutor"),
    ("ES2", ROOT / "Engenharia-Software-2-Tutor"),
    ("TCC", ROOT / "TCC-Tutor"),
    ("CG", ROOT / "Computacao-Grafica-Tutor"),
    ("FR", ROOT / "Fundamentos-de-Redes-Tutor"),
    ("FRzero", ROOT / "GPT-Tutor-Generator/.frzero/base"),
]
GENERIC = {"exemplo", "exemplos", "outro", "outros", "etc", "introducao",
           "conceito", "conceitos", "atividade", "atividades", "exercicio",
           "exercicios", "objetivo", "objetivos", "conteudo", "conteudos"}
NEGATION = {"nao", "sem", "exceto", "exclui", "excluindo", "nunca", "nem"}
VERBS = {"explique", "descreva", "compare", "implemente", "responda",
         "defina", "calcule", "resolva", "estude", "leia", "veja",
         "sao", "estao", "pode", "podem", "deve", "devem", "permite",
         "permitem", "utiliza", "utilizam", "consiste", "consistem"}
BULLET = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+(.+?)\s*$")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
FORBIDDEN = re.compile(
    r"glossary|glossary_curation|code_curation|_gt_|ground_truth_|"
    r"contradicoes_|erros_subunidade_|teto_aquisicao_|scores_pai_filho_|"
    r"diagnostico_|pai_filho_|evidencia_fora_do_bundle_", re.I)

def norm(s):
    s = unicodedata.normalize("NFKD", s.casefold())
    return " ".join(re.findall(r"[a-z0-9]+",
                   "".join(c for c in s if not unicodedata.combining(c))))

def clean(s):
    return re.sub("[*_" + chr(96) + "]", "", s).strip().rstrip(".").strip()

def parts(s):
    return [clean(x) for x in re.split(r"[,;]", s) if clean(x)]

def strip_images(s):
    opening = r"<!--\s*IMAGE_DESCRIPTION\b"
    complete = opening + r".*?<!--\s*/IMAGE_DESCRIPTION\s*-->"
    s = re.sub(complete, lambda m: "\n" * m[0].count("\n"), s,
               flags=re.S | re.I)
    if re.search(opening, s, re.I):
        raise ValueError("IMAGE_DESCRIPTION sem fechamento")
    return s

def anchor_names(label):
    yield norm(label)
    m = re.fullmatch(r"(.*?)\s*\(([^()]*)\)\s*", label)
    if m and len(parts(m[2])) >= 2:
        yield norm(m[1])

def classify(term, context):
    words = set(norm(term).split())
    if not 2 <= len(term) <= 80 or not 1 <= len(norm(term).split()) <= 8:
        return False, "tamanho"
    if words & GENERIC:
        return False, "generico"
    if set(norm(context).split()) & NEGATION:
        return False, "negacao"
    if words & VERBS or re.search(r"https?://|[!?=<>]|\([^)]*$", term):
        return False, "frase_ou_sintaxe"
    if not re.search(r"[^\W\d_]", term, re.UNICODE):
        return False, "sem_letras"
    return True, "relacao_local_explicita"

def scan(lines):
    active = None
    fence = False
    for i, raw in enumerate(lines, 1):
        if re.match(r"^\s*(" + chr(96) * 3 + r"|~~~)", raw):
            fence = not fence
            active = None
            continue
        if fence:
            continue
        h = HEADING.match(raw)
        b = BULLET.match(raw)
        line = clean(h[1] if h else b[1] if b else raw)
        if h:
            active = (line, i, raw)
        elif b and active:
            yield active[0], line, "subtitulo_lista", i, active[2] + "\n" + raw
        elif raw.strip():
            active = None
        m = re.fullmatch(r"([^:()]+):\s*(.+)", line)
        if m and len(parts(m[2])) >= 2:
            for term in parts(m[2]):
                yield clean(m[1]), term, "categoria_dois_pontos", i, raw
        m = re.fullmatch(r"([^:()]+)\s*\(([^()]+)\)", line)
        if m and len(parts(m[2])) >= 2:
            for term in parts(m[2]):
                yield clean(m[1]), term, "categoria_parenteses", i, raw

def main():
    assert strip_images("a\n<!-- IMAGE_DESCRIPTION x -->\ny\n<!-- /IMAGE_DESCRIPTION -->\nb") == "a\n\n\n\nb"
    assert list(anchor_names("A (B, C)")) == ["a b c", "a"]
    assert list(anchor_names("A (geral)")) == ["a geral"]
    assert not classify("nao TCP", "nao TCP")[0]
    for course, base in COURSES:
        base = base.resolve()
        stats = collections.Counter()
        problems = []
        anchors = collections.defaultdict(list)
        taxonomy = base / "course/.content_taxonomy.json"
        manifest = base / "manifest.json"
        if not taxonomy.exists() or not manifest.exists():
            print(json.dumps({"curso": course, "erro": "taxonomia/manifest ausente"},
                             ensure_ascii=False), file=sys.stderr)
            continue
        data = json.loads(taxonomy.read_text(encoding="utf-8-sig"))
        for unit in data["units"]:
            for raw in unit["topics"]:
                topic = {k: raw.get(k, "") for k in ("label", "code", "kind", "unit_slug")}
                if topic["kind"] != "topic":
                    continue
                stats["topicos"] += 1
                for key in set(anchor_names(topic["label"])):
                    if key:
                        anchors[key].append(topic)
        entries = json.loads(manifest.read_text(encoding="utf-8-sig"))["entries"]
        sources = {}
        course_map = base / "course/COURSE_MAP.md"
        if course_map.exists():
            sources[str(course_map)] = course_map
        else:
            problems.append("COURSE_MAP ausente")
        metadata = []
        for index, entry in enumerate(entries):
            stats["entries"] += 1
            for key in ("source_section", "moodle_label"):
                value = entry.get(key)
                if isinstance(value, str) and value.strip():
                    metadata.append((str(manifest) + "#entries/" + str(index) + "/" + key, value))
            found = False
            for key in ("approved_markdown", "curated_markdown", "base_markdown"):
                value = entry.get(key)
                if not isinstance(value, str) or not value:
                    continue
                path = (base / value).resolve()
                if not path.is_relative_to(base) or FORBIDDEN.search(str(path)) or path.suffix.lower() != ".md":
                    problems.append("path rejeitado: " + str(path))
                    continue
                if path.exists():
                    sources[str(path)] = path
                    found = True
                    break
                problems.append("path ausente: " + str(path))
            stats["entries_com_markdown" if found else "entries_sem_markdown"] += 1
        documents = []
        for filename, path in sorted(sources.items()):
            try:
                documents.append((filename, strip_images(path.read_text(encoding="utf-8-sig"))))
                stats["arquivos_lidos"] += 1
            except (OSError, UnicodeError, ValueError) as error:
                problems.append(filename + ": " + str(error))
        documents.extend(metadata)
        stats["campos_moodle"] = len(metadata)
        seen = set()
        unique_new = set()
        for filename, document in documents:
            for category, term, pattern, line, excerpt in scan(document.splitlines()):
                matched = anchors.get(norm(category), [])
                for topic in matched:
                    identity = (filename, line, topic["unit_slug"], topic["code"],
                                topic["label"], norm(term))
                    if identity in seen:
                        continue
                    seen.add(identity)
                    admissible, reason = classify(term, excerpt)
                    if len(matched) > 1:
                        admissible, reason = False, "ancora_ambigua"
                    in_label = (" " + norm(term) + " ") in (" " + norm(topic["label"]) + " ")
                    row = dict(curso=course, topic_code=topic["code"],
                               topic_label=topic["label"], termo=term, padrao=pattern,
                               arquivo=filename, linha=line, trecho=excerpt,
                               ja_no_rotulo=in_label, admissivel=admissible, motivo=reason)
                    print(json.dumps(row, ensure_ascii=False))
                    stats["candidatos"] += 1
                    if admissible:
                        stats["admissiveis"] += 1
                        if not in_label:
                            stats["admissiveis_novos"] += 1
                            unique_new.add((topic["unit_slug"], topic["code"], topic["label"], norm(term)))
        stats["relacoes_novas_unicas"] = len(unique_new)
        for key in ("candidatos", "admissiveis", "admissiveis_novos"):
            stats[key] += 0
        print(json.dumps({"curso": course, "totais": dict(stats), "problemas": problems},
                         ensure_ascii=False), file=sys.stderr)

if __name__ == "__main__":
    main()
```

3. **Resultado e auditoria**

Execução: `python -B -`, saída 0, 2,62 s. Cobertura: 361 entradas, 313 com markdown e 48 sem; 321 arquivos, incluindo oito `COURSE_MAP.md`; 763 campos Moodle. Nenhum erro reportado de leitura, caminho ou remoção de bloco.

| Curso | Candidatos | Admissíveis automáticos | Admissíveis auditados | Novos auditados |
|---|---:|---:|---:|---:|
| MF | 10 | 4 | 2 | 2 |
| SO | 8 | 5 | 1 | 1 |
| IA | 0 | 0 | 0 | 0 |
| ES2 | 3 | 1 | 0 | 0 |
| TCC | 4 | 2 | 0 | 0 |
| CG | 0 | 0 | 0 | 0 |
| FR | 0 | 0 | 0 | 0 |
| FRzero | 0 | 0 | 0 | 0 |
| **Total** | **25** | **12** | **3** | **3** |

Relações aceitas, todas pelo padrão `subtitulo_lista`, ausentes do próprio rótulo:

| Curso/tópico | Categoria | Termo literal | Fonte |
|---|---|---|---|
| MF `1.3` | Abordagens para Verificação Formal | `Verificação de Modelos (Model Checking):` | `introducao.md:190` |
| MF `1.3` | Abordagens para Verificação Formal | `Verificação Dedutiva:` | `introducao.md:198` |
| SO `7.4` | Proteção | `Bit de validade:` | `2105-laminas-paginacao.md:266` |

Os nove falsos positivos automáticos: seis bullets de prosa/descrição, uma lista de links não atomizada, uma citação `Turing, 1936` e uma definição de classe. **IA: nenhuma relação nova.**

**Veredito do passo 3:** há três relações novas admissíveis no corpus coberto; o critério de encerramento por zero não ocorreu. Ganho no motor permanece não medido.
