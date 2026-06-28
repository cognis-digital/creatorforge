"""A minimal Model Context Protocol server (JSON-RPC 2.0 over stdio).

Exposes the content engine as MCP tools so an agent host — Claude, an internal
orchestrator, anything MCP-capable — can drive creatorforge directly. Plain
JSON-RPC over stdio, standard library only, same shape as the rest of the
ecosystem's MCP servers.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Optional, TextIO

from .hooks import write_hooks
from .ideas import generate_ideas
from .pipeline import ContentBrief, run_pipeline
from .platforms import PLATFORMS, package
from .script import write_script
from .thumbnails import thumbnail_concepts
from .voice import VoiceProfile, analyze

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "creatorforge"


def _voice(d: Optional[dict]) -> VoiceProfile:
    if not d:
        return VoiceProfile()
    fields = VoiceProfile().to_dict().keys()
    return VoiceProfile(**{k: v for k, v in d.items() if k in fields})


class Tools:
    def profile_voice(self, texts: list) -> dict:
        prof = analyze(texts)
        return {"style": prof.style_brief(), "profile": prof.to_dict()}

    def write_hooks(self, topic: str, n: int = 8, audience: str = "people",
                    voice: Optional[dict] = None) -> dict:
        return {"hooks": write_hooks(topic, _voice(voice), n, audience=audience)}

    def generate_ideas(self, niche: str, n: int = 10, voice: Optional[dict] = None) -> dict:
        return {"ideas": generate_ideas(niche, _voice(voice), n)}

    def write_script(self, topic: str, platform: str = "youtube",
                     voice: Optional[dict] = None) -> dict:
        return {"script": write_script(topic, _voice(voice), platform)}

    def thumbnail_concepts(self, topic: str, n: int = 3, voice: Optional[dict] = None) -> dict:
        return {"concepts": thumbnail_concepts(topic, _voice(voice), n)}

    def package_for_platform(self, topic: str, platform: str = "youtube", niche: str = "",
                             voice: Optional[dict] = None) -> dict:
        v = _voice(voice)
        hook = write_hooks(topic, v, 1)[0]["hook"]
        core = {"topic": topic, "hook": hook, "summary": "", "niche": niche or topic}
        return {"package": package(core, platform, v)}

    def run_pipeline(self, topic: str, niche: str = "", platforms: Optional[list] = None,
                     voice: Optional[dict] = None) -> dict:
        brief = ContentBrief(topic=topic, niche=niche,
                             platforms=platforms or ["youtube", "tiktok", "x"])
        return run_pipeline(brief, _voice(voice))


TOOL_SPECS = [
    ("profile_voice", "Learn a voice profile from a list of the creator's past posts.",
     {"texts": {"type": "array", "items": {"type": "string"}}}, ["texts"]),
    ("write_hooks", "Write scroll-stopping hooks for a topic, in the creator's voice.",
     {"topic": {"type": "string"}, "n": {"type": "integer", "default": 8},
      "audience": {"type": "string"}, "voice": {"type": "object"}}, ["topic"]),
    ("generate_ideas", "Generate content ideas (format x angle) for a niche.",
     {"niche": {"type": "string"}, "n": {"type": "integer", "default": 10},
      "voice": {"type": "object"}}, ["niche"]),
    ("write_script", "Write a platform-sized script (hook, beats, CTA).",
     {"topic": {"type": "string"},
      "platform": {"type": "string", "enum": list(PLATFORMS)}, "voice": {"type": "object"}}, ["topic"]),
    ("thumbnail_concepts", "Propose thumbnail concepts (headline, visual, emotion, layout).",
     {"topic": {"type": "string"}, "n": {"type": "integer", "default": 3},
      "voice": {"type": "object"}}, ["topic"]),
    ("package_for_platform", "Package a topic into a ready-to-post deliverable for one platform.",
     {"topic": {"type": "string"}, "platform": {"type": "string", "enum": list(PLATFORMS)},
      "niche": {"type": "string"}, "voice": {"type": "object"}}, ["topic"]),
    ("run_pipeline", "Run the full content pipeline for a topic across platforms.",
     {"topic": {"type": "string"}, "niche": {"type": "string"},
      "platforms": {"type": "array", "items": {"type": "string"}},
      "voice": {"type": "object"}}, ["topic"]),
]


class MCPServer:
    def __init__(self, instream: TextIO = sys.stdin, outstream: TextIO = sys.stdout):
        self.tools = Tools()
        self.instream = instream
        self.outstream = outstream

    def _send(self, obj: dict) -> None:
        self.outstream.write(json.dumps(obj, default=str) + "\n")
        self.outstream.flush()

    @staticmethod
    def _ok(req_id, result):
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _err(req_id, code, message):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def serve_forever(self) -> None:
        for line in self.instream:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                self._send(self._err(None, -32700, "parse error"))
                continue
            resp = self.dispatch(req)
            if resp is not None:
                self._send(resp)

    def handle(self, req: dict) -> None:
        resp = self.dispatch(req)
        if resp is not None:
            self._send(resp)

    def dispatch(self, req: dict) -> Optional[dict]:
        method = req.get("method")
        req_id = req.get("id")
        params = req.get("params") or {}
        if method == "initialize":
            return self._ok(req_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": "0.1.0"}})
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return self._ok(req_id, {"tools": [
                {"name": n, "description": d,
                 "inputSchema": {"type": "object", "properties": p, "required": r}}
                for n, d, p, r in TOOL_SPECS]})
        if method == "tools/call":
            return self._call(req_id, params)
        if req_id is not None:
            return self._err(req_id, -32601, f"method not found: {method}")
        return None

    def _call(self, req_id, params: dict) -> dict:
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in {n for n, *_ in TOOL_SPECS}:
            return self._err(req_id, -32602, f"unknown tool: {name}")
        handler: Callable[..., Any] = getattr(self.tools, name)
        try:
            data = handler(**args)
        except TypeError as e:
            return self._err(req_id, -32602, f"bad arguments: {e}")
        except Exception as e:  # noqa: BLE001
            return self._err(req_id, -32000, f"tool error: {e}")
        return self._ok(req_id, {
            "content": [{"type": "text", "text": json.dumps(data, indent=2, default=str)}],
            "isError": False})
