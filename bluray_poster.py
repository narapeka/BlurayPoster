"""
Copyright (C) 2025 whitebrise

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version
"""

import logging
import os
import threading
import time

from app.app_manager import AppManager
from app.control_api import create_app, run_control_app
from app.logging_utils import LogBuffer, setup_logging
from configuration import Configuration


def bootstrap_logging(config_path: str) -> LogBuffer:
    """
    Initialize logging with configured level and in-memory buffer.
    """
    temp_config = Configuration(path=config_path)
    temp_config.initialize()
    log_level = temp_config.get("LogLevel") or "info"
    log_buffer = LogBuffer(max_entries=200)
    setup_logging(log_level, log_buffer)
    return log_buffer


def main():
    config_dir = os.getenv("CONFIG_DIR", "config") + "/config.yaml"
    control_port = int(os.getenv("CONTROL_PORT", "7508"))
    control_host = os.getenv("CONTROL_HOST", "0.0.0.0")

    log_buffer = bootstrap_logging(config_dir)
    logger = logging.getLogger(__name__)
    logger.info("Starting BlurayPoster with config: %s", config_dir)
    # Silence noisy Werkzeug/Flask request logs so only core app logs remain.
    werk_logger = logging.getLogger("werkzeug")
    werk_logger.setLevel(logging.CRITICAL)
    werk_logger.propagate = False
    werk_logger.disabled = True
    logging.getLogger("werkzeug.serving").disabled = True
    # Flask app logger (used by Flask itself) can also be muted.
    logging.getLogger("flask.app").disabled = True

    manager = AppManager(config_path=config_dir)
    api_static = os.path.join(os.path.dirname(__file__), "webui", "dist")
    static_folder = api_static if os.path.exists(api_static) else None
    control_app = create_app(manager, log_buffer, static_folder=static_folder)

    api_thread = threading.Thread(
        target=run_control_app, args=(control_app, control_host, control_port), daemon=True
    )
    api_thread.start()

    if not manager.start():
        logger.error("Failed to start manager; exiting")
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        manager.stop()


if __name__ == "__main__":
    main()
