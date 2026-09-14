import json

from microvid.llm import GeminiProvider


class FakeThinkingConfig:
    def __init__(self, **kwargs):
        self.values = kwargs


class FakeGenerateContentConfig:
    def __init__(self, **kwargs):
        self.values = kwargs


class FakeAutomaticFunctionCallingConfig:
    def __init__(self, **kwargs):
        self.values = kwargs


class FakeTypes:
    ThinkingConfig = FakeThinkingConfig
    GenerateContentConfig = FakeGenerateContentConfig
    AutomaticFunctionCallingConfig = FakeAutomaticFunctionCallingConfig


class FakeModels:
    def __init__(self):
        self.call = None

    def generate_content_stream(self, **kwargs):
        self.call = kwargs
        payload = json.dumps({"ok": True})
        return iter(
            [
                type("Chunk", (), {"text": payload[:5]})(),
                type("Chunk", (), {"text": payload[5:]})(),
            ]
        )


class FakeClient:
    def __init__(self):
        self.models = FakeModels()


class RemoteProtocolError(Exception):
    pass


class FlakyModels(FakeModels):
    def __init__(self):
        super().__init__()
        self.attempts = 0

    def generate_content_stream(self, **kwargs):
        self.attempts += 1
        if self.attempts < 3:
            raise RemoteProtocolError("temporary disconnect")
        return super().generate_content_stream(**kwargs)


def test_gemini_provider_uses_generate_content_structured_output(monkeypatch):
    client = FakeClient()
    provider = GeminiProvider(model="gemini-flash-latest", thinking_level="high")
    monkeypatch.setattr(provider, "_client", lambda: (client, FakeTypes))
    schema = {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "items": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {"type": "string"},
            },
        },
        "required": ["ok"],
    }

    payload = provider.generate_json("Return JSON.", schema)

    assert payload == {"ok": True}
    assert client.models.call["model"] == "gemini-flash-latest"
    assert client.models.call["contents"] == "Return JSON."
    config = client.models.call["config"].values
    assert config["response_mime_type"] == "application/json"
    sent_schema = config["response_json_schema"]
    assert sent_schema["properties"]["items"] == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert schema["properties"]["items"]["minItems"] == 1
    assert config["thinking_config"].values["thinking_level"] == "HIGH"
    assert config["automatic_function_calling"].values["disable"] is True


def test_gemini_provider_retries_transient_stream_disconnects(monkeypatch):
    client = FakeClient()
    client.models = FlakyModels()
    provider = GeminiProvider()
    monkeypatch.setattr(provider, "_client", lambda: (client, FakeTypes))
    monkeypatch.setattr("microvid.llm.time.sleep", lambda _seconds: None)

    payload = provider.generate_json(
        "Return JSON.",
        {
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
        },
    )

    assert payload == {"ok": True}
    assert client.models.attempts == 3
