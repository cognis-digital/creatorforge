"""Pluggable generation backends.

creatorforge's generators produce real, structured content on their own — hooks,
ideas, scripts, captions — so the whole pipeline runs **offline with zero
dependencies** via `TemplateProvider`. A provider is an optional *enhancer*: give
it a model and it rewrites that scaffold into sharper prose in the creator's
voice.

The point the agencies hide: this is *your* choice. Run a local model with
`OllamaProvider` (nothing leaves your machine) or wire a cloud model behind the
same interface. The engine never needs one to function.
"""

from __future__ import annotations

import json
from typing import Optional

from .voice import VoiceProfile


class Provider:
    name = "abstract"
    available = False

    def rewrite(self, text: str, voice: VoiceProfile, instruction: str = "") -> str:
        """Return a voice-polished version of `text` (or `text` unchanged)."""
        return text


class TemplateProvider(Provider):
    """The default: no model, fully deterministic. Returns the engine's own
    structured output untouched, so runs are reproducible and offline."""

    name = "template"
    available = True


class OllamaProvider(Provider):
    """Rewrite content with a local model via Ollama (http://localhost:11434).

    Nothing leaves the machine. If Ollama isn't reachable, `rewrite` degrades
    gracefully to returning the input, so a pipeline never breaks on a missing
    model.
    """

    name = "ollama"
    # preference order when model="auto": instruction-tuned / capable first
    _PREFER = ("omnicoder", "qwen2.5", "qwen", "llama3.1", "llama3", "mistral", "codellama")

    def __init__(self, model: str = "auto", host: str = "http://localhost:11434",
                 timeout: float = 120.0):
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.model = model

    def list_models(self) -> list:
        import urllib.request
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=3) as r:
                return [m["name"] for m in json.loads(r.read()).get("models", [])]
        except Exception:
            return []

    def best_model(self) -> Optional[str]:
        models = self.list_models()
        if not models:
            return None
        for pref in self._PREFER:
            for m in models:
                if pref in m.lower():
                    return m
        return models[0]

    def resolve_model(self) -> Optional[str]:
        if self.model and self.model != "auto":
            return self.model
        return self.best_model()

    @property
    def available(self) -> bool:  # type: ignore[override]
        return bool(self.list_models())

    def rewrite(self, text: str, voice: VoiceProfile, instruction: str = "") -> str:
        import urllib.request

        model = self.resolve_model()
        if not model:
            return text
        system = (
            "You are a ghostwriter. Rewrite the content in this exact creator voice, "
            "preserving meaning and structure. Voice: " + voice.style_brief()
        )
        prompt = (instruction + "\n\n" if instruction else "") + text
        body = json.dumps({
            "model": model, "system": system, "prompt": prompt, "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(f"{self.host}/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read()).get("response", text).strip() or text
        except Exception:
            return text  # degrade gracefully — never break the pipeline


def get_provider(name: str = "template", **kwargs) -> Provider:
    if name in ("template", "offline", None):
        return TemplateProvider()
    if name == "ollama":
        return OllamaProvider(**kwargs)
    raise ValueError(f"unknown provider: {name}")
