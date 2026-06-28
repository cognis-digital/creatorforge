"""creatorforge — the AI content team you own.

Research, ideas, hooks, scripts, captions, thumbnails, and platform-ready
packaging — trained on your voice, run on your hardware and your model. The
same pipeline agencies rent for five figures a month, as open software:

  * learns your voice from a corpus of your past posts (no model training, just
    measurable style features);
  * generates ideas, hooks, scripts, captions, and thumbnail concepts;
  * packages one core idea into platform-tailored deliverables for YouTube,
    Shorts, TikTok, Reels, X, and LinkedIn;
  * runs fully offline on a deterministic engine, and gets sharper the moment
    you plug in a local (Ollama) or cloud model — your choice, your data.

You film. creatorforge does the rest.
"""

from .voice import VoiceProfile, analyze
from .providers import Provider, TemplateProvider, OllamaProvider, get_provider
from .platforms import PLATFORMS, platform_spec
from .pipeline import ContentBrief, run_pipeline
from .longform import LongformBrief, build_longform
from .hardware import detect, recommend
from .capabilities import capabilities

__version__ = "0.1.0"
__all__ = [
    "VoiceProfile", "analyze",
    "Provider", "TemplateProvider", "OllamaProvider", "get_provider",
    "PLATFORMS", "platform_spec",
    "ContentBrief", "run_pipeline",
    "LongformBrief", "build_longform",
    "detect", "recommend", "capabilities",
    "__version__",
]
