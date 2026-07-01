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
