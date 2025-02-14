# BlurayPoster extended with FileCatcher
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

### 1. 环境准备
运行Linux正规发行版 (推荐Ubuntu/Debian) 的amd64架构小主机/NAS一台，假设ip设定为192.168.1.50

### 2. 安装本项目
在小主机/NAS上安装本项目 (带有FileCatcher扩展的BlurayPoster)，建议docker方式，镜像narapeka/blurayposter：
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
### 3. 配置本项目
参见以下配置说明。配置完成后重启BlurayPoster

### 4. 设备注册

#### 4.1 Doopoo X3
首次运行，请注册小主机/NAS为 doopoo X3 的信任设备，两种方式：
```bash
curl --request GET \
  --url 'http://<盒子ip>:9527/doopoo/connect?uniqueId=any&from=any&ip=<小主机ip>'
```
或用浏览器打开URL：
```url
http://<盒子ip>:9527/doopoo/connect?uniqueId=any&from=pc&ip=<小主机ip>
```
运行后X3设备上会弹出确认框，**点击确认**。

#### 4.2 其他设备首次连接，是否需要信任握手，未经测试。有条件的请自行测试并提交issue。

### 5. 安装FileWatcher
在小主机/NAS上安装FileWatcher项目

配置参考：https://github.com/narapeka/FileWatcher

注意事项:
- http_server指向安装了BlurayPoster的小主机/NAS，即192.168.1.50
- 盒子海报墙请禁用自动刷新/自动更新设备之类，避免访问文件系统导致误拉起蓝光机。
- 同理，刮削时请停止FileWatcher服务或者关闭蓝光机

关闭FileWatcher服务
```bash
sudo systemctl stop filewatcher
```
启动FileWatcher服务
```bash
sudo systemctl start filewatcher
```

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
  PlayStopNotifyUrl: "http://<ip>:9527/doopoo/sendKey?action=KEYCODE_MEDIA_STOP&from=pc&keyValue=86"
  PlayStopNotifyMethod: "GET"

  # zidoo配置
  # PlayStopNotifyUrl: "http://<ip>:9529/VideoPlay/changeStatus?status=-1"
  # PlayStopNotifyMethod: "POST"

  # kodi/coreelec配置 (在kodi/coreelec中先开启web服务，并关闭web登录验证)
  # PlayStopNotifyUrl: "http://<ip>:8080/jsonrpc"
  # PlayStopNotifyMethod: "POST"

  # dune配置
  # PlayStopNotifyUrl: "http://<ip>:8080/cgi-bin/do?cmd=ir_code&ir_code=stop"
  # PlayStopNotifyMethod: "GET"
```

配置文件路径映射时：

源路径为FileWatcher监控的目录之完整路径，也就是盒子海报墙刮削时使用的路径。

目标路径为蓝光机能访问的SMB路径 (参见原BlurayPoster项目说明)
```yaml
  # 文件夹映射路径(不用的协议路径值可以留空)
  # 文件最后有路径配置说明, pioneer请参照 pioneer部分
  MappingPath:
    - Media: /path1 # FileWatcher监控的目录，确保与FileWatcher中配置的目录一致
      SMB: /smb_host1
      NFS: /192.168.1.10/path1
    - Media: /path2 # FileWatcher监控的目录，确保与FileWatcher中配置的目录一致
      SMB: /smb_host2
      NFS: /192.168.1.10/path2
```
