"""Voice profiling — learn a creator's style from their own words.

"Trained on your voice" doesn't have to mean fine-tuning a model on your data
(and handing it to a vendor). Most of what makes a voice recognizable is
*measurable*: sentence length, how often you ask questions, emoji and emphasis
habits, the vocabulary of your niche, the way you call viewers to action. We
extract those features from a corpus of your past posts with the standard
library alone — nothing is uploaded, nothing is trained — and use them to
condition every piece of content the engine produces.
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import List

_EMOJI = re.compile(
    "[" "\U0001F300-\U0001FAFF" "\U00002600-\U000027BF" "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF" "\U00002B00-\U00002BFF" "\U0000FE00-\U0000FE0F" "]"
)
_WORD = re.compile(r"[A-Za-z']+")
_SENT = re.compile(r"[.!?]+(?:\s|$)")
_CTA_PATTERNS = [
    "link in bio", "click the link", "subscribe", "follow for", "comment",
    "dm me", "sign up", "book a call", "tap in", "let me know", "save this",
    "share this", "join", "download",
]
_STOP = set(
    "the a an and or but if then of to in on for with at by from as is are was "
    "were be been being this that these those it its i you he she they we me my "
    "your our their his her them us so not no do does did have has had will would "
    "can could should may might just about into out up down over under more most "
    "very really also too than what when where which who how why all any some".split()
)


def _syllables(word: str) -> int:
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups)
    if word.endswith("e") and n > 1:
        n -= 1
    return max(1, n)


@dataclass
class VoiceProfile:
    samples: int = 0
    words: int = 0
    avg_sentence_len: float = 14.0
    reading_grade: float = 7.0
    emoji_per_100w: float = 0.0
    exclamation_rate: float = 0.0     # per sentence
    question_rate: float = 0.0        # per sentence
    caps_emphasis_rate: float = 0.0   # ALLCAPS words per 100 words
    list_usage: float = 0.0           # fraction of lines that are bullets
    top_terms: List[str] = field(default_factory=list)
    signature_emojis: List[str] = field(default_factory=list)
    cta_phrases: List[str] = field(default_factory=list)

    # ---- derived descriptors used to condition generation ----------------
    @property
    def punchy(self) -> bool:
        return self.avg_sentence_len <= 12

    @property
    def emoji_heavy(self) -> bool:
        return self.emoji_per_100w >= 2.0

    @property
    def energetic(self) -> bool:
        return self.exclamation_rate >= 0.25 or self.caps_emphasis_rate >= 2.0

    def style_brief(self) -> str:
        """A compact, human-readable spec — also fed to an LLM provider as system context."""
        bits = [
            f"~{self.avg_sentence_len:.0f}-word sentences",
            "punchy/short lines" if self.punchy else "flowing sentences",
            f"reading grade ~{self.reading_grade:.0f}",
        ]
        if self.emoji_heavy:
            bits.append("uses emoji liberally (" + " ".join(self.signature_emojis[:3]) + ")")
        elif self.signature_emojis:
            bits.append("occasional emoji (" + " ".join(self.signature_emojis[:2]) + ")")
        if self.energetic:
            bits.append("energetic, emphatic tone")
        if self.cta_phrases:
            bits.append("calls to action like: " + ", ".join(f'"{c}"' for c in self.cta_phrases[:2]))
        if self.top_terms:
            bits.append("niche vocabulary: " + ", ".join(self.top_terms[:6]))
        return "; ".join(bits)

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def load(cls, path: str) -> "VoiceProfile":
        with open(path, "r", encoding="utf-8") as fh:
            return cls(**json.load(fh))


def analyze(texts: List[str]) -> VoiceProfile:
    """Build a VoiceProfile from a list of the creator's past posts/scripts."""
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        return VoiceProfile()

    joined = "\n".join(texts)
    words = _WORD.findall(joined)
    n_words = len(words) or 1
    sentences = [s for s in _SENT.split(joined) if s.strip()] or [joined]
    n_sent = len(sentences)

    sent_lens = [len(_WORD.findall(s)) for s in sentences if _WORD.findall(s)]
    avg_sent = statistics.mean(sent_lens) if sent_lens else 14.0
    syll = sum(_syllables(w) for w in words)
    grade = 0.39 * (n_words / n_sent) + 11.8 * (syll / n_words) - 15.59

    emojis = _EMOJI.findall(joined)
    caps = [w for w in words if len(w) >= 2 and w.isupper()]
    lines = [ln.strip() for ln in joined.splitlines() if ln.strip()]
    bullets = [ln for ln in lines if ln[:1] in "-*•" or re.match(r"^\d+[.)]", ln)]

    lower = joined.lower()
    ctas = [p for p in _CTA_PATTERNS if p in lower]

    terms = Counter(w.lower() for w in words if len(w) > 3 and w.lower() not in _STOP)

    return VoiceProfile(
        samples=len(texts),
        words=n_words,
        avg_sentence_len=round(avg_sent, 1),
        reading_grade=round(max(1.0, grade), 1),
        emoji_per_100w=round(100 * len(emojis) / n_words, 2),
        exclamation_rate=round(joined.count("!") / n_sent, 3),
        question_rate=round(joined.count("?") / n_sent, 3),
        caps_emphasis_rate=round(100 * len(caps) / n_words, 2),
        list_usage=round(len(bullets) / len(lines), 3) if lines else 0.0,
        top_terms=[t for t, _ in terms.most_common(12)],
        signature_emojis=[e for e, _ in Counter(emojis).most_common(5)],
        cta_phrases=ctas[:5],
    )
