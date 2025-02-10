# FileCatcher
Fork自@whitebrise/BlurayPoster，感谢原作者。
FileCatcher是一个基于HTTP通知的BlurayPoster扩展，它通过 Flask 提供 HTTP 服务，允许外部设备通过联动FileWatcher触发播放请求。

## 支持设备
- 保留BlurayPoster原有功能
- 额外支持从多珀以及芝杜海报墙触发，调用蓝光机播放

## 工作原理
1. 用户浏览多珀或者芝杜海报墙，播放NAS/网盘电影 ->
2. 通过FileWatcher项目监控到多珀或者芝杜设备对文件的访问请求 ->
3. FileWatcher发送HTTP通知给FileCatcher，传递电影文件路径 ->
4. FileCatcher接收通知，利用BlurayPoster提供的功能，自动调用蓝光机播放电影（并同时停止在原多珀或者芝杜设备上的播放）

## 配置说明
仅需更改媒体库配置，删除emby相关所有配置，并替换为FileCatcher

```yaml
# 媒体库配置
Media:
  # 使用FileCatcher媒体库
  # 请预先安装和配置FileWatcher
  # https://github.com/narapeka/FileWatcher
  Executor: media.filecatcher.FileCatcher
  # HTTP服务端口，确保与FileWatcher中配置的端口一致
  HttpPort: 7507

  # 配置停止播放通知端点
  # 在doopoo或者zidoo设备的海报墙中，播放影片开始后，FileWatcher将监测到该播放事件，并启用FileCatcher调用蓝光机播放
  # 在蓝光机开始播放后，我们需要通知doopoo或者zidoo设备停止播放同一文件
  # doopoo配置
  PlayStopNotifyUrl: "http://<ip>:9527/doopoo/sendKey?action=KEYCODE_MEDIA_STOP&from=pc&keyValue=86"
  PlayStopNotifyMethod: "GET"

  # zidoo配置
  # PlayStopNotifyUrl: "http://<ip>:9529/VideoPlay/changeStatus?status=-1"
  # PlayStopNotifyMethod: "POST"
```