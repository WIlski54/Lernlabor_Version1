import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app  # noqa: E402


def _app(tmp_path):
    (tmp_path / "welt").mkdir()
    (tmp_path / "index.html").write_text("<html>Garten-Labor</html>", encoding="utf-8")
    (tmp_path / "welt" / "haus.glb").write_bytes(b"glTF")
    (tmp_path / "sw.js").write_text("// sw", encoding="utf-8")
    return create_app(str(tmp_path)).test_client()


def test_gesundheit(tmp_path):
    r = _app(tmp_path).get("/api/gesundheit")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True}


def test_startseite_und_spa_fallback(tmp_path):
    c = _app(tmp_path)
    assert b"Garten-Labor" in c.get("/").data
    assert b"Garten-Labor" in c.get("/irgendwas/unbekannt").data


def test_weltdateien_mit_cache(tmp_path):
    r = _app(tmp_path).get("/welt/haus.glb")
    assert r.status_code == 200
    assert r.data == b"glTF"
    assert r.cache_control.max_age == 3600


def test_service_worker_nicht_zwischengespeichert(tmp_path):
    r = _app(tmp_path).get("/sw.js")
    assert r.status_code == 200
    assert r.cache_control.no_cache


def test_kein_pfad_ausbruch(tmp_path):
    r = _app(tmp_path).get("/../app.py")
    assert b"Garten-Labor" in r.data or r.status_code == 404
