from gevent.pywsgi import WSGIServer
from flask import Flask

app = Flask("")


@app.route("/health")
def health() -> tuple[str, int]:
    return "ok", 200


def start_healthcheck_endpoint() -> None:

    http_server = WSGIServer(('', 8089), app, log=None)
    http_server.serve_forever()
