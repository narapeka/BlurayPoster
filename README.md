# BlurayPoster extended with FileCatcher

Fork自[whitebrise/BlurayPoster](https://github.com/whitebrise/BlurayPoster)，感谢原作者。

## 目录

- [Fork添加的功能](#fork添加的功能)
- [如何使用](#如何使用)
  - [安装](#安装)
  - [安装Watcher](#安装watcher)

## Fork添加的功能

### 1. 新媒体库执行器 

- 添加了新媒体库执行器 `media.file.Path`，支持以HTTP接口方式传入媒体文件路径，直接调用蓝光机播放。
- filePath执行器的接口为：`http://<blurayposter_ip>:7507/play`
- 搭配ZidooWatcher/ADBWathcer项目，可监控芝杜/多珀海报墙事件，推送文件路径到filePath执行器。

```yaml
# 媒体库配置
Media:
  # 使用芝杜海报墙媒体库
  # 请预先安装和配置ZidooWatcher
  # https://github.com/narapeka/ZidooWatcher

  # 或者使用多珀海报墙媒体库
  # 请预先安装和配置ADBWatcher
  # https://github.com/narapeka/ADBWatcher
  Executor: media.file.Path
```

### 2. 支持配置多个媒体库执行器

- 可以同时配置emby和filePath执行器
- 不同的执行器处理不同媒体源的播放事件，互不冲突
- **保持向后兼容性**，现有配置无需更改

**示例：Emby + filePath**

```yaml
# 保持现有 Emby 配置不变
Media:
  Executor: media.emby.Emby
  Server: http://your-emby-server:8096
  ApiKey: your-api-key
  # ... 所有其他 Emby 参数

# 添加 filePath 作为新的媒体执行器
Media2:
  Executor: media.file.Path
```

### 3. 优化调用蓝光机的拉起时间

## 如何使用

### 安装

#### 全新安装

建议使用Docker方式，镜像：**narapeka/blurayposter**

#### 升级安装

- 如果已经部署了原版 BlurayPoster，仅需更改镜像名后升级容器，原有配置可继续工作。
- 如果需要增加filePath执行器，仅需如上所述修改 `config.yaml` 文件，添加 `media2` 执行器为 `media.file.Path`

#### Docker CLI 安装

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

#### Docker Compose 安装

```yaml
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

> **注意：必须采用host模式安装。**

### 安装Watcher

- **芝杜播放器**：安装 [ZidooWatcher](https://github.com/narapeka/ZidooWatcher)
- **多珀播放器**：安装 [ADBWatcher](https://github.com/narapeka/ADBWatcher)


