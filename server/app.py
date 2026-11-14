"""Garten-Labor-Server: liefert die Web-App aus. Plan 2 ergänzt Sitzungen, Teams und Speichern."""
import os

from flask import Flask, jsonify, send_from_directory


def create_app(dist=None):
    dist = os.path.abspath(dist or os.environ.get(
        "WEB_DIST", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "dist")))
    app = Flask(__name__, static_folder=None)

    @app.get("/api/gesundheit")
    def gesundheit():
        return jsonify(ok=True)

    @app.get("/", defaults={"pfad": "index.html"})
    @app.get("/<path:pfad>")
    def statisch(pfad):
        voll = os.path.abspath(os.path.join(dist, pfad))
        if not voll.startswith(dist + os.sep) or not os.path.isfile(voll):
            pfad = "index.html"
        antwort = send_from_directory(dist, pfad)
        if pfad.startswith("assets/"):
            antwort.cache_control.max_age = 31536000      # Vite-Dateinamen enthalten einen Hash
            antwort.cache_control.immutable = True
        elif pfad.startswith("welt/"):
            antwort.cache_control.max_age = 3600
        else:
            antwort.cache_control.no_cache = True
        return antwort

    return app


app = create_app()
