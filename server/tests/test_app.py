import gzip
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app  # noqa: E402

GROSSES_JS = "console.log('Garten-Labor');\n" * 200  # deutlich über COMPRESS_MIN_SIZE (500 B)


def _app(tmp_path):
    # Neben dist liegt eine „geheime“ app.py – ein Pfadausbruch würde sie ausliefern.
    (tmp_path / "app.py").write_text("def create_app(): GEHEIM", encoding="utf-8")
    dist = tmp_path / "dist"
    (dist / "welt").mkdir(parents=True)
    (dist / "assets").mkdir()
    (dist / "index.html").write_text("<html>Garten-Labor</html>", encoding="utf-8")
    (dist / "welt" / "haus.glb").write_bytes(b"glTF" + bytes(4000))
    (dist / "assets" / "index-abc123.js").write_bytes(GROSSES_JS.encode("utf-8"))
    (dist / "sw.js").write_text("// sw", encoding="utf-8")
    return create_app(str(dist)).test_client()


def _ist_index(r):
    return r.status_code == 200 and b"Garten-Labor" in r.data


def test_gesundheit(tmp_path):
    r = _app(tmp_path).get("/api/gesundheit")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True}


def test_startseite_und_spa_fallback(tmp_path):
    c = _app(tmp_path)
    assert _ist_index(c.get("/"))
    r = c.get("/irgendwas/unbekannt")
    assert _ist_index(r)
    assert r.cache_control.no_cache


def test_fehlende_weltdatei_ist_404(tmp_path):
    assert _app(tmp_path).get("/welt/fehlt.glb").status_code == 404


def test_fehlendes_asset_ist_404(tmp_path):
    assert _app(tmp_path).get("/assets/alt-123.js").status_code == 404


def test_fehlende_datei_mit_endung_ist_404(tmp_path):
    assert _app(tmp_path).get("/irgendwo/bild.png").status_code == 404


def test_weltdateien_mit_etag_revalidierung(tmp_path):
    c = _app(tmp_path)
    r = c.get("/welt/haus.glb")
    assert r.status_code == 200
    assert r.data.startswith(b"glTF")
    assert r.cache_control.no_cache
    assert r.headers.get("ETag")
    assert c.get("/welt/haus.glb", headers={"If-None-Match": r.headers["ETag"]}).status_code == 304


def test_assets_unveraenderlich(tmp_path):
    r = _app(tmp_path).get("/assets/index-abc123.js")
    assert r.status_code == 200
    assert r.cache_control.max_age == 31536000
    assert r.cache_control.immutable


def test_service_worker_nicht_zwischengespeichert(tmp_path):
    r = _app(tmp_path).get("/sw.js")
    assert r.status_code == 200
    assert r.cache_control.no_cache


def test_kein_pfad_ausbruch(tmp_path):
    c = _app(tmp_path)
    for url in ("/../app.py", "/%2e%2e/app.py", "/welt/..%2f..%2fapp.py", "/welt/%2e%2e/%2e%2e/app.py"):
        r = c.get(url)
        assert b"GEHEIM" not in r.data, url
        assert r.status_code == 404 or _ist_index(r), url


def test_text_wird_gzip_komprimiert(tmp_path):
    r = _app(tmp_path).get("/assets/index-abc123.js", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert r.headers.get("Content-Encoding") == "gzip"
    assert gzip.decompress(r.data).decode("utf-8") == GROSSES_JS


def test_komprimierter_text_mit_etag_revalidierung(tmp_path):
    c = _app(tmp_path)
    kopf = {"Accept-Encoding": "gzip"}
    r = c.get("/assets/index-abc123.js", headers=kopf)
    etag = r.headers["ETag"]
    assert c.get("/assets/index-abc123.js", headers={**kopf, "If-None-Match": etag}).status_code == 304


def test_startseite_gzip(tmp_path):
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "index.html").write_text("<html>Garten-Labor" + " " * 2000 + "</html>", encoding="utf-8")
    r = create_app(str(tmp_path / "dist")).test_client().get("/", headers={"Accept-Encoding": "gzip"})
    assert r.headers.get("Content-Encoding") == "gzip"
    assert b"Garten-Labor" in gzip.decompress(r.data)


def test_glb_wird_nicht_komprimiert(tmp_path):
    r = _app(tmp_path).get("/welt/haus.glb", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert "Content-Encoding" not in r.headers
    assert r.data.startswith(b"glTF")
