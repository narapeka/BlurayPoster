# BlurayPoster修改版

Fork自[whitebrise/BlurayPoster](https://github.com/whitebrise/BlurayPoster)，感谢原作者。

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

检测到播放事件后，立即切换到蓝光机对应的HDMI口，而不是等待播放开始后才切换HDMI。
可以显著降低使用网盘或使用HDFury后的拉起等待时间。

### 4. Pioneer增加拉起mkv和mp4功能

如需拉起mkv和mp4，则需要额外配置设备序号

```yaml
  # smb_index 和 nfs_index 为pioneer播放mkv和mp4专用，如果是oppo或者不需要播放mkv和mp4，则无需配置
  # index的数字代表pioneer进入网络页面后，从上到下的共享设备序号，从1开始
  MappingPath:
    - Media: /path1
      SMB: /smb_host1
      SMB_INDEX: 2
      NFS: /192.168.1.10/path1
      NFS_INDEX: 3
    - Media: /path2
      SMB: /smb_host2
      SMB_INDEX: 1
      NFS: /192.168.1.10/path2
      NFS_INDEX: 4
```

### 5. Web控制台

- 内置 React 前端，可在浏览器查看运行状态、启动/停止/重载、在线编辑配置、实时查看日志（最多保留 200 条）。
- 访问地址 `http://<blurayposter_ip>:7508/`

## 如何使用

### 全新安装

建议使用Docker方式，镜像：**narapeka/blurayposter**

> **注意：必须采用host模式安装。**

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

### 升级安装

如果已经部署了原版`BlurayPoster`，两种方式迁移到修改版`narapeka/blurayposter`：
1. 备份原版`BlurayPoster`的`config.yaml`文件。全新安装修改版`BlurayPoster`之后，复制备份的`config.yaml`到新安装的容器，并添加新的媒体库执行器`media.file.Path`
2. 如果熟悉Docker容器如何修改镜像，比如使用`Portainer`，则可以修改原有BlurayPoster容器的镜像为`narapeka/blurayposter`，更新容器后再修改`config.yaml`文件添加新的媒体库执行器`media.file.Path`

添加新媒体库执行器`media.file.Path`的写法，注意media2与media同级：

```yaml
# 媒体库配置
Media:
  # 引用的媒体库执行器, 不要改
  Executor: media.emby.Emby
  # 设备客户端, 不要改
  Client: Emby Bluray Poster
  # 媒体库服务端显示的设备名称， 不要改
  Device: Bluray Poster
  # 设备唯一id， 不要改
  DeviceId: whitebrise
  # 其他emby相关配置参数
  ...

# 附加媒体库配置
Media2:
  # 使用芝杜海报墙媒体库
  # 请预先安装和配置ZidooWatcher
  # https://github.com/narapeka/ZidooWatcher

  # 或者使用多珀海报墙媒体库
  # 请预先安装和配置ADBWatcher
  # https://github.com/narapeka/ADBWatcher
  Executor: media.file.Path

# 播放器配置
Player:
  # 引用的播放机执行器(默认oppo)
  # 可供选择的执行器请看程序所在目录的player文件夹下，使用player.<filename>.<classname>来命名
  # 目前有以下几种:
    # player.oppo.Oppo
    # player.pioneer.Pioneer
  Executor: player.oppo.Oppo
```

### 完整配置样例

查看项目内`config/config.yaml`文件

## 安装Watcher

如果要支持emby以外的海报墙拉起蓝光机，需要另外再安装相应播放器对应的监测器，详见：

- **芝杜播放器**：安装 [ZidooWatcher](https://github.com/narapeka/ZidooWatcher)
- **多珀播放器**：安装 [ADBWatcher](https://github.com/narapeka/ADBWatcher)


