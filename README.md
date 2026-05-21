# Media Center

个人媒体中心 - AList + Jellyfin + MoviePilot 一键部署。

聚合百度网盘/迅雷网盘/CloudDrive2/本地磁盘，支持在线播放、媒体刮削、自动识别归类。附带文件去重和归类脚本。

## 架构

```
百度网盘 ──┐                    ┌── TMDB 自动刮削
迅雷网盘 ──┼── AList ──WebDAV──►│   Jellyfin (:8096)
CloudDrive2┘   (:5244)         └── 在线转码播放
                                        ▲
E:/ 本地视频/下载 ──────────────────────┘
    │
    └── MoviePilot (:3000)
        ├── 自动识别电影/剧集
        ├── 重命名 + 分类整理
        └── 订阅追更自动下载
```

## 服务清单

| 服务 | 端口 | 用途 |
|------|------|------|
| AList | 5244 | 云盘聚合、WebDAV、文件浏览 |
| Jellyfin | 8096 | 媒体库管理、刮削、在线播放 |
| MoviePilot | 3000 | 自动识别、重命名、分类、订阅追更 |

## 快速开始

### 1. 一键启动

```bash
# Windows
start.bat

# Linux/Mac
bash start.sh

# 或直接
docker-compose up -d
```

### 2. 初始化配置

#### AList (http://localhost:5244)

```bash
# 查看初始管理员密码
docker logs media-alist 2>&1 | grep -i "password"
```

登录后到 **管理 → 存储** 添加云盘：

| 云盘 | 驱动类型 | 配置要点 |
|------|---------|---------|
| 百度网盘 | 百度网盘 | OAuth 授权获取刷新令牌 |
| 迅雷网盘 | 迅雷 | 填写迅雷账号密码 |
| CloudDrive2 | WebDAV | 地址 `http://localhost:19798/dav` + CD2 账号密码 |
| 本地磁盘 | 本机存储 | 已通过 Docker 挂载，可选配置 |

#### Jellyfin (http://localhost:8096)

1. 按向导设置语言(中文)、创建管理员
2. 添加媒体库 → 文件夹 `/media/local`（E 盘本地视频）
3. 刮削语言设为 Chinese，启用 TheMovieDb
4. 添加 `/media/organized` 目录（MoviePilot 整理后的文件）

#### MoviePilot (http://localhost:3000)

1. 账号 `admin`，首次登录设置密码
2. 设置 → 媒体服务器 → 配置 Jellyfin（地址 `http://jellyfin:8096`）
3. 设置 → 目录 → 下载目录 `/download`，媒体库目录 `/media`
4. MoviePilot 会自动监控 E 盘文件，识别后重命名并整理到 `/media`
5. 整理完的文件会自动出现在 Jellyfin 媒体库中

### 3. 对接 AList 到 Jellyfin

用 rclone 把 AList WebDAV 挂载为本地盘：

```bash
# 安装 rclone: https://rclone.org/downloads/
rclone config
# New remote → 命名 alist → 类型 webdav
# URL: http://localhost:5244/dav
# Vendor: Other → 填 AList 账号密码

# 挂载为 Z: 盘
rclone mount alist:/ Z: --vfs-cache-mode full --vfs-cache-max-size 10G
```

然后在 Jellyfin 中添加 Z: 盘作为媒体库。

## 工具脚本

### 文件去重 (scripts/dedup.py)

扫描指定目录，按文件大小 + MD5 哈希查找重复文件。

```bash
# 扫描并输出报告（不删除）
python scripts/dedup.py E:/Movies

# 只扫描视频文件
python scripts/dedup.py E:/Movies --video-only

# 扫描并删除重复文件（保留每组第一个，会二次确认）
python scripts/dedup.py E:/Movies --delete

# 指定最小文件大小（默认 1MB）
python scripts/dedup.py E:/Movies --min-size 100
```

输出示例：
```
--- 重复组 #1 | 文件大小: 1.4 GB | 浪费: 1.4 GB ---
  [保留] E:\Movies\复仇者联盟4.mkv
  [重复] E:\Movies\备份\复仇者联盟4.mkv

======================================
  共发现 3 组重复，5 个冗余文件
  可回收空间: 8.2 GB
======================================
```

### 媒体文件归类 (scripts/organize.py)

按文件类型自动将散落的文件整理到分类目录。

```bash
# 预览归类结果（不移动文件）
python scripts/organize.py E:/Downloads

# 执行归类
python scripts/organize.py E:/Downloads --execute

# 指定输出目录
python scripts/organize.py E:/Downloads --output E:/Media --execute

# 复制而非移动
python scripts/organize.py E:/Downloads --output E:/Media --execute --copy
```

归类规则：
```
输出目录/
├── 电影/         .mp4, .mkv, .avi 等（单文件）
├── 电视剧/       带 S01E01、第X集 等特征的视频
├── 音乐/         .mp3, .flac, .wav 等
├── 图片/         .jpg, .png, .gif 等
├── 字幕/         .srt, .ass, .ssa 等
├── 文档/         .pdf, .doc, .txt 等
├── 压缩包/       .zip, .rar, .7z 等
└── 其他/
```

## 目录结构

```
media-center/
├── docker-compose.yml      # 服务编排（AList + Jellyfin + MoviePilot）
├── scripts/
│   ├── dedup.py            # 文件去重工具
│   └── organize.py         # 媒体文件归类工具
├── start.bat               # Windows 一键启动
├── start.sh                # Linux 一键启动
├── .env.example            # 环境变量模板
├── .gitignore
└── README.md
```

## 存储映射

| 宿主机路径 | 容器内路径 | 内容 |
|-----------|-----------|------|
| G:/docker-data/alist | /opt/alist/data | AList 配置和数据库 |
| G:/docker-data/jellyfin/config | /config | Jellyfin 配置、刮削元数据、海报 |
| G:/docker-data/jellyfin/cache | /cache | Jellyfin 转码缓存 |
| G:/docker-data/moviepilot/config | /config | MoviePilot 配置 |
| G:/docker-data/moviepilot/media | /media | 整理后的媒体文件 |
| E:/ | /download + /media/local | 本地视频和下载文件 |

## 常见问题

### AList 忘记密码
```bash
docker exec -it media-alist ./alist admin random
```

### Jellyfin 刮削失败
- 确认能访问 api.themoviedb.org（可能需要代理）
- Jellyfin 控制台 → 网络 → 配置 HTTP 代理
- 文件命名规范化：`电影名 (年份)/电影名 (年份).mkv`

### 视频播放卡顿
- Jellyfin 控制台 → 播放 → 启用硬件转码
- Windows Docker 不支持 GPU 直通，可改用 Jellyfin Windows 原生安装

### MoviePilot 无法识别文件
- 确认文件名包含电影/剧集名称
- 查看日志：`docker logs media-moviepilot`
- 在 MoviePilot Web UI 中手动搜索匹配
