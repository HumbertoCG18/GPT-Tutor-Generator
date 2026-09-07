"""Regex compartilhadas do motor (consolidacao 07/09). Cada uma existia em dois modulos com o MESMO texto; aqui e a unica definicao,
os modulos de origem importam por alias. Nao mude o texto sem remedir as reguas."""
from __future__ import annotations

import re

# "1.3 - Estilos", "12 - Modelagem Geometrica", "3: ..." -> prefixo numerico de secao do Moodle / rotulo do plano
SECTION_NUM_PREFIX_RE = re.compile(r"^\s*\d+(\.\d+)*\s*[-.:]?\s*")

# "20/03/2026" com grupos (dia, mes, ano) — labels de semana e datas em nomes de modulo
DATE_DMY_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
