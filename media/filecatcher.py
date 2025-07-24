import logging
import threading
import requests
from flask import Flask, request, jsonify
from abstract_classes import Media, MediaException

logger = logging.getLogger(__name__)

class FileCatcher(Media):
    def __init__(self, player, tv, av, config: dict):
        super().__init__(player, tv, av, config)
        try:
            # 读取配置
            self.http_port = 7507
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

                # 判断是文件还是目录
                import os
                # 支持的视频文件扩展名
                video_extensions = ['iso', 'mkv', 'm2ts', 'mp4']
                file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
                
                if file_extension in video_extensions:  # 是支持的视频文件
                    media_path = file_path
                    media_container = file_extension
                    logger.info(f"Processing video file: {file_path}, container: {media_container}")
                else:  # 其他情况都视为目录（BDMV或其他）
                    media_path = file_path.rstrip('/')
                    media_container = "bluray"
                    logger.info(f"Processing directory: {file_path}, container: {media_container}")

                # 调用播放器播放
                play_result = self._player.play(
                    media_path=media_path,
                    container=media_container,
                    on_message=self.on_message,
                    on_play_begin=self.on_play_begin,
                    on_play_in_progress=self.on_play_in_progress,
                    on_play_end=self.on_play_end
                )

                # 返回成功响应
                return jsonify({"status": "success", "message": "Play request sent successfully"}), 200

            except Exception as e:
                logger.error(f"Play failed: {str(e)}")
                return jsonify({"status": "error", "message": str(e)}), 500

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
