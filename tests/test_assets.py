from pathlib import Path

from creatorforge.assets import Asset, LocalLibrary, gather
from creatorforge.compose import compose_thumbnail
from creatorforge.images import generate_thumbnail
from creatorforge.thumbnails import thumbnail_concepts


def _img(path: Path, w=320, h=200, color=(40, 80, 120)):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (w, h), color).save(path)


def build_library(tmp_path) -> LocalLibrary:
    _img(tmp_path / "beach" / "sunset_over_the_ocean.jpg")
    _img(tmp_path / "city" / "skyline_at_night.jpg")
    (tmp_path / "city" / "skyline_at_night.txt").write_text("downtown skyscrapers neon", encoding="utf-8")
    _img(tmp_path / "tech" / "server_rack_datacenter.png")
    return LocalLibrary().index([str(tmp_path)])


def test_library_indexes_images(tmp_path):
    lib = build_library(tmp_path)
    assert len(lib) == 3


def test_library_search_finds_related(tmp_path):
    lib = build_library(tmp_path)
    hits = lib.search("ocean sunset", 3)
    assert hits and Path(hits[0].ref).name == "sunset_over_the_ocean.jpg"
    # sidecar caption tokens are searchable too
    neon = lib.search("neon skyscrapers", 3)
    assert any("skyline" in Path(h.ref).name for h in neon)


def test_search_returns_multiple_related(tmp_path):
    lib = build_library(tmp_path)
    # a broad query touching two assets returns multiple
    hits = lib.search("night ocean", 3)
    assert len(hits) >= 1


def test_library_save_load(tmp_path):
    lib = build_library(tmp_path)
    idx = tmp_path / "idx.json"
    lib.save(str(idx))
    lib2 = LocalLibrary.load(str(idx))
    assert len(lib2) == len(lib)


def test_gather_offline_only(tmp_path):
    lib = build_library(tmp_path)
    res = gather("datacenter server", 4, library=lib, online=False)
    assert all(a.source == "local" and a.license == "owned" for a in res)


def test_compose_thumbnail_from_real_photo(tmp_path):
    hero = tmp_path / "hero.png"
    _img(hero, 1600, 900, (30, 60, 90))
    concept = thumbnail_concepts("owning your AI stack", None, 1)[0]
    res = compose_thumbnail(str(hero), concept, str(tmp_path / "thumb"))
    assert res["backend"] == "composite-photo"
    from PIL import Image
    img = Image.open(res["path"])
    assert img.size == (1280, 720)


def test_generate_thumbnail_uses_hero(tmp_path):
    hero = tmp_path / "h.png"
    _img(hero, 1280, 720)
    concept = thumbnail_concepts("x", None, 1)[0]
    res = generate_thumbnail(concept, str(tmp_path / "t"), hero=str(hero))
    assert res["backend"] == "composite-photo"
