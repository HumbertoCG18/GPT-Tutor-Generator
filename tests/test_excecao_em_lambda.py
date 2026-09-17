"""Regressao: lambda dentro de except nao pode usar a variavel da excecao sem bind.

A PEP 3110 apaga o nome ao fim do bloco except. Quando o lambda roda depois
(fila do Tk, via after()), o nome nao existe mais e o proprio handler de erro
estoura NameError — a mensagem que deveria dizer o que falhou quebra sozinha.

Teste por AST, e nao por sitio: a suite nao instancia Tk, e a regra vale para
todo o src/, nao so para os tres casos encontrados em 09/09.
"""

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "src"


def _lambdas_que_vazam(arvore: ast.AST):
    """Devolve (nome_da_excecao, linha) de lambda que usa a variavel sem bind."""
    achados = []
    for no in ast.walk(arvore):
        if not isinstance(no, ast.ExceptHandler) or not no.name:
            continue
        for interno in ast.walk(no):
            if not isinstance(interno, ast.Lambda):
                continue
            # bind por argumento (default ou kwonly) congela o valor e resolve
            ligado = {a.arg for a in interno.args.args}
            ligado |= {a.arg for a in interno.args.kwonlyargs}
            if no.name in ligado:
                continue
            for usado in ast.walk(interno.body):
                if isinstance(usado, ast.Name) and usado.id == no.name:
                    achados.append((no.name, interno.lineno))
                    break
    return achados


def test_nenhum_lambda_usa_variavel_de_excecao_sem_bind():
    falhas = []
    for arquivo in sorted(RAIZ.rglob("*.py")):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))
        for nome, linha in _lambdas_que_vazam(arvore):
            falhas.append(f"{arquivo.relative_to(RAIZ.parent)}:{linha} usa `{nome}`")

    assert not falhas, (
        "lambda captura variavel de excecao que a PEP 3110 apaga ao fim do except; "
        "quando o lambda roda, estoura NameError. Corrija com bind por argumento "
        "(lambda exc=" + "e: ...):\n  " + "\n  ".join(falhas)
    )
