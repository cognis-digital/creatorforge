import io
import json

from creatorforge.mcp_server import MCPServer
from creatorforge.pipeline import ContentBrief, run_pipeline
from creatorforge.voice import analyze


def test_pipeline_produces_all_sections():
    brief = ContentBrief(topic="cold outreach", niche="b2b sales",
                         platforms=["youtube", "tiktok", "x"], start_date="2026-07-06")
    out = run_pipeline(brief)
    for key in ("research_brief", "ideas", "hooks", "script", "captions",
                "thumbnails", "packages", "calendar"):
        assert key in out and out[key]
    assert set(out["packages"]) == {"youtube", "tiktok", "x"}
    assert out["calendar"]                         # start_date -> calendar built


def test_pipeline_uses_voice():
    v = analyze(["🔥 LET'S GO! Massive value! Follow for more 🚀"])
    out = run_pipeline(ContentBrief(topic="email", niche="sales"), v)
    assert "emoji" in out["voice"] or "energetic" in out["voice"]


def drive(server, req):
    server.outstream = io.StringIO()
    server.handle(req)
    return json.loads(server.outstream.getvalue().strip())


def test_mcp_initialize_list_and_call():
    s = MCPServer()
    init = drive(s, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init["result"]["serverInfo"]["name"] == "creatorforge"

    listed = drive(s, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in listed["result"]["tools"]}
    assert {"run_pipeline", "write_hooks", "profile_voice"} <= names

    called = drive(s, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                       "params": {"name": "write_hooks",
                                  "arguments": {"topic": "saas onboarding", "n": 5}}})
    payload = json.loads(called["result"]["content"][0]["text"])
    assert len(payload["hooks"]) == 5


def test_mcp_unknown_tool_errors():
    s = MCPServer()
    resp = drive(s, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                     "params": {"name": "nope", "arguments": {}}})
    assert resp["error"]["code"] == -32602
