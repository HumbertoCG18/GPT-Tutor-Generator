"""`GeminiClient.generate_text` (SYNC S6b, 2026-09-03): texto puro (traducao de legenda do Datalab) ou
texto + imagem (descricao de figura que o Datalab devolveu vazia). O client do SDK e falso: so o contrato
`models.generate_content(model=, contents=)` com `Part.from_bytes` para a imagem."""
from src.builder.runtime.gemini_client import GeminiClient


class _Resp:
    def __init__(self, text):
        self.text = text


class _Models:
    def __init__(self):
        self.calls = []

    def generate_content(self, *, model, contents, config=None):
        self.calls.append((model, contents))
        return _Resp("  resposta  ")


class _Client:
    def __init__(self):
        self.models = _Models()


def test_generate_text_sends_prompt_and_image_part(tmp_path):
    img = tmp_path / "f.gif"
    img.write_bytes(b"GIF89a")
    client = GeminiClient(api_key="k", model="m")
    fake = _Client()
    client._client = fake
    assert client.generate_text("descreva", image_path=img) == "resposta"
    model, contents = fake.models.calls[0]
    assert model == "m"
    assert contents[0] == "descreva"
    assert contents[1].inline_data.mime_type == "image/gif"
    assert contents[1].inline_data.data == b"GIF89a"


def test_generate_text_without_image_sends_only_prompt():
    client = GeminiClient(api_key="k")
    fake = _Client()
    client._client = fake
    assert client.generate_text("traduza") == "resposta"
    assert fake.models.calls[0][1] == "traduza"
