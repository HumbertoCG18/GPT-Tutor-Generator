# Pacote completo de fontes: protocolo executado

Autorizado: reconstrução nova dos sete cursos, com stash original, perfil salvo
(plano/SARC) e captura Moodle local. Sem src, .ablacao, .motor3eixos ou produto
como destino; sem LLM, commits ou push. Não transplantar campos de decisões.

Driver reaproveita cru_fontes_15-09.py e seu bloqueio de rede. Única extensão:
copiar payload contents.json validado por hash para o destino novo; depois do
build, chamar backfills Moodle existentes (aditivo e consumido) e reprocessar.
Primeiro build gera o cronograma necessário ao parsing de datas. Último passe
regenera estrutura por ano do cronograma. Nenhum mapa de cards pronto é copiado.

Extração documental usa o mesmo regime local da referência, cap zero para imagens
HTML. Metadados de plataforma vêm da captura; nenhum MD Datalab é substituído por
outro MD nesta etapa. Preferência Datalab permanece para a frente documental,
que não é fator deste contraste. Perfil salvo continua entrada herdada declarada.

| Faixa | Destino exclusivo | Gate |
|---|---|---|
| ES2/IA | .frzero/pacote_fontes_15-09 por tutor | fontes + rede + conclusão |
| MF/SO | mesmo pai, tutores diferentes | fontes + rede + conclusão |
| TCC/CG/FR | mesmo pai, tutores diferentes | fontes + rede + conclusão |

Verificação: hashes das fontes antes/depois; zero tentativas de rede; nenhum
pino/curadoria de benchmark importado; conjuntos de entradas e estrutura temporal
comparáveis. Derivados novos podem mudar com os metadados, portanto não exigir
taxonomia idêntica como no contraste anterior. Antes de gold ordinal, conferir
IDs/datas/sessões dos blocos. Divergência temporal suspende a pontuação afetada.

Pontuar depois do build, mesmos 316 materiais da régua, ausentes no denominador;
também reportar comuns. Referência imediata: 169/234/99/76. Publicar ganhos e
perdas por eixo, não só saldo. Resultado positivo não autoriza promoção ao produto.
