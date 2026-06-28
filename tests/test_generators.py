from creatorforge.captions import to_overlays, to_srt
from creatorforge.hooks import write_hooks
from creatorforge.ideas import generate_ideas
from creatorforge.script import write_script
from creatorforge.thumbnails import render_svg, thumbnail_concepts
from creatorforge.voice import VoiceProfile, analyze


def emoji_voice():
    return analyze(["🚀 LET'S GO! This is HUGE! Follow for more 🔥"])


def test_hooks_count_and_topic():
    hooks = write_hooks("cold email", VoiceProfile(), n=8)
    assert len(hooks) == 8
    assert any("cold email" in h["hook"] for h in hooks)
    assert all("formula" in h for h in hooks)


class _FakeProvider:
    name = "fake"
    available = True

    def rewrite(self, text, voice, instruction=""):
        # echo the same number of lines, transformed — simulates an LLM rewrite
        return "\n".join(f"{i + 1}. SHARP {ln.split('. ', 1)[-1]}"
                         for i, ln in enumerate(text.splitlines()))


def test_hooks_polished_by_provider():
    base = write_hooks("cold email", VoiceProfile(), 4)
    sharp = write_hooks("cold email", VoiceProfile(), 4, provider=_FakeProvider())
    assert len(sharp) == 4
    assert all(h["hook"].startswith("SHARP") for h in sharp)
    assert sharp[0]["hook"] != base[0]["hook"]
    assert sharp[0]["formula"] == base[0]["formula"]   # metadata preserved


def test_hooks_template_provider_is_noop():
    from creatorforge.providers import TemplateProvider
    base = write_hooks("cold email", VoiceProfile(), 4)
    same = write_hooks("cold email", VoiceProfile(), 4, provider=TemplateProvider())
    assert [h["hook"] for h in base] == [h["hook"] for h in same]


def test_hooks_apply_voice_styling():
    hooks = write_hooks("cold email", emoji_voice(), n=3)
    # emoji-heavy + energetic voice -> emoji prefix and emphatic punctuation
    assert any(h["hook"][0] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for h in hooks)


def test_ideas_distinct_and_have_platforms():
    ideas = generate_ideas("real estate", VoiceProfile(), n=10)
    assert len(ideas) == 10
    assert len({(i["format"], i["angle"]) for i in ideas}) == 10  # de-duped
    assert all(i["platforms"] for i in ideas)


def test_script_length_scales_with_platform():
    short = write_script("habits", VoiceProfile(), "youtube_shorts")
    long = write_script("habits", VoiceProfile(), "youtube")
    assert len(short["beats"]) == 3
    assert len(long["beats"]) > len(short["beats"])
    assert short["est_seconds"] > 0 and short["word_count"] > 0


def test_captions_srt_and_overlays():
    script = write_script("habits", VoiceProfile(), "youtube_shorts")
    srt = to_srt(script)
    assert "1\n00:00:00,000 -->" in srt           # well-formed first cue
    overlays = to_overlays(script)
    assert overlays and all(o == o.upper() for o in overlays)


def test_thumbnail_concepts_and_svg():
    concepts = thumbnail_concepts("morning routines", VoiceProfile(), n=3)
    assert len(concepts) == 3
    svg = render_svg(concepts[0])
    assert svg.startswith("<svg") and "</svg>" in svg
    assert "MORNING" in svg.upper()                 # headline keyword rendered
