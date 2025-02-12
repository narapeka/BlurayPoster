# FileCatcher
Fork自[whitebrise/BlurayPoster](https://github.com/whitebrise/BlurayPoster)，感谢原作者。

FileCatcher是一个基于HTTP通知的BlurayPoster扩展，它通过 Flask 提供 HTTP 服务，允许外部设备通过联动FileWatcher触发播放请求。

## 支持设备
- 保留BlurayPoster原有功能
- 额外支持从多珀以及芝杜海报墙触发，调用蓝光机播放
- 配合FileWatcher基于文件系统底层的监听，理论上支持从任意海报墙app调用蓝光机播放。

## 工作原理
1. 用户浏览多珀或者芝杜海报墙，播放NAS/网盘电影 ->
2. 通过FileWatcher项目监控到多珀或者芝杜设备对文件的访问请求 ->
3. FileWatcher发送HTTP通知给FileCatcher，传递电影文件路径 ->
4. FileCatcher接收通知，利用BlurayPoster提供的功能，自动调用蓝光机播放电影（并同时停止在原多珀或者芝杜设备上的播放）

## 如何使用
1. 环境准备：运行Linux正规发行版(推荐Ubuntu/Debian)的amd64架构小主机或者NAS一台
2. 参阅FileWatcher项目，安装，配置并运行[FileWatcher](https://github.com/narapeka/FileWatcher)
3. 安装带有FileCatcher扩展的BlurayPoster，建议docker方式，镜像narapeka/blurayposter：
```bash
docker run -itd \
    --name blurayposter \
    --log-driver=json-file \
    --log-opt max-size=2m \
    --log-opt max-file=7 \
    --hostname blurayposter \
    -v /blurayposter/config:/config \
    -e 'PUID=0' \
    -e 'PGID=0' \
    -e 'UMASK=000' \
    -e 'TZ=Asia/Shanghai' \
    --restart unless-stopped \
    narapeka/blurayposter:latest
```
4. 配置BlurayPoster (见以下配置说明)
5. 首次运行，请注册小主机/NAS为 doopoo X3 信任设备：
```bash
curl --request GET \
  --url 'http://<盒子ip>:9527/doopoo/connect?uniqueId=any&from=any&ip=<小主机ip>'
```
或者用浏览器打开URL：
```url
http://<盒子ip>:9527/doopoo/connect?uniqueId=any&from=pc&ip=<小主机ip>
```
运行后X3设备上会弹出确认框，**点击确认**。

## 配置说明
参阅本项目config/config.yaml文件。

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
  PlayStopNotifyUrl: "http://<ip>:9527/doopoo/sendKey?action=KEYCODE_MEDIA_STOP&from=any&keyValue=86"
  PlayStopNotifyMethod: "GET"

  # zidoo配置
  # PlayStopNotifyUrl: "http://<ip>:9529/VideoPlay/changeStatus?status=-1"
  # PlayStopNotifyMethod: "POST"
```
