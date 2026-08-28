"""Parser de unidades do plano de ensino (src/builder/extraction/teaching_plan.py)."""
from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan


def test_template_pucrs_n_da_unidade_com_conteudo_em_bullet_e_topicos_de_um_nivel():
    """Lab de Redes 2026/2 (2026-08-28): "## **Nº DA UNIDADE:** 01" numa linha, o CONTEÚDO
    na seguinte rendido como item de lista, topicos "1. HTTP e HTTPS". Antes: 1 unidade, 0 topicos."""
    md = """## **CONTEÚDOS:**
## **Nº DA UNIDADE:** 01
- **CONTEÚDO:** Nível de aplicação - Configuração e análise de protocolos
1. HTTP e HTTPS
2. Configuração dinâmica de hosts (DHCP)
3. Sistemas de domínios de nomes (DNS)
## **Nº DA UNIDADE:** 02
- **CONTEÚDO:** Nível de transporte - protocolos TCP e UDP
1. Estudo de comportamento e funcionalidades
2. Análise de congestionamento
## **Nº DA UNIDADE:** 03
**CONTEÚDO:** Nível de rede
1. Protocolos IPv4 e IPv6
2. Protocolo ARP
## **PROCEDIMENTOS METODOLÓGICOS:**
Estão descritos em cada unidade do conteúdo.
## **AVALIAÇÃO:**
1. Isto não é tópico
"""
    units = _parse_units_from_teaching_plan(md)
    assert [t for t, _ in units] == [
        "Unidade 01 — Nível de aplicação - Configuração e análise de protocolos",
        "Unidade 02 — Nível de transporte - protocolos TCP e UDP",
        "Unidade 03 — Nível de rede",
    ]
    assert [[label for label, _ in tops] for _, tops in units] == [
        ["HTTP e HTTPS", "Configuração dinâmica de hosts (DHCP)", "Sistemas de domínios de nomes (DNS)"],
        ["Estudo de comportamento e funcionalidades", "Análise de congestionamento"],
        ["Protocolos IPv4 e IPv6", "Protocolo ARP"],
    ]


def test_topico_de_um_nivel_nao_vira_codigo_de_taxonomia():
    md = """## **Nº DA UNIDADE:** 01
**CONTEÚDO:** Nível de rede
1. Protocolos IPv4 e IPv6
4.1 Roteamento estático
"""
    (_, tops), = _parse_units_from_teaching_plan(md)
    # numerado multinivel presente => o de um nivel e descartado como nao-conteudo (regra existente
    # de _finalize_topics); o multinivel mantem o codigo no texto
    assert tops == [("4.1 Roteamento estático", 0)]
