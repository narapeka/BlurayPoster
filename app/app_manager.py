import logging
import os
import threading
import time
from typing import Dict, List, Optional, Tuple

from abstract_classes import (
    AVException,
    MediaException,
    PlayerException,
    TVException,
)
from configuration import Configuration


logger = logging.getLogger(__name__)


def dynamic_import(module_name: str, class_name: str):
    """
    Dynamically import a class by module and class name.
    """
    try:
        module = __import__(module_name, fromlist=[class_name])
    except ModuleNotFoundError as e:
        raise ImportError(f"Error importing module {module_name}: {e}") from e
    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(
            f"Error importing class {class_name} from module {module_name}: {e}"
        ) from e


class AppManager:
    """
    Coordinates configuration loading, component initialization, lifecycle control,
    and simple status reporting for the BlurayPoster app.
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = Configuration(path=config_path)
        self.media_instances: List = []
        self.media_executor_names: List[str] = []
        self.player = None
        self.tv = None
        self.av = None

        self._state = "stopped"
        self._state_lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------
    # Config helpers
    # ------------------------------
    def load_config(self) -> bool:
        return self.config.initialize()

    def get_config_text(self) -> str:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return f.read()

    def update_config_text(self, content: str) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_config_version(self) -> Optional[str]:
        if self.config is None:
            return None
        try:
            return self.config.get("Version")
        except Exception:
            return None

    # ------------------------------
    # Component lifecycle
    # ------------------------------
    def _initialize_component(self, component_key, exception_class):
        component_config = self.config.get(component_key)
        executor = component_config.get("Executor") if component_config else None

        if component_config and executor:
            try:
                module_name, class_name = executor.rsplit(".", 1)
                cls = dynamic_import(module_name, class_name)
                return cls(component_config)
            except Exception as e:
                logger.error(f"Error importing {component_key}: {e}")
        elif component_config:
            logger.info("%s executor not configured; skipping", component_key)
        return None

    def _initialize_components(self) -> Tuple[Optional[List], Optional[List[str]]]:
        try:
            self.player = self._initialize_component("Player", PlayerException)
            self.tv = self._initialize_component("TV", TVException)
            self.av = self._initialize_component("AV", AVException)

            media_instances = []
            media_executor_names = []

            media_sections = [
                key for key in self.config._config.keys() if key.startswith("Media")
            ]
            media_sections.sort()

            for section_name in media_sections:
                media_config = self.config.get(section_name)
                if media_config and "Executor" in media_config:
                    try:
                        module_name, class_name = media_config["Executor"].rsplit(
                            ".", 1
                        )
                        media_class = dynamic_import(module_name, class_name)
                        media = media_class(self.player, self.tv, self.av, media_config)
                        media_instances.append(media)
                        media_executor_names.append(media_config["Executor"])
                        logger.info(
                            "%s Media executor initialized successfully: %s",
                            section_name,
                            media_config["Executor"],
                        )
                    except Exception as e:
                        logger.error(
                            "Error initializing %s Media executor (%s): %s",
                            section_name,
                            media_config.get("Executor", "Unknown"),
                            e,
                        )
                else:
                    logger.warning(
                        "%s Media executor is missing Executor field, skipping",
                        section_name,
                    )

            if not media_instances:
                raise MediaException("Error initializing Media: No valid executors.")

            logger.info("Successfully initialized %d Media executor(s)", len(media_instances))
            return media_instances, media_executor_names

        except (PlayerException, TVException, AVException, MediaException) as e:
            logger.error("Initialization error: %s", getattr(e, "message", str(e)))
            return None, None

    def _run_loop(self):
        logger.info(
            "Main application running with %d Media executor(s)",
            len(self.media_instances),
        )
        while not self._stop_event.wait(timeout=1):
            continue
        logger.info("Stop signal received, exiting main loop")

    def start(self) -> bool:
        with self._state_lock:
            if self._state == "running":
                logger.info("Application already running")
                return True
            self._stop_event.clear()

        if not self.load_config():
            logger.error("Failed to initialize configuration")
            with self._state_lock:
                self._state = "error"
            return False

        media_instances, media_executor_names = self._initialize_components()
        if media_instances is None:
            with self._state_lock:
                self._state = "error"
            return False

        self.media_instances = media_instances
        self.media_executor_names = media_executor_names

        # Initialize devices
        for media, executor_name in zip(self.media_instances, self.media_executor_names):
            try:
                media.start_before()
                logger.info("%s Media executor start_before() completed", executor_name)
            except Exception as e:
                logger.error("Error in %s start_before(): %s", executor_name, e)

        # Start devices
        for media, executor_name in zip(self.media_instances, self.media_executor_names):
            try:
                media.start()
                logger.info("%s Media executor start() completed", executor_name)
            except Exception as e:
                logger.error("Error in %s start(): %s", executor_name, e)

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        with self._state_lock:
            self._state = "running"
        return True

    def stop(self) -> bool:
        with self._state_lock:
            if self._state != "running":
                logger.info("Application already stopped")
                return True
            self._state = "stopping"
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

        self.media_instances = []
        self.media_executor_names = []
        self.player = None
        self.tv = None
        self.av = None

        with self._state_lock:
            self._state = "stopped"
        return True

    def reload(self) -> bool:
        logger.info("Reloading configuration and restarting components")
        self.stop()
        return self.start()

    # ------------------------------
    # Status helpers
    # ------------------------------
    def status(self) -> Dict:
        with self._state_lock:
            state = self._state
        return {
            "state": state,
            "configVersion": self.get_config_version(),
            "mediaExecutors": self.media_executor_names,
            "configPath": os.path.abspath(self.config_path),
            "running": state == "running",
        }

    def is_running(self) -> bool:
        with self._state_lock:
            return self._state == "running"


