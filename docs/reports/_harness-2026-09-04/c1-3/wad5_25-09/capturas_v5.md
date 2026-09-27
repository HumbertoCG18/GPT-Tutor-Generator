# W-AD5 — captura dos sete braços, sem gold (25/09)

Congelamento comum: `3fe5d1ff97258644b3148860cbe235aa3e16acfac91e9a291ea3c3e63a8e355d`.
Resultado: **APROVADO**

## Condições

- ✅ preflight v5 aprovado com este congelamento
- ✅ processo, código, src/ e distribuições = congelamento (início)
- ✅ CAPTURA_LIBERADA = os sete braços
- ✅ inventário de entradas confere (início)
- ✅ sete capturas completas, validador completo sem problemas
- ✅ 350 registros por captura, IDs = inventário congelado
- ✅ mesmo congelamento comum e insumos do próprio braço
- ✅ nenhuma violação nas capturas
- ✅ arquivos de captura = conteúdo validado
- ✅ palcos e snapshots = insumos congelados (fim)
- ✅ código, src/ e distribuições = congelamento (fim)
- ✅ entradas comuns preservadas (árvores inteiras)
- ✅ inventário de entradas confere (fim)
- ✅ coordenador sem violações

## Capturas

| braço | origem | materiais | chamados | não chamados | violações | manual | conteudo_sha | sha256 do arquivo |
|---|---|---:|---:|---:|---:|---|---|---|
| CRU | reutilizada | 350 | 341 | 9 | 0 | — | `4a57c98e548ef9f4e0b8c9e6a71aa2d3f148b7c14f247f5b0a5be5310fb95ce0` | `07a24d96f85204c3b41472911be3ab28422419c624cadf6e562d07d65f3f6dd7` |
| VOCAB_ATUAL | nova | 350 | 341 | 9 | 0 | CG, ES2, IA, SO, TCC | `623aebcddff76712fae4b7803466733753b40b7a47c4224fbfaa347704c269c5` | `dd7303718e9d6487fa100193dbec005275518686ceb9129e6347ee0f3d8a7f85` |
| VOCAB_LLM | nova | 350 | 341 | 9 | 0 | — | `2695e0b60823ddb3ac6ca3150d86439299cf169f03261232494573e6865d2a3e` | `3fa6fda88f15b19f76ceaf9a0d70cebf60f9de6e5fab60e626c289cc63e69390` |
| CTRL_MAIOR | nova | 350 | 341 | 9 | 0 | — | `55b8d14ec2944a553e9619b8f07a5134b45549a5e23ec78f5d7ef957506cce73` | `4b79a2488a433cc23747e409cfdacdfa85c317ec6b1cfd8c701aa1964f11657d` |
| CTRL_ALEAT_1 | nova | 350 | 341 | 9 | 0 | — | `089c7824000edb0c4a4707767818579d1435c65bf0b10f1f3d87f34c34f47be9` | `ca1eaaba1f359ebef05ab6c2c49d33751ad6cd776569d87d5d4b816dba1cbc88` |
| CTRL_ALEAT_2 | nova | 350 | 341 | 9 | 0 | — | `b363497e2be8d5f8dc305cab5e7982d9cf0820a6cb0590be462ec5a2ac2e24b0` | `260e40980ba4cd380c6f00d53d82e3b7a43b41ce0fe5ee168c5aa2a668a8866a` |
| CTRL_ALEAT_3 | nova | 350 | 341 | 9 | 0 | — | `134ff2387dba05eb5a0425d7d9b3453427b20754977b547d4eaa3d94298bebe4` | `3922bb68e427ae21c7666de3db787460b481050c01d2bc7041d6bd9abb320a39` |
