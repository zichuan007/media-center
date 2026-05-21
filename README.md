# Media Center

个人媒体中心 - AList + Jellyfin 一键部署，聚合百度网盘/迅雷网盘/CloudDrive2/本地磁盘，支持在线播放和媒体刮削。

## 架构

```
百度网盘 ──┐
迅雷网盘 ──┼── AList (:5244) ──WebDAV──► Jellyfin (:8096)
CloudDrive2┘       │                       ├── TMDB 自动刮削
                   │                       ├── 在线转码播放
              Web 文件管理器               └── 多端访问
                                    E:/ 本地视频 ──────┘
```

## 端口

| 服务 | 端口 | 用途 |
|------|------|------|
| AList | 5244 | 云盘聚合、WebDAV 服务、文件管理 |
| Jellyfin | 8096 | 媒体库管理、刮削、在线播放 |

## 快速开始

### 1. 创建数据目录

```bash
mkdir -p G:/docker-data/alist
mkdir -p G:/docker-data/jellyfin/config
mkdir -p G:/docker-data/jellyfin/cache
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. AList 初始化

```bash
# 查看初始管理员密码
docker logs media-alist 2>&1 | grep "password"
```

访问 http://localhost:5244 ，使用 admin + 上面的密码登录。

登录后到 **管理 → 存储** 中添加云盘：

#### 添加百度网盘

1. 驱动选择 **百度网盘**
2. 根据提示完成 OAuth 授权（需要在百度开放平台注册应用获取 API Key，或使用 AList 提供的默认 Key）
3. 填写刷新令牌，保存

#### 添加迅雷网盘

1. 驱动选择 **迅雷**
2. 填写迅雷账号和密码
3. 保存

#### 添加 CloudDrive2

1. 驱动选择 **CloudDrive**（WebDAV 模式）
2. 填写 CloudDrive2 的 WebDAV 地址（通常是 `http://localhost:19798/dav`）
3. 填写 CloudDrive2 的用户名密码
4. 保存

#### 添加本地磁盘

本地磁盘已通过 Docker 挂载，无需在 AList 中配置。如需通过 AList 也浏览本地文件：

1. 驱动选择 **本机存储**
2. 根目录填 `/` 或特定路径
3. 保存

### 4. Jellyfin 初始化

访问 http://localhost:8096 ，按向导操作：

1. 选择语言 → **中文**
2. 创建管理员账号
3. 添加媒体库：
   - 类型：电影/电视节目
   - 文件夹：`/media/local`（E 盘本地视频）
4. 元数据刮削：
   - 语言：**Chinese**
   - 国家/地区：**China**
   - 启用 **TheMovieDb** 刮削器

### 5. Jellyfin 挂载 AList 云盘资源

Jellyfin 不能直接读 AList，需要通过 rclone 将 AList 的 WebDAV 挂载为本地目录：

#### 方式一：rclone 挂载（推荐）

```bash
# 安装 rclone（Windows 下载: https://rclone.org/downloads/）
# 配置 AList WebDAV
rclone config
# 选择 New remote → 命名 alist → 类型 webdav
# URL: http://localhost:5244/dav
# Vendor: Other
# User: admin
# Password: 你的 AList 密码

# 挂载为本地驱动器（比如 Z:）
rclone mount alist:/ Z: --vfs-cache-mode full --vfs-cache-max-size 10G
```

然后在 Jellyfin 中添加媒体库，路径指向 Z: 盘。

#### 方式二：Docker 内 rclone sidecar

如需容器化部署 rclone，可在 docker-compose.yml 中添加 rclone 容器，挂载到 Jellyfin 的 `/media/cloud` 目录。

## 目录结构

```
media-center/
├── docker-compose.yml    # 服务编排
├── .env.example          # 环境变量模板
├── .gitignore
└── README.md             # 本文件
```

## 存储说明

| 目录 | 内容 |
|------|------|
| `G:/docker-data/alist` | AList 配置、数据库、缓存 |
| `G:/docker-data/jellyfin/config` | Jellyfin 配置、刮削元数据、海报 |
| `G:/docker-data/jellyfin/cache` | Jellyfin 转码缓存 |
| `E:/` | 本地视频文件（只读挂载） |

## 常见问题

### AList 忘记密码

```bash
docker exec -it media-alist ./alist admin random
```

### Jellyfin 刮削失败

- 确认网络可以访问 api.themoviedb.org（可能需要代理）
- 在 Jellyfin 控制台 → 网络 中配置 HTTP 代理
- 文件命名尽量规范：`电影名 (年份)/电影名 (年份).mkv`

### 视频播放卡顿

- 检查 Jellyfin 是否启用了硬件转码（控制台 → 播放 → 转码）
- Windows 下 Docker Desktop 默认不支持 GPU 直通，可考虑直接安装 Jellyfin Windows 版本以获得硬件加速
