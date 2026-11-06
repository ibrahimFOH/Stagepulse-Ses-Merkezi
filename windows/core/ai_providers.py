"""Yalnızca yerel Ollama ve isteğe bağlı Groq AI adaptörleri."""
from __future__ import annotations

import json
import time
from threading import RLock
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

PROVIDERS = {
    "ollama": {
        "label": "Ollama (yerel)",
        "endpoint": "http://127.0.0.1:11434/api/chat",
        "model": "auto",
        "requires_key": False,
    },
    "groq": {
        "label": "GroqCloud (yedek)",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "model": "openai/gpt-oss-120b",
        "requires_key": True,
    },
}

OLLAMA_MODEL_ROUTES = {
    "code": (
        "iamhere/qwen2.5-coder-3b-instruct-abliterated:latest",
        "hf.co/bartowski/Qwen2.5-14B-Instruct-1M-GGUF:Q2_K",
        "huihui_ai/qwen2.5-abliterate:latest",
        "dolphin-llama3:latest",
        "superdrew100/llama3-abliterated:latest",
    ),
    "analysis": (
        "hf.co/bartowski/Qwen2.5-14B-Instruct-1M-GGUF:Q2_K",
        "huihui_ai/qwen2.5-abliterate:latest",
        "dolphin-mistral:latest",
        "dolphin-llama3:latest",
    ),
    "general": (
        "huihui_ai/qwen2.5-abliterate:latest",
        "dolphin-mistral:latest",
        "dolphin-llama3:latest",
        "superdrew100/llama3-abliterated:latest",
        "dolphin-phi:latest",
        "hf.co/bartowski/Qwen2.5-14B-Instruct-1M-GGUF:Q2_K",
    ),
}

_MODEL_CACHE = {}
_MODEL_CACHE_LOCK = RLock()
_MODEL_CACHE_TTL = 30.0


def clear_ollama_model_cache(endpoint=None):
    with _MODEL_CACHE_LOCK:
        if endpoint is None:
            _MODEL_CACHE.clear()
        else:
            _MODEL_CACHE.pop(str(endpoint).strip(), None)


SYSTEM_PROMPT = (
    "Türkçe yanıt ver. Ses mühendisliği eğitiminde teknik doğruluğu gözet; ölçülmemiş "
    "SPL, true-peak, faz veya akustik değerleri uydurma. Varsayım ile ölçüm sonucunu ayır. "
    "Tehlikeli ses seviyesi, elektrik, rigging ve işitme maruziyetinde güvenlik uyarısı ver. "
    "API anahtarını veya özel bilgileri yanıta koyma."
)


def _validate_endpoint(provider: str, endpoint: str) -> None:
    parsed = urlparse(str(endpoint or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Endpoint geçerli bir HTTP(S) URL olmalı.")
    local = parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
    if provider == "ollama":
        if parsed.scheme != "http" or not local:
            raise ValueError("Ollama yalnızca bu bilgisayardaki http://127.0.0.1:11434 adresinde çalışır.")
        if parsed.port not in (None, 11434) or parsed.path not in ("", "/", "/api/chat"):
            raise ValueError("Ollama endpoint yolu /api/chat olmalı ve port 11434 kullanılmalı.")
    elif parsed.scheme != "https":
        raise ValueError("Groq bağlantısı HTTPS kullanmalıdır.")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Endpoint URL'sinde kullanıcı bilgisi veya fragment bulunamaz.")
    if provider == "groq" and parsed.hostname.lower() != "api.groq.com":
        raise ValueError("Groq sağlayıcısında yalnızca resmi api.groq.com adresi kabul edilir.")


def _read_json_response(request: Request, timeout: int = 180) -> dict:
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"AI servisi HTTP {response.status} döndürdü.")
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise RuntimeError("AI yanıtı 2 MB sınırını aştı.")
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError("AI servisi geçerli JSON döndürmedi.") from exc
    except HTTPError as exc:
        detail = exc.read(2048).decode("utf-8", errors="replace")
        raise RuntimeError(f"AI servisi HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"AI servisine ulaşılamadı: {exc}") from exc


def _tags_url(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    return urlunparse((parsed.scheme, parsed.netloc, "/api/tags", "", "", ""))


def list_ollama_models(endpoint: str | None = None, force_refresh: bool = False) -> list[dict]:
    """Return the exact model tags installed on the local Ollama service."""
    raw_endpoint = str(endpoint or PROVIDERS["ollama"]["endpoint"]).strip()
    _validate_endpoint("ollama", raw_endpoint)
    with _MODEL_CACHE_LOCK:
        cached = _MODEL_CACHE.get(raw_endpoint)
        if not force_refresh and cached and cached[0] > time.monotonic():
            return [dict(item) for item in cached[1]]
    request = Request(
        _tags_url(raw_endpoint),
        headers={"Accept": "application/json", "User-Agent": "StagepulseSesMerkezi/3.7"},
        method="GET",
    )
    data = _read_json_response(request, timeout=45)
    items = data.get("models", []) if isinstance(data, dict) else []
    models = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("model") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        models.append({
            "name": name,
            "size": int(item.get("size") or 0),
            "modified_at": str(item.get("modified_at") or ""),
        })
    if not models:
        raise RuntimeError("Ollama yanıt verdi ancak yüklü model bulunamadı. ollama list ile kontrol et.")
    result = sorted(models, key=lambda item: item["name"])
    with _MODEL_CACHE_LOCK:
        _MODEL_CACHE[raw_endpoint] = (time.monotonic() + _MODEL_CACHE_TTL, result)
    return [dict(item) for item in result]


def select_ollama_model(prompt: str, installed_models: list[str] | list[dict]) -> str:
    """Route a prompt to an installed model based on task type."""
    available = {
        str(item.get("name") if isinstance(item, dict) else item).strip()
        for item in installed_models
        if str(item.get("name") if isinstance(item, dict) else item).strip()
    }
    if not available:
        raise RuntimeError("Ollama'da kullanılabilir model bulunamadı.")

    text = str(prompt or "").casefold()
    code_terms = (
        "kod", "python", "javascript", "typescript", "kotlin", "java ",
        "html", "css", "json", "yaml", "sql", "powershell", "terminal",
        "cmd", "script", "debug", "hata ayıkla", "derle", "build", "apk",
        "exe", "github", "repo", "pull request", "workflow", "fonksiyon yaz",
        "uygulama geliştir", "programla", "kodla",
    )
    analysis_terms = (
        "kapsamlı", "detaylı analiz", "derin analiz", "araştır", "karşılaştır",
        "mühendislik", "akustik", "spl", "rta", "teknik rapor", "mimari",
        "fiziksel hesap", "hesapla", "tasarla", "projelendir", "teknik şartname",
        "foh", "monitör", "monitor", "line array", "subwoofer", "subbass",
        "rider", "stageplot", "stage plot", "midas", "m32", "cl5", "avantis",
        "mikser", "mikrofon", "dante", "iem", "soundcheck", "gain staging",
        "oda akustiği", "oda akustigi", "yankı süresi", "reverb time",
    )
    route = "code" if any(term in text for term in code_terms) else (
        "analysis" if any(term in text for term in analysis_terms) else "general"
    )
    for candidate in OLLAMA_MODEL_ROUTES[route]:
        if candidate in available:
            return candidate
    # Keep future locally installed models usable; never invent a model tag.
    return sorted(available)[0]


def _extract_openai(data: dict) -> str:
    choices = data.get("choices") if isinstance(data, dict) else None
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("AI yanıtında choices alanı yok.")
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, list):
        content = "\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("AI yanıtında metin içeriği bulunamadı.")
    return content.strip()


def chat(provider: str, model: str, api_key: str, prompt: str, endpoint: str | None = None, request_options: dict | None = None, keep_alive: str = "30m", think: bool = False) -> dict:
    provider = str(provider or "ollama").strip().lower()
    if provider not in PROVIDERS:
        raise ValueError("Yalnızca yerel Ollama veya Groq sağlayıcısı kullanılabilir.")
    spec = PROVIDERS[provider]
    model = str(model or spec["model"]).strip()[:200]
    prompt = str(prompt or "").strip()
    key = str(api_key or "").strip()
    if not model or not prompt:
        raise ValueError("Model yönlendirmesi ve istem zorunlu.")
    if len(prompt) > 12000:
        raise ValueError("İstem 12.000 karakteri aşamaz.")
    if len(key) > 2048:
        raise ValueError("API anahtarı uzunluğu geçersiz.")
    if spec["requires_key"] and not key:
        raise ValueError("Groq için API anahtarı gerekli.")

    raw_endpoint = str(endpoint or spec["endpoint"]).strip()
    _validate_endpoint(provider, raw_endpoint)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "StagepulseSesMerkezi/3.7",
    }

    if provider == "ollama":
        installed = list_ollama_models(raw_endpoint)
        if model.lower() in {"auto", "otomatik"}:
            selected_model = select_ollama_model(prompt, installed)
        else:
            installed_names = {item["name"] for item in installed}
            if model not in installed_names:
                raise ValueError(
                    "Seçili Ollama modeli bu bilgisayarda yüklü değil. "
                    "Model seçimi otomatik bırakılmalı. Yüklü modeller: "
                    + ", ".join(sorted(installed_names))
                )
            selected_model = model
        body = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "keep_alive": str(keep_alive)[:32],
            "think": bool(think),
            "options": {"temperature": 0.2, "num_ctx": 8192, "num_predict": -1},
        }
        if request_options is not None:
            if not isinstance(request_options, dict):
                raise ValueError("Ollama istek seçenekleri sözlük olmalıdır.")
            allowed = {"temperature", "top_p", "top_k", "num_ctx", "num_predict", "repeat_penalty", "seed"}
            for option, value in request_options.items():
                if option not in allowed:
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(f"Ollama {option} seçeneği sayısal olmalıdır.")
                body["options"][option] = value
        request = Request(raw_endpoint, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        data = _read_json_response(request, timeout=600)
        content = ((data.get("message") or {}).get("content") or "").strip()
        if not content:
            raise RuntimeError("Ollama yanıtında metin yok.")
        return {
            "ok": True,
            "provider": provider,
            "provider_name": spec["label"],
            "model": selected_model,
            "content": content,
        }

    try:
        headers["Authorization"] = "Bearer " + key
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "stream": False,
        }
        request = Request(raw_endpoint, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        data = _read_json_response(request, timeout=90)
        content = _extract_openai(data)
        return {
            "ok": True,
            "provider": provider,
            "provider_name": spec["label"],
            "model": model,
            "content": content,
        }
    finally:
        key = ""
        headers.pop("Authorization", None)
