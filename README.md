# BlurayPoster extended with FileCatcher
Fork自[whitebrise/BlurayPoster](https://github.com/whitebrise/BlurayPoster)，感谢原作者。

FileCatcher是一个基于HTTP通知的BlurayPoster扩展，它通过 Flask 提供 HTTP 服务，允许外部设备通过API直接发送播放请求。

## 支持设备
- 保留BlurayPoster原有功能
- 额外支持从芝杜以及多珀海报墙触发，调用蓝光机播放
- FileCatcher接收通知的endpoint是：`http://<ip>:7507/play`

## 工作原理
1. 用户浏览芝杜多珀海报墙，播放NAS/网盘电影 ->
2. 通过ZidooWatcher/ADBWathcer项目监控到事件，并发送媒体文件路径给FileCatcher ->
3. FileCatcher接收通知，利用BlurayPoster已有的功能，自动调用蓝光机播放电影


## 如何使用

### 安装
建议docker方式，镜像 **narapeka/blurayposter**：

docker-cli
```bash
docker run -itd \
    --name blurayposter \
    --log-driver=json-file \
    --log-opt max-size=2m \
    --log-opt max-file=7 \
    --network host \
    -v /blurayposter/config:/config \
    -e 'PUID=0' \
    -e 'PGID=0' \
    -e 'UMASK=000' \
    -e 'TZ=Asia/Shanghai' \
    --restart unless-stopped \
    narapeka/blurayposter:latest
```
docker compose
```yml
version: '3.8'

services:
    blurayposter:
        image: narapeka/blurayposter:latest
        container_name: blurayposter
        logging:
            driver: "json-file"
            options:
                max-size: "2m"
                max-file: "7"
        volumes:
            - /blurayposter/config:/config
        environment:
            - 'PUID=0'
            - 'PGID=0'
            - 'UMASK=000'
            - 'TZ=Asia/Shanghai'
        network_mode: host
        restart: unless-stopped
        tty: true
        stdin_open: true
```
**注意：必须采用host模式安装。**

### 配置

参阅本项目config/config.yaml文件。

仅需在原有BlurayPoster项目基础上，更改媒体库配置，使用 **media.filecatcher.FileCatcher** 执行器。

```yaml
# 媒体库配置
Media:
  # 使用芝杜海报墙媒体库
  # 请预先安装和配置ZidooWatcher
  # https://github.com/narapeka/ZidooWatcher

  # 或者使用多珀海报墙媒体库
  # 请预先安装和配置ADBWatcher
  # https://github.com/narapeka/ADBWatcher
  Executor: media.filecatcher.FileCatcher
```

### 安装Watcher

- 芝杜播放器，安装ZidooWatcher `https://github.com/narapeka/ZidooWatcher`
- 多珀播放器，安装ADBWatcher `https://github.com/narapeka/ADBWatcher`


