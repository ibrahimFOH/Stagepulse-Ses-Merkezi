import io
import json

import pytest

from core import ai_providers


class FakeResponse(io.BytesIO):
    status = 200
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


def json_response(payload):
    return FakeResponse(json.dumps(payload).encode("utf-8"))


def test_only_local_ollama_and_groq_are_active():
    assert set(ai_providers.PROVIDERS) == {"ollama", "groq"}
    assert ai_providers.PROVIDERS["ollama"]["requires_key"] is False
    assert ai_providers.PROVIDERS["groq"]["requires_key"] is True


def test_ollama_endpoint_must_be_localhost():
    with pytest.raises(ValueError, match="127.0.0.1"):
        ai_providers._validate_endpoint("ollama", "https://127.0.0.1:11434/api/chat")
    with pytest.raises(ValueError, match="127.0.0.1"):
        ai_providers._validate_endpoint("ollama", "http://192.168.1.20:11434/api/chat")


def test_groq_requires_official_https_host():
    with pytest.raises(ValueError, match="HTTPS"):
        ai_providers._validate_endpoint("groq", "http://api.groq.com/openai/v1/chat/completions")
    with pytest.raises(ValueError, match="api.groq.com"):
        ai_providers._validate_endpoint("groq", "https://api.groq.com.attacker.test/v1/chat/completions")


def test_list_ollama_models_reads_exact_installed_tags(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=75):
        captured["url"] = request.full_url
        return json_response({"models": [
            {"name": "huihui_ai/qwen2.5-abliterate:latest", "size": 100},
            {"model": "dolphin-mistral:latest", "size": 200},
        ]})

    monkeypatch.setattr(ai_providers, "urlopen", fake_urlopen)
    ai_providers.clear_ollama_model_cache()
    models = ai_providers.list_ollama_models()
    assert captured["url"] == "http://127.0.0.1:11434/api/tags"
    assert [item["name"] for item in models] == [
        "dolphin-mistral:latest",
        "huihui_ai/qwen2.5-abliterate:latest",
    ]


def test_model_router_selects_coder_for_code_prompts():
    models = [
        "hf.co/bartowski/Qwen2.5-14B-Instruct-1M-GGUF:Q2_K",
        "huihui_ai/qwen2.5-abliterate:latest",
        "iamhere/qwen2.5-coder-3b-instruct-abliterated:latest",
        "dolphin-mistral:latest",
        "dolphin-llama3:latest",
        "superdrew100/llama3-abliterated:latest",
        "dolphin-phi:latest",
    ]
    assert ai_providers.select_ollama_model("Python kodunu debug et", models) == (
        "iamhere/qwen2.5-coder-3b-instruct-abliterated:latest"
    )


def test_model_router_selects_qwen_14b_for_engineering_analysis():
    models = [
        "hf.co/bartowski/Qwen2.5-14B-Instruct-1M-GGUF:Q2_K",
        "huihui_ai/qwen2.5-abliterate:latest",
    ]
    assert ai_providers.select_ollama_model("Kapsamlı SPL mühendislik analizi", models) == (
        "hf.co/bartowski/Qwen2.5-14B-Instruct-1M-GGUF:Q2_K"
    )


def test_model_router_selects_general_model_and_never_invents_tags():
    assert ai_providers.select_ollama_model(
        "Merhaba", ["huihui_ai/qwen2.5-abliterate:latest", "dolphin-phi:latest"]
    ) == "huihui_ai/qwen2.5-abliterate:latest"
    assert ai_providers.select_ollama_model("Kod yaz", ["dolphin-phi:latest"]) == "dolphin-phi:latest"


def test_ollama_chat_auto_discovers_and_routes_without_key(monkeypatch):
    ai_providers.clear_ollama_model_cache()
    calls = []

    def fake_urlopen(request, timeout=75):
        calls.append((request.full_url, timeout))
        if request.full_url.endswith("/api/tags"):
            return json_response({"models": [
                {"name": "huihui_ai/qwen2.5-abliterate:latest"},
                {"name": "iamhere/qwen2.5-coder-3b-instruct-abliterated:latest"},
            ]})
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == "iamhere/qwen2.5-coder-3b-instruct-abliterated:latest"
        assert body["options"]["num_predict"] == -1
        assert body["options"]["num_ctx"] == 8192
        return json_response({"message": {"content": "Yerel kod yanıtı"}})

    monkeypatch.setattr(ai_providers, "urlopen", fake_urlopen)
    result = ai_providers.chat("ollama", "auto", "", "Python kodunu debug et")
    assert result["content"] == "Yerel kod yanıtı"
    assert result["model"] == "iamhere/qwen2.5-coder-3b-instruct-abliterated:latest"
    assert calls[0][0] == "http://127.0.0.1:11434/api/tags"
    assert calls[1][0] == "http://127.0.0.1:11434/api/chat"


def test_explicit_uninstalled_ollama_model_is_rejected(monkeypatch):
    monkeypatch.setattr(ai_providers, "list_ollama_models", lambda endpoint=None: [
        {"name": "dolphin-phi:latest", "size": 1, "modified_at": ""}
    ])
    with pytest.raises(ValueError, match="yüklü değil"):
        ai_providers.chat("ollama", "qwen3:0.6b", "", "test")


def test_groq_adapter_uses_official_chat_completions(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=75):
        captured["url"] = request.full_url
        captured["headers"] = request.headers
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return json_response({"choices": [{"message": {"content": "Groq bağlantısı başarılı"}}]})

    monkeypatch.setattr(ai_providers, "urlopen", fake_urlopen)
    result = ai_providers.chat("groq", "openai/gpt-oss-120b", "test-key", "test")
    assert result["content"] == "Groq bağlantısı başarılı"
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["body"]["model"] == "openai/gpt-oss-120b"
    assert captured["headers"]["Authorization"] == "Bearer test-key"


def test_cloud_provider_requires_groq_key():
    with pytest.raises(ValueError, match="API anahtarı"):
        ai_providers.chat("groq", "openai/gpt-oss-120b", "", "test")


def test_disabled_cloud_provider_is_rejected():
    with pytest.raises(ValueError, match="Yalnızca yerel Ollama veya Groq"):
        ai_providers.chat("gemini", "any-model", "unused", "test")


def test_prompt_size_is_checked():
    with pytest.raises(ValueError, match="12.000"):
        ai_providers.chat("ollama", "auto", "", "x" * 12001)



def test_app_auto_provider_uses_local_ollama_before_any_groq_fallback(monkeypatch):
    from Merkez import AppApi

    app = AppApi.__new__(AppApi)
    app._cached_license_status = lambda: {"active": True}
    calls = []
    def fake_chat(provider, model, api_key, prompt, endpoint, *args, **kwargs):
        calls.append(provider)
        return {"ok": True, "provider": provider, "model": "huihui_ai/qwen2.5-abliterate:latest", "content": "Yerel yanıt"}
    monkeypatch.setattr(ai_providers, "chat", fake_chat)
    result = app.ai_chat("auto", "auto", "", "merhaba", "http://127.0.0.1:11434/api/chat")
    assert calls == ["ollama"]
    assert result["routing"] == "ollama"
    assert result["content"] == "Yerel yanıt"


def test_app_auto_provider_uses_groq_only_after_local_failure_and_license(monkeypatch):
    from Merkez import AppApi

    app = AppApi.__new__(AppApi)
    app._cached_license_status = lambda: {"active": True}
    calls = []
    def fake_chat(provider, model, api_key, prompt, endpoint, *args, **kwargs):
        calls.append(provider)
        if provider == "ollama":
            raise RuntimeError("Ollama kapalı")
        return {"ok": True, "provider": provider, "model": model, "content": "Groq yedek yanıt"}
    monkeypatch.setattr(ai_providers, "chat", fake_chat)
    result = app.ai_chat("auto", "auto", "groq-test-key", "merhaba", "http://127.0.0.1:11434/api/chat")
    assert calls == ["ollama", "groq"]
    assert result["routing"] == "groq"
    assert result["fallback_reason"] == "Ollama kapalı"


def test_app_auto_provider_does_not_send_to_groq_without_license(monkeypatch):
    from Merkez import AppApi

    app = AppApi.__new__(AppApi)
    app._cached_license_status = lambda: {"active": False}
    calls = []
    def fake_chat(provider, model, api_key, prompt, endpoint, *args, **kwargs):
        calls.append(provider)
        raise RuntimeError("Ollama kapalı")
    monkeypatch.setattr(ai_providers, "chat", fake_chat)
    with pytest.raises(RuntimeError, match="ödemesi onaylı lisans gerekir"):
        app.ai_chat("auto", "auto", "groq-test-key", "merhaba", "http://127.0.0.1:11434/api/chat")
    assert calls == []



def test_audio_engineering_prompts_route_to_qwen14():
    models = [
        "hf.co/bartowski/Qwen2.5-14B-Instruct-1M-GGUF:Q2_K",
        "huihui_ai/qwen2.5-abliterate:latest",
        "iamhere/qwen2.5-coder-3b-instruct-abliterated:latest",
    ]
    assert ai_providers.select_ollama_model(
        "Midas M32 FOH monitör ve line array sistem tasarımı", models
    ) == "hf.co/bartowski/Qwen2.5-14B-Instruct-1M-GGUF:Q2_K"


def test_ollama_model_list_cache_expires_by_force_refresh(monkeypatch):
    ai_providers.clear_ollama_model_cache()
    calls = []
    def fake_urlopen(request, timeout=75):
        calls.append(request.full_url)
        return json_response({"models": [{"name": "dolphin-phi:latest"}]})
    monkeypatch.setattr(ai_providers, "urlopen", fake_urlopen)
    first = ai_providers.list_ollama_models()
    second = ai_providers.list_ollama_models()
    refreshed = ai_providers.list_ollama_models(force_refresh=True)
    assert first == second == refreshed
    assert len(calls) == 2
    ai_providers.clear_ollama_model_cache()


def test_ollama_request_options_are_provider_specific_and_validated(monkeypatch):
    captured = {}
    def fake_urlopen(request, timeout=75):
        if request.full_url.endswith("/api/tags"):
            return json_response({"models": [{"name": "dolphin-phi:latest"}]})
        captured.update(json.loads(request.data.decode("utf-8")))
        return json_response({"message": {"content": "ok"}})
    monkeypatch.setattr(ai_providers, "urlopen", fake_urlopen)
    ai_providers.clear_ollama_model_cache()
    ai_providers.chat("ollama", "auto", "", "merhaba", request_options={"temperature": 0.1, "num_ctx": 4096, "ignored": 1}, keep_alive="10m", think=True)
    assert captured["options"]["temperature"] == 0.1
    assert captured["options"]["num_ctx"] == 4096
    assert "ignored" not in captured["options"]
    assert captured["keep_alive"] == "10m"
    assert captured["think"] is True
    ai_providers.clear_ollama_model_cache()

