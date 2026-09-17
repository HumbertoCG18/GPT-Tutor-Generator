# Brief 9 para o astra (read-only, esforco LOW): singular x plural na subunidade vale um braco? — 2026-09-13

Ordem do usuario: *"delegue o astra no low para isso"* — "isso" = o proximo passo que propus: tratamento de singular/plural na
subunidade, atras de flag desligada, medido no FR construido do zero e nos 7 cursos. **Resposta curta. Verifique a minha
aritmetica antes de qualquer desenho.** MEDIDO x HIPOTESE, `arquivo:linha`.

## 1. Contexto minimo

- Meta do usuario: bloco, unidade e subunidade >= 95% (primario) **sem LLM, sem gold, motor modular**.
- FR construido do zero (unico curso so com fontes do professor, 0 chamadas): subunidade primario **6/18**. Com vocab
  compilado por LLM: 16/18.
- Licao de hoje: desligar a propagacao de headings deu **+2 no FR do zero e saldo ZERO nos 7 cursos** (5 ganhos, 5 perdas,
  CG -3). **Ganho no FR nao transfere por padrao.**

## 2. Os 5 erros do FR do zero atribuidos a singular x plural (score real do motor, `diagnostico_frzero_13-09.log`)

| material | texto do material | topico do gold | score do gold | vencedor (score) |
|---|---|---|---|---|
| tcp-chat-c, tcp-example, udp-example-c, udp-example-java | resumo deterministico com "socket", "cliente/servidor" | `2.2.1 Implementacao de sockets` (subtopico) | **0,017** | `2.2 Paradigmas cliente/servidor e P2P` (**0,91**) |
| 01-protocolos-de-rede | titulo "Protocolos de Rede" | `1.3 Conceito de protocolo de redes pessoais, locais, metropolitanas e de longa distancia` | **0,00** | `1.2 Modelos OSI e TCP/IP` (0,11, conf 1,000) |

## 3. O codigo relevante

`src/builder/timeline/index.py:141-162` — casamento de frase:
```python
if " " not in normalized_phrase:
    return normalized_phrase in _signal_token_set(normalized_signal)   # token unico: pertinencia EXATA
if normalized_phrase in normalized_signal:
    return True                                                         # frase: substring exata
if not stem_fallback:
    return False
# stem6 so com stem_fallback=True, hoje ligado SO na rota de topico do mapeador de UNIDADE (file_map.py:514)
```
Comentario na linha 142: *"stem6 ligado globalmente derrubou subunidade 87->83 e bloco 199->198"* — negativo anterior no
mesmo espaco.

`index.py:1859-1943` — overlap de tokens: `topic_tokens` = tokens >= 4 chars (ou short_vocab) do label, aliases e slug, menos
genericos; `signal_tokens` = tokens dos campos. Depois:
```python
elif len(topic_tokens) == 1:            score += 0.9 if overlap
elif len(overlap) >= len(topic_tokens): score += 1.4 + 0.22*len(overlap)
elif len(overlap) >= 2:                 score += 0.9 + 0.18*len(overlap)
elif len(overlap) == 1:                 score += 0.25
if kind == "subtopic":                  score += 0.04
if exact_hits == 0 and score > 0:       score *= 0.72
if exact_hits == 0 and len(overlap) <= 1: score *= 0.68
```
O scorer e INJETADO nos mapeadores de unidade e subunidade na importacao do engine (`engine.py:2274`), entao um braco exige
flag no codigo, nao monkeypatch.

## 4. A MINHA ARITMETICA (hipotese — nao rodei o motor), e o que eu quero que voce confirme ou derrube

**Zips:** singularizando os dois lados, `Implementacao de sockets` tem topic_tokens {implementacao, socket}; o resumo so tem
"socket" -> overlap 1 de 2 -> (0,25 + 0,04) x 0,72 x 0,68 ~= **0,14**. O pai `Paradigmas cliente/servidor` ja tem overlap 2
("cliente", "servidor") e fica em **0,91**. **Conclusao: singularizar NAO vira os 4 zips.** O que os perde e o pai com dois
tokens contra o filho com um — competicao pai x filho, nao plural.

**01-protocolos:** singularizando, "Protocolos de Rede" -> {protocolo, rede} casa 2 tokens do gold -> ~(0,9 + 0,36) x 0,72
~= 0,9 contra 0,11 -> **provavelmente vira**. Se "redes"/"rede" for token generico do curso, cai para overlap 1 e nao vira.

**Se a aritmetica estiver certa, o mecanismo vale ~1 de 12 no FR, nao 5**, e eu superestimei a alavanca na resposta ao usuario.

## 5. O que eu quero (curto)

1. **A aritmetica da §4 esta certa?** Se nao, onde erra.
2. **Vale um braco?** Dado o negativo do stem6 e o tamanho real, sim ou nao, e por que.
3. **Se sim:** a costura minima (qual funcao, quais campos, os dois lados ou so um, qual regra de singular evita o que
   derrubou o stem6) e o criterio de aceite (FR do zero + 7 cursos, sem regredir bloco/unidade).
4. **Se nao:** entre os 12 erros do FR do zero (plural 5, 2a passada quebrando acerto 2, "camada" x "nivel" 2, empate 2,
   migalha com conf 1,000 1), **qual e o proximo mecanismo com maior ganho esperado por risco** — e a competicao pai x filho
   dos zips e um mecanismo proprio que valha olhar?
5. **O que NAO fazer.**
