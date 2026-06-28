from creatorforge.posttypes import POST_TYPES, make_post, mixed_posts

CTX = {"name": "codegraph-mcp", "summary": "a no-train code knowledge graph for AI agents",
       "features": ["6 languages", "MCP server", "hash-chained audit"],
       "url": "https://github.com/cognis-digital/codegraph-mcp"}


def test_all_post_types_build():
    posts = mixed_posts(CTX)
    assert len(posts) == len(POST_TYPES)
    for p in posts:
        assert p["text"] and CTX["url"] in p["text"]
        assert "#codegraphmcp" in p["text"]


def test_hook_becomes_first_line():
    p = make_post("promotion", CTX, hook="The truth nobody tells you about code graphs")
    assert p["text"].splitlines()[0] == "The truth nobody tells you about code graphs"


def test_report_uses_features_as_bullets():
    p = make_post("report", CTX)
    assert "• 6 languages" in p["text"]


def test_unknown_type_raises():
    import pytest
    with pytest.raises(ValueError):
        make_post("tweetstorm", CTX)


def test_subset_of_types():
    posts = mixed_posts(CTX, types=["whitepaper", "demo"])
    assert [p["type"] for p in posts] == ["whitepaper", "demo"]
