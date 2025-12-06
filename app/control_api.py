import json
import logging
import os
import time
from typing import Optional

from flask import Flask, Response, jsonify, request, send_from_directory

from app.app_manager import AppManager
from app.logging_utils import LogBuffer


logger = logging.getLogger(__name__)


def _add_cors_headers(response, allow_origin: str):
    response.headers["Access-Control-Allow-Origin"] = allow_origin
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,OPTIONS"
    return response


def create_app(
    manager: AppManager, log_buffer: LogBuffer, static_folder: Optional[str] = None
) -> Flask:
    app = Flask(
        __name__,
        static_folder=static_folder if static_folder else None,
        static_url_path="/",
    )

    allow_origin = os.getenv("CONTROL_ALLOW_ORIGIN", "*")

    @app.after_request
    def add_cors(resp):
        return _add_cors_headers(resp, allow_origin)

    @app.route("/api/ping", methods=["GET"])
    def ping():
        return jsonify({"status": "ok"})

    @app.route("/api/status", methods=["GET"])
    def status():
        return jsonify(manager.status())

    @app.route("/api/start", methods=["POST"])
    def start():
        ok = manager.start()
        return jsonify({"ok": ok, "state": manager.status()["state"]})

    @app.route("/api/stop", methods=["POST"])
    def stop():
        ok = manager.stop()
        return jsonify({"ok": ok, "state": manager.status()["state"]})

    @app.route("/api/reload", methods=["POST"])
    def reload():
        ok = manager.reload()
        return jsonify({"ok": ok, "state": manager.status()["state"]})

    @app.route("/api/config", methods=["GET", "PUT", "OPTIONS"])
    def config():
        if request.method == "OPTIONS":
            resp = jsonify({"ok": True})
            return _add_cors_headers(resp, allow_origin)

        if request.method == "GET":
            try:
                return jsonify(
                    {
                        "content": manager.get_config_text(),
                        "path": manager.status()["configPath"],
                    }
                )
            except Exception as e:
                logger.error("Failed to read config: %s", e)
                return jsonify({"error": str(e)}), 500

        data = request.get_json(silent=True) or {}
        content = data.get("content", "")
        reload_flag = data.get("reload", True)
        try:
            manager.update_config_text(content)
            if reload_flag:
                manager.reload()
            return jsonify({"ok": True, "reloaded": bool(reload_flag)})
        except Exception as e:
            logger.error("Failed to update config: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/logs", methods=["GET"])
    def logs():
        return jsonify({"entries": log_buffer.get_entries()})

    @app.route("/api/logs/stream", methods=["GET"])
    def logs_stream():
        def event_stream():
            last_index = 0
            while True:
                entries = log_buffer.get_entries()
                if len(entries) > last_index:
                    new_entries = entries[last_index:]
                    last_index = len(entries)
                    for entry in new_entries:
                        yield f"data: {json.dumps(entry)}\n\n"
                time.sleep(1)

        return Response(event_stream(), mimetype="text/event-stream")

    if static_folder:
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path):
            if path and os.path.exists(os.path.join(static_folder, path)):
                return send_from_directory(static_folder, path)
            index_path = os.path.join(static_folder, "index.html")
            if os.path.exists(index_path):
                return send_from_directory(static_folder, "index.html")
            return "UI assets not built yet", 404

    return app


def run_control_app(app: Flask, host: str, port: int):
    logger.info("Starting control API on %s:%d", host, port)
    app.run(host=host, port=port, use_reloader=False, threaded=True)


