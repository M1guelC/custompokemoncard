"""Web app Vercel runs. The desktop window still starts from main.py."""

from flask import Flask, Response, request

from cardmaker.server import answer

app = Flask(__name__)


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def site(path):
    status, content_type, payload = answer(
        request.method,
        "/" + path,
        request.headers.get("Content-Type", ""),
        request.get_data(),
    )
    response = Response(payload, status=status, mimetype=content_type)
    response.headers["Cache-Control"] = "no-store"
    return response
