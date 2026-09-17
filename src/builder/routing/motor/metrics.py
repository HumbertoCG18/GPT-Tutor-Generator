"""Métricas do gate D4 (FASE 1): recall do gate sobre decisões ANCORADAS.

Puro (stdlib): consumido pelo harness externo (scripts/fase1_recall_gate_MF.py)
e reutilizável pelo Dashboard na FASE 4. Funil (None) NÃO entra aqui — recall
do gate mede só o que o motor ancorou.
"""
from __future__ import annotations

from typing import Dict, List


def gate_report(outcomes: List[dict]) -> Dict[str, object]:
    """Agrega outcomes ancorados em métricas do gate D4.

    outcome: {"correct": bool, "band": str, "flag": bool, "method": str}.
    recall_gate = erros_flagados / erros (1.0 quando não há erros — gate sem
    erro para pegar não é gate ruim).
    """
    total = len(outcomes)
    erros = [o for o in outcomes if not o.get("correct")]
    erros_flagados = [o for o in erros if o.get("flag")]
    confiante_errado = [o for o in erros if str(o.get("band")) == "alta"]
    flagged = [o for o in outcomes if o.get("flag")]
    janela1_erros = [o for o in erros if str(o.get("method")) == "janela-1"]
    return {
        "total": total,
        "erros": len(erros),
        "erros_flagados": len(erros_flagados),
        "confiante_errado": len(confiante_errado),
        "recall_gate": (len(erros_flagados) / len(erros)) if erros else 1.0,
        "flagged_total": len(flagged),
        "flagged_certos": len([o for o in flagged if o.get("correct")]),
        "janela1_erros": len(janela1_erros),
    }
