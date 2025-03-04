import logging
import threading
import requests
from flask import Flask, request, jsonify
from abstract_classes import Media, MediaException

logger = logging.getLogger(__name__)

BD_SUFFIX = ".bluray"

class FileCatcher(Media):
    def __init__(self, player, tv, av, config: dict):
        super().__init__(player, tv, av, config)
        try:
            # 读取配置
            self.http_port = config.get("HttpPort", 7507)
            self.notify_url = config.get("PlayStopNotifyUrl")
            self.notify_method = config.get("PlayStopNotifyMethod", "GET").upper()
            self.app = Flask(__name__)
            self._setup_routes()
            
            # 在独立线程启动Flask服务器
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
        except Exception as e:
            raise MediaException(f"FileCatcher init error: {str(e)}")

    def _setup_routes(self):
        @self.app.route('/play', methods=['POST'])
        def handle_play():
            try:
                # 获取请求的 JSON 数据
                data = request.get_json()
                file_path = data.get("file_path")
                if not file_path:
                    return jsonify({"status": "error", "message": "Missing file_path"}), 400

                # 通知外部设备停止播放
                if self.notify_url:
                    try:
                        response = self._send_play_stop_notification()
                        logger.info(f"Sent playback stop notification to {self.notify_url}, response: {response.status_code}")
                    except Exception as e:
                        logger.error(f"Failed to send notification: {str(e)}")
                        # 即使通知失败，也应继续执行播放

                # 获取bdmv路径
                if file_path.endswith(BD_SUFFIX):
                    media_path = file_path[:-len(BD_SUFFIX)]
                    media_path = media_path.rstrip('/')
                    media_container = "bluray"
                else:
                    media_path = file_path
                    media_container = file_path.split('.')[-1]

                # 调用播放器播放
                play_result = self._player.play(
                    media_path=media_path,
                    container=media_container,
                    on_message=self.on_message,
                    on_play_begin=self.on_play_begin,
                    on_play_in_progress=self.on_play_in_progress,
                    on_play_end=self.on_play_end
                )
                logger.info(f"Play result: {play_result}")
                
                if play_result:
                    return jsonify({"status": "success"})
                else:
                    return jsonify({"status": "error", "message": "Playback failed"}), 500

            except Exception as e:
                logger.error(f"Play failed: {str(e)}")
                return jsonify({"status": "error", "message": str(e)}), 500

    def _send_play_stop_notification(self):
        """ 根据配置的 HTTP 方法（GET/POST）发送播放停止通知 """
        headers = {"Content-Type": "application/json"}
        # for kodi/coreelec only
        data = {
            "jsonrpc": "2.0",
            "method": "Player.Stop",
            "params": {
                "playerid": 1
            },
            "id": 1
        }

        if self.notify_method == "GET":
            return requests.get(self.notify_url, timeout=3)
        elif self.notify_method == "POST":
            return requests.post(self.notify_url, json=data, headers=headers, timeout=3)
        else:
            logger.warning(f"Invalid notify method: {self.notify_method}, defaulting to GET")
            return requests.get(self.notify_url, timeout=3)

    def _run_server(self):
        # 启动 Flask 服务器
        self.app.run(host='0.0.0.0', port=self.http_port)

    def on_play_end(self, **kwargs):
        # 通知av,tv
        if self._tv is not None:
            try:
                self._tv.play_end(self.on_message)
            except Exception as e:
                logger.error(f"Exception during tv play end: {e}")
        if self._av is not None:
            try:
                self._av.play_end(self.on_message)
            except Exception as e:
                logger.error(f"Exception during av play end: {e}")

    # 其他必须实现的抽象方法（根据abstract_classes.Media要求）
    def start_before(self, **kwargs):
        # 初始化启动其他设备
        if self._player is not None:
            self._player.start_before()
        if self._tv is not None:
            self._tv.start_before()
        if self._av is not None:
            self._av.start_before()

    def on_play_begin(self, **kwargs):
        # 通知tv,av
        if self._tv is not None:
            try:
                self._tv.play_begin(self.on_message)
            except Exception as e:
                logger.error(f"Exception during tv play begin: {e}")
        if self._av is not None:
            try:
                self._av.play_begin(self.on_message)
            except Exception as e:
                logger.error(f"Exception during av play begin: {e}")


    def on_play_in_progress(self, **kwargs):
        pass

    def start(self, **kwargs):
        pass

    def on_message(self, header: str, message: str):
        pass
