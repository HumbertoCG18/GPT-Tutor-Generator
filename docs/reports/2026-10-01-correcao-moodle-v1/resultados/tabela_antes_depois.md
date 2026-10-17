| caso | grupo | delta (S4) | candidato V1 (S6) | asserções que falhavam no delta |
|---|---|---|---|---|
| M1a | M-01 | defeito reproduzido: IncompleteRead, 0 B, `''` | contrato ok: IncompleteRead, 3 B, `'abc'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; causa encadeada; corpo; partial |
| M1b | M-01 | defeito reproduzido: IncompleteRead, 2 B, `'[]'` | contrato ok: IncompleteRead, 5 B, `'[]abc'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; causa encadeada; corpo; partial |
| M1c | M-01 | defeito reproduzido: IncompleteRead, 0 B, `''` | contrato ok: IncompleteRead, 3 B, `'abc'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; causa encadeada; corpo; partial |
| M1d | M-01 | defeito reproduzido: IncompleteRead, 4 B, `'[]  '` | contrato ok: IncompleteRead, 7 B, `'[]  abc'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; causa encadeada; corpo; partial |
| A07 | M-01 | defeito reproduzido: IncompleteRead, 0 B, `''` | contrato ok: IncompleteRead, 3 B, `'abc'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; causa encadeada; corpo; partial |
| A08 | M-01 | defeito reproduzido: IncompleteRead, 3 B, `'[] '` | contrato ok: IncompleteRead, 6 B, `'[] abc'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; causa encadeada; corpo; partial |
| M2a | M-02 | defeito reproduzido: IncompleteRead, 2 B, `'[]'` | contrato ok: sucesso, 2 B | retorno; tipo |
| M2b | M-02 | defeito reproduzido: sucesso, 2 B | contrato ok: OrcamentoExcedido, 2 B, `'[]'` | tipo |
| M2c | M-02 | defeito reproduzido: OrcamentoExcedido, 0 B, `''` | contrato ok: sucesso, 2 B | bytes; corpo; retorno; tipo |
| A02 | M-02 | defeito reproduzido: OrcamentoExcedido, 0 B, `''` | contrato ok: sucesso, 2 B | bytes; corpo; retorno; tipo |
| A03 | M-02 | defeito reproduzido: sucesso, 2 B | contrato ok: OrcamentoExcedido, 2 B, `'[]'` | tipo |
| A12 | M-02 | defeito reproduzido: OrcamentoExcedido, 0 B, `''` | contrato ok: sucesso, 2 B | bytes; corpo; retorno; tipo |
| A16 | M-02 | defeito reproduzido: OrcamentoExcedido, 0 B, `''` | contrato ok: sucesso, 2 B | bytes; corpo; retorno; tipo |
| A18 | P-01 | defeito reproduzido: LineTooLong, 0 B, `''` | contrato ok: LineTooLong, 2 B, `'[]'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; corpo |
| A19 | P-01 | defeito reproduzido: LineTooLong, 0 B, `''` | contrato ok: LineTooLong, 2 B, `'[]'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; corpo |
| A20 | P-01 | controle verde: LineTooLong, 2 B, `'[]'` | contrato ok: LineTooLong, 2 B, `'[]'` | — |
| A33 | P-01 | defeito reproduzido: TimeoutError, 0 B, `''` | contrato ok: TimeoutError, 2 B, `'[]'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; corpo |
| A34 | P-01 | defeito reproduzido: TimeoutError, 0 B, `''` | contrato ok: TimeoutError, 2 B, `'[]'` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; bytes; corpo |
| A21 | P-02 | defeito reproduzido: IncompleteRead, 3 B, `'[] '` | contrato ok: IncompleteRead, 0 B, `''` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; R2: bytes entregues do trecho proibido; R2: operação no trecho proibido; bytes; corpo; partial; tamanho negativo lido e nada depois |
| A22 | P-02 | defeito reproduzido: IncompleteRead, 23 B | contrato ok: IncompleteRead, 0 B, `''` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; R2: bytes entregues do trecho proibido; R2: operação no trecho proibido; R2: pedido de payload acima do saldo; bytes; corpo; partial; tamanho negativo lido e nada depois |
| A35 | P-02 | defeito reproduzido: OrcamentoExcedido, 0 B, `''` | contrato ok: IncompleteRead, 0 B, `''` | tamanho negativo lido e nada depois; tipo |
| A23 | R5 | regra nova ausente no delta: sucesso, 2 B | contrato ok: UnknownTransferEncoding, 0 B, `''` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; R2: bytes entregues do trecho proibido; R2: operação no trecho proibido; bytes; corpo; nenhuma operação no corpo; tipo |
| A24 | R5 | regra nova ausente no delta: JSONDecodeError, 12 B, `'2\r\n[]\r\n0\r\n\r\n'` | contrato ok: UnknownTransferEncoding, 0 B, `''` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; R2: bytes entregues do trecho proibido; R2: operação no trecho proibido; bytes; corpo; nenhuma operação no corpo; tipo |
| TE-REPETIDO | R5 | regra nova ausente no delta: sucesso, 2 B | contrato ok: UnknownTransferEncoding, 0 B, `''` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; R2: bytes entregues do trecho proibido; R2: operação no trecho proibido; bytes; corpo; nenhuma operação no corpo; tipo |
| TE-IDENTITY | R5 | regra nova ausente no delta: sucesso, 2 B | contrato ok: UnknownTransferEncoding, 0 B, `''` | R1/R3: contador = payload entregue pelo fio; R1/R3: corpo = payload entregue pelo fio; R2: bytes entregues do trecho proibido; R2: operação no trecho proibido; bytes; corpo; nenhuma operação no corpo; tipo |
| TE-CAIXA | R5 | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| C02 | terminal | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| A01 | terminal | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| SO-ZERO | terminal | controle verde: JSONDecodeError, 0 B, `''` | contrato ok: JSONDecodeError, 0 B, `''` | — |
| SO-ZERO-LIMITE | terminal | controle verde: JSONDecodeError, 0 B, `''` | contrato ok: JSONDecodeError, 0 B, `''` | — |
| C16 | crlf | controle verde com assercao nova vermelha: IncompleteRead, 2 B, `'[]'` | contrato ok: IncompleteRead, 2 B, `'[]'` | causa encadeada |
| C17 | crlf | controle verde com assercao nova vermelha: IncompleteRead, 2 B, `'[]'` | contrato ok: IncompleteRead, 2 B, `'[]'` | causa encadeada |
| A09 | crlf | controle verde com assercao nova vermelha: IncompleteRead, 2 B, `'[]'` | contrato ok: IncompleteRead, 2 B, `'[]'` | causa encadeada |
| C09 | read1-curto | controle verde: sucesso, 5 B | contrato ok: sucesso, 5 B | — |
| CHUNK-CURTO | read1-curto | controle verde: sucesso, 5 B | contrato ok: sucesso, 5 B | — |
| CHUNK-MAIOR-QUE-BLOCO | read1-curto | controle verde: sucesso, 10 B | contrato ok: sucesso, 10 B | — |
| TIMEOUT-PAYLOAD | timeout-payload | novo registrado: TimeoutError, 0 B, `''` | contrato ok: TimeoutError, 2 B, `'[1'` | bytes; corpo |
| C04 | sem-CL | controle verde: OrcamentoExcedido, 2 B, `'[]'` | contrato ok: OrcamentoExcedido, 2 B, `'[]'` | — |
| C05 | sem-CL | controle verde: OrcamentoExcedido, 2 B, `'[]'` | contrato ok: OrcamentoExcedido, 2 B, `'[]'` | — |
| C10 | sem-CL | controle verde: sucesso, 5 B | contrato ok: sucesso, 5 B | — |
| C12 | sem-CL | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| C01 | CL | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| C11 | CL | controle verde: IncompleteRead, 2 B, `'[]'` | contrato ok: IncompleteRead, 2 B, `'[]'` | — |
| C19 | CL | controle verde: sucesso, 65536 B | contrato ok: sucesso, 65536 B | — |
| C20 | CL | controle verde: sucesso, 65539 B | contrato ok: sucesso, 65539 B | — |
| C03 | saldo-exato | controle verde: OrcamentoExcedido, 2 B, `'[]'` | contrato ok: OrcamentoExcedido, 2 B, `'[]'` | — |
| A31 | saldo-exato | controle verde: OrcamentoExcedido, 2 B, `'[]'` | contrato ok: OrcamentoExcedido, 2 B, `'[]'` | — |
| C06 | controles | controle verde: OrcamentoExcedido, 0 B, `''` | contrato ok: OrcamentoExcedido, 0 B, `''` | — |
| C07 | controles | controle verde: OrcamentoExcedido, 0 B, `''` | contrato ok: OrcamentoExcedido, 0 B, `''` | — |
| C08 | controles | controle verde: OrcamentoExcedido, 0 B, `''` | contrato ok: OrcamentoExcedido, 0 B, `''` | — |
| C13 | controles | controle verde: JSONDecodeError, 5 B, `'[]xxx'` | contrato ok: JSONDecodeError, 5 B, `'[]xxx'` | — |
| C14 | controles | controle verde: UnicodeDecodeError, 1 B, `'ÿ'` | contrato ok: UnicodeDecodeError, 1 B, `'ÿ'` | — |
| C15 | controles | controle verde: RuntimeError, 58 B | contrato ok: RuntimeError, 58 B | — |
| C18 | controles | controle verde com assercao nova vermelha: IncompleteRead, 2 B, `'[]'` | contrato ok: IncompleteRead, 2 B, `'[]'` | causa encadeada |
| A04 | controles | controle verde com assercao nova vermelha: IncompleteRead, 0 B, `''` | contrato ok: IncompleteRead, 0 B, `''` | causa encadeada |
| A05 | controles | controle verde com assercao nova vermelha: IncompleteRead, 2 B, `'[]'` | contrato ok: IncompleteRead, 2 B, `'[]'` | causa encadeada |
| A06 | controles | controle verde com assercao nova vermelha: IncompleteRead, 0 B, `''` | contrato ok: IncompleteRead, 0 B, `''` | causa encadeada |
| A17 | controles | controle verde com assercao nova vermelha: IncompleteRead, 2 B, `'[]'` | contrato ok: IncompleteRead, 2 B, `'[]'` | causa encadeada |
| A11 | tolerancias | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| A13 | tolerancias | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| A14 | tolerancias | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| A15 | tolerancias | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| A32 | tolerancias | controle verde: sucesso, 2 B | contrato ok: sucesso, 2 B | — |
| R02 | retencao | controle verde: seq. | contrato ok: seq. | — |
