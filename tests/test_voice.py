from pathlib import Path

from creatorforge.voice import VoiceProfile, analyze

CORPUS = Path(__file__).resolve().parent.parent / "examples" / "sample_corpus"


def corpus_texts():
    return [f.read_text(encoding="utf-8") for f in sorted(CORPUS.glob("*.txt"))]


def test_analyze_extracts_features():
    v = analyze(corpus_texts())
    assert v.samples == 2
    assert v.words > 0
    assert v.emoji_per_100w > 0          # the corpus is emoji-heavy
    assert v.signature_emojis            # detected at least one emoji
    assert v.top_terms                   # niche vocabulary surfaced
    assert v.cta_phrases                 # "follow for", "comment" detected


def test_style_brief_nonempty():
    v = analyze(corpus_texts())
    brief = v.style_brief()
    assert isinstance(brief, str) and len(brief) > 10


def test_empty_corpus_is_safe():
    v = analyze([])
    assert v.samples == 0
    assert v.style_brief()               # still produces a default descriptor


def test_save_load_roundtrip(tmp_path):
    v = analyze(corpus_texts())
    p = str(tmp_path / "voice.json")
    v.save(p)
    v2 = VoiceProfile.load(p)
    assert v2.top_terms == v.top_terms
    assert v2.emoji_per_100w == v.emoji_per_100w


def test_derived_flags():
    punchy = analyze(["Go. Now. Do it. Win."])
    assert punchy.punchy
    energetic = analyze(["THIS IS HUGE! ACT NOW! LET'S GO!"])
    assert energetic.energetic
