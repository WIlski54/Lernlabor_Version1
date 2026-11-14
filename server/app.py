"""Garten-Labor-Server: liefert die Web-App aus. Plan 2 ergänzt Sitzungen, Teams und Speichern."""
import os

from flask import Flask, abort, jsonify, send_from_directory
from flask_compress import Compress

# Nur Text komprimieren; GLB (Meshopt), WebP, JPG und .bin sind schon gepackt.
TEXT_MIMETYPES = [
    "text/html", "text/css", "text/javascript", "application/javascript", "application/json",
]
# Unter diesen Präfixen liegen nur echte Dateien – fehlt eine, ist das ein 404, kein SPA-Fallback.
NUR_DATEIEN = ("welt", "assets")


def create_app(dist=None):
    dist = os.path.abspath(dist or os.environ.get(
        "WEB_DIST", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "dist")))
    app = Flask(__name__, static_folder=None)
    app.config["COMPRESS_MIMETYPES"] = TEXT_MIMETYPES
    Compress(app)

    @app.get("/api/gesundheit")
    def gesundheit():
        return jsonify(ok=True)

    def ausliefern(rel):
        unveraenderlich = rel.startswith("assets/")      # Vite-Dateinamen enthalten einen Hash
        # max_age an send_file geben – sonst setzt Werkzeug zusätzlich no-cache
        antwort = send_from_directory(dist, rel, max_age=31536000 if unveraenderlich else None)
        if antwort.status_code == 200 and antwort.mimetype in TEXT_MIMETYPES:
            # Datei-Antworten sind „gestreamt“; Flask-Compress packt Streams nicht mit gzip (Safari!)
            # und prüft dann kein ETag. Textdateien sind klein → als Ganzes in den Speicher.
            antwort.direct_passthrough = False
            antwort.make_sequence()
        if unveraenderlich:
            antwort.cache_control.immutable = True
        else:
            # welt/, sw.js, HTML: jedes Mal per ETag nachfragen (304, wenn unverändert)
            antwort.cache_control.no_cache = True
        return antwort

    @app.get("/", defaults={"pfad": "index.html"})
    @app.get("/<path:pfad>")
    def statisch(pfad):
        voll = os.path.abspath(os.path.join(dist, pfad))
        if voll.startswith(dist + os.sep) and os.path.isfile(voll):
            return ausliefern(os.path.relpath(voll, dist).replace(os.sep, "/"))
        # SPA-Fallback nur für „Seiten“: ohne Dateiendung und nicht unter welt/ oder assets/
        teile = pfad.replace("\\", "/").split("/")
        if os.path.splitext(teile[-1])[1] or teile[0] in NUR_DATEIEN or ".." in teile:
            abort(404)
        return ausliefern("index.html")

    return app


app = create_app()
