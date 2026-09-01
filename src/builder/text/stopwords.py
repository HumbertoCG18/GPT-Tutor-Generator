"""Fonte única para todos os conjuntos de stopwords do builder.

Escopos DISTINTOS — não fundir:
  TIMELINE_GENERIC_TOKENS   : palavras genéricas de atividade/calendário (filtragem de eventos)
  TIMELINE_UNIT_NEUTRAL_TOKENS : termos técnicos que aparecem em TODA unidade (não discriminam)
  UNIT_GENERIC_TOKENS       : tokens genéricos do índice de unidades (roteamento file_map)
  UNIT_MATCHER_STOPWORDS    : stopwords PT + termos de estrutura para o matcher posicional
  CARD_BLOCK_STOP           : stopwords leves para resolução card→bloco
"""

# --- escopo: filtragem de eventos no cronograma ---
TIMELINE_GENERIC_TOKENS: frozenset = frozenset({
    "apresentacao", "assincrona", "assincrono", "atividade", "aula", "aulas",
    "caso", "complementar", "conteudo", "conteudos", "continuacao", "dia",
    "estudo", "estudos", "exercicio", "exercicios", "finalizacao", "gabarito",
    "gabaritos", "hora", "leituras", "lista", "listas", "materia", "material",
    "pagina", "paginas", "pratica", "praticas", "prova", "provas", "recomendadas",
    "recursos", "resposta", "respostas", "revisao", "revisoes", "semana",
    "teorica", "teoricas", "unidade",
})

# --- escopo: tokens neutros-para-unidade (aparecem em toda unidade, não discriminam) ---
TIMELINE_UNIT_NEUTRAL_TOKENS: frozenset = frozenset({
    "algoritmo", "algoritmos", "aplicacao", "aplicacoes", "computa",
    "computacao", "computacoes", "estado", "estados", "formais", "formal",
    "fundamentos", "logica", "logicas", "metodos", "modelo", "modelos",
    "para", "passo", "passos", "predicado", "predicados", "programa",
    "programas", "proposicional", "semantica", "sequencia", "sequencias",
    "simplificacao", "sintaxe", "sistemas", "software", "softwares",
    "substituicao", "suporte", "variaveis", "variavel", "verificacao",
    "verificacoes",
})

# --- escopo: tokens genéricos no índice de unidades (roteamento/file_map) ---
UNIT_GENERIC_TOKENS: frozenset = frozenset({
    "aplicacoes", "concorrentes", "especificacao", "especificacoes",
    "formais", "formal", "fundamentos", "linguagens", "logica", "logicas",
    "metodos", "modelo", "modelos", "programa", "programas", "propriedades",
    "sequenciais", "sistemas", "software", "softwares", "suporte",
    "verificacao", "verificacoes",
})

# --- escopo: genericos de UNIDADE calculados POR CURSO (A2, 2026-08-27) ---
# TIMELINE_UNIT_NEUTRAL_TOKENS e UNIT_GENERIC_TOKENS carregam vocabulario do Metodos Formais
# (formais, predicado, proposicional, sintaxe, verificacao...) numa constante global: no MF
# removem 9-10 palavras reais; na CG matam "fundamentos" (titulo da unidade 2). O que a lista
# tenta capturar e "palavra presente em quase toda unidade do plano" — isso e df por curso.
# Medido nos 6 cursos: df/n >= 0,4 sobre (titulo + topicos) reproduz a lista do MF onde ela
# acerta (formal/verificacao/logica em 3/3) e descobre SO "gerencia" 4/7, IA "aprendizagem"
# 5/5, ES2 "software", CG "algoritmos" 4/9, sem matar topico raro (CG "fundamentos" 1/9).
UNIT_STRUCTURAL_TOKENS: frozenset = frozenset({"unidade", "aprendizagem", "modulo", "parte", "topico"})
UNIT_GENERIC_MODE_ENV = "UNIT_GENERIC_MODE"  # df (default desde 2026-08-27) | lista (constantes antigas) | ambos


def unit_generic_tokens_from_units(units, share: float = 0.4, min_len: int = 4) -> frozenset:
    """Tokens presentes em >= `share` das unidades (titulo + rotulos dos topicos) + estruturais.

    `units`: iteravel de (title, topics) ou dicts {title, topics}; topics = str | (label, depth) | dict."""
    import os
    from src.builder.text.normalize import normalize_match_text

    def _texto(unit):
        if isinstance(unit, dict):
            title, topics = unit.get("title", ""), unit.get("topics", []) or []
        else:
            title, topics = unit[0], unit[1] or []
        parts = [str(title or "")]
        for t in topics:
            if isinstance(t, dict):
                parts.append(str(t.get("label") or t.get("title") or t.get("slug") or ""))
            elif isinstance(t, (tuple, list)):
                parts.append(str(t[0]))
            else:
                parts.append(str(t))
        return " ".join(parts)

    units = list(units or [])
    if not units:
        return UNIT_STRUCTURAL_TOKENS
    df: dict = {}
    for u in units:
        for tok in {w for w in normalize_match_text(_texto(u)).split() if len(w) >= min_len}:
            df[tok] = df.get(tok, 0) + 1
    n = len(units)
    generic = {tok for tok, c in df.items() if c / n >= share}
    return frozenset(generic | UNIT_STRUCTURAL_TOKENS)


def resolve_unit_generic_tokens(units, base, mode: str | None = None, course_name: str = ""):
    """Seleciona o conjunto de genericos de unidade conforme UNIT_GENERIC_MODE:
    df (DEFAULT) = calculado por curso + nome do curso · lista = None (cada consumidor usa a SUA
    constante antiga: byte-identico ao regime anterior) · ambos = uniao de `base` com o calculado.
    Medido nos 6 cursos (2026-08-27): df = 199/200 · 191/191 · cobertura 41/57 (+1) · subunidade 87/93;
    ambos nao ganha nada; lista era o regime anterior (40/57)."""
    import os
    mode = (mode or os.environ.get(UNIT_GENERIC_MODE_ENV) or "df").strip().lower()
    if mode == "lista":
        return None
    from src.builder.text.normalize import normalize_match_text
    # Nome do curso e boilerplate tambem no eixo de unidade: "Computacao Grafica" esta no cabecalho de
    # todo PDF da CG e a u09 ("Temas ... de Computacao Grafica") casava tudo (medido 2026-08-27).
    curso = {w for w in normalize_match_text(course_name or "").split() if len(w) >= 4}
    calc = frozenset(set(unit_generic_tokens_from_units(units)) | curso)
    return calc if mode == "df" else frozenset(set(base or ()) | calc)


# --- escopo: stopwords PT + termos estruturais para matcher posicional bloco→unidade ---
UNIT_MATCHER_STOPWORDS: frozenset = frozenset({
    "a", "ao", "aos", "as", "aula", "com", "da", "das", "de", "do", "dos",
    "e", "em", "introducao", "modulo", "na", "nas", "no", "nos", "o", "os",
    "para", "parte", "que", "sobre", "um", "uma",
})

# --- escopo: stopwords leves para resolução card→bloco ---
CARD_BLOCK_STOP: frozenset = frozenset({
    "a", "da", "de", "do", "e", "em", "o", "of", "para", "por", "the",
})


# Palavras-funcao PT curtas (2-3 chars): NUNCA viram vocabulario consagrado de
# curso (short-vocab, 2026-09-01) mesmo aparecendo em label de topico — "Redes
# SEM fio" consagra "fio", nao "sem". Preposicoes/artigos/conjuncoes apenas;
# "pre"/"pos" (Pre e Pos Condicoes, MF) sao DISTINTIVOS e ficam de fora daqui.
SHORT_FUNCTION_WORDS_PT: frozenset = frozenset({
    "de", "e", "a", "o", "da", "do", "em", "com", "por", "as", "os",
    "na", "no", "ao", "aos", "das", "dos", "um", "uma", "uns", "sem",
    "sob", "ou", "que", "se", "ate", "mas", "ja", "la", "seu", "sua",
})


def short_vocab_from_topic_labels(labels) -> frozenset:
    """Tokens CURTOS (2-3 chars) consagrados pelos LABELS de topico do curso.

    Fenomeno medido no holdout FR (2026-09-01): os tokenizadores cortam
    len<4 e o plano de redes so usa SIGLAS ("Protocolo TCP/UDP/ARP/ICMP",
    "Modelos OSI e TCP/IP") — o unico token distintivo desses labels era
    invisivel e o scorer de subunidade decidia por migalhas (02-modelos
    conf 0.92 ERRADO; 05-dns em 'usuario' com dns invisivel). A allowlist e
    POR CURSO e vem do proprio plano: "tcp" vale no FR porque um label o
    consagra; segue ruido no MF, onde nenhum label o tem. CG (2d/3d/ray),
    TCC (np) e ES2 (ci/cd) tem o mesmo fenomeno em menor grau.
    """
    vocab = set()
    for label in labels or []:
        for token in str(label or "").split():
            if 2 <= len(token) <= 3 and token not in SHORT_FUNCTION_WORDS_PT and not token.isdigit():
                vocab.add(token)
    return frozenset(vocab)
