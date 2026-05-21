#!/usr/bin/env python3
"""
媒体文件自动归类工具 - 按文件类型将散落的文件整理到分类目录

用法:
    # 预览归类结果（不移动文件）
    python organize.py E:/Downloads

    # 执行归类（移动文件到分类目录）
    python organize.py E:/Downloads --execute

    # 指定输出目录（默认在扫描目录下创建分类文件夹）
    python organize.py E:/Downloads --output E:/Media --execute

目录结构示例:
    E:/Media/
    ├── 电影/          (.mp4, .mkv, .avi 等，单文件)
    ├── 电视剧/        (按文件夹识别的剧集)
    ├── 音乐/          (.mp3, .flac, .wav 等)
    ├── 图片/          (.jpg, .png, .gif 等)
    ├── 字幕/          (.srt, .ass, .ssa 等)
    ├── 文档/          (.pdf, .doc, .txt 等)
    ├── 压缩包/        (.zip, .rar, .7z 等)
    └── 其他/

@author media-center
@version V1.0
@since 2026-05-22
"""

import os
import sys
import shutil
import argparse
import re
from datetime import datetime

# 文件类型分类规则
CATEGORY_MAP = {
    '电影': {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.ts',
            '.rmvb', '.rm', '.m4v', '.mpg', '.mpeg', '.webm', '.iso'},
    '音乐': {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.wma', '.ape', '.m4a'},
    '图片': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg', '.ico'},
    '字幕': {'.srt', '.ass', '.ssa', '.sub', '.idx', '.sup', '.vtt'},
    '文档': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.md', '.csv', '.epub', '.mobi'},
    '压缩包': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'},
}

# 剧集文件名模式（S01E01, EP01, 第01集 等）
EPISODE_PATTERNS = [
    re.compile(r'[Ss]\d{1,2}[Ee]\d{1,2}'),
    re.compile(r'[Ee][Pp]?\d{1,3}', re.IGNORECASE),
    re.compile(r'第\s*\d+\s*[集话]'),
    re.compile(r'\b\d{1,2}of\d{1,2}\b', re.IGNORECASE),
]

# 忽略的文件和目录
IGNORE_DIRS = {'.git', '.svn', '__MACOSX', '@eaDir', '#recycle', 'System Volume Information'}
IGNORE_FILES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}


def get_category(filepath):
    """根据文件扩展名和文件名判断分类"""
    ext = os.path.splitext(filepath)[1].lower()
    filename = os.path.basename(filepath)

    # 先按扩展名分类
    for category, extensions in CATEGORY_MAP.items():
        if ext in extensions:
            # 视频文件进一步区分电影和电视剧
            if category == '电影':
                if is_episode(filename) or is_episode(os.path.dirname(filepath)):
                    return '电视剧'
                return '电影'
            return category

    # NFO 文件归类到字幕（刮削信息）
    if ext == '.nfo':
        return '字幕'

    return '其他'


def is_episode(text):
    """判断文件名或路径是否包含剧集特征"""
    for pattern in EPISODE_PATTERNS:
        if pattern.search(text):
            return True
    return False


def format_size(size_bytes):
    """字节转人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def scan_and_classify(directory, min_size_mb=0):
    """扫描目录并分类文件"""
    min_size = min_size_mb * 1024 * 1024
    classified = {}
    skipped = 0

    for root, dirs, files in os.walk(directory):
        # 过滤忽略的目录
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for name in files:
            if name in IGNORE_FILES:
                continue

            filepath = os.path.join(root, name)
            try:
                size = os.path.getsize(filepath)
                if size < min_size:
                    skipped += 1
                    continue
            except OSError:
                skipped += 1
                continue

            category = get_category(filepath)
            if category not in classified:
                classified[category] = []
            classified[category].append({
                'path': filepath,
                'name': name,
                'size': size,
            })

    return classified, skipped


def preview_plan(classified, output_dir):
    """预览归类计划"""
    print("\n" + "=" * 60)
    print("  归类预览")
    print("=" * 60)

    total_files = 0
    total_size = 0

    for category in sorted(classified.keys()):
        files = classified[category]
        cat_size = sum(f['size'] for f in files)
        total_files += len(files)
        total_size += cat_size

        target = os.path.join(output_dir, category)
        print(f"\n📁 {category}/ ({len(files)} 个文件, {format_size(cat_size)})")
        print(f"   目标: {target}")

        # 只显示前 5 个
        for f in files[:5]:
            print(f"   - {f['name']} ({format_size(f['size'])})")
        if len(files) > 5:
            print(f"   ... 还有 {len(files) - 5} 个文件")

    print(f"\n{'=' * 60}")
    print(f"  共 {total_files} 个文件, {format_size(total_size)}")
    print(f"{'=' * 60}")


def execute_organize(classified, output_dir, move=True):
    """执行归类操作"""
    action = "移动" if move else "复制"
    success = 0
    failed = 0

    for category, files in classified.items():
        target_dir = os.path.join(output_dir, category)
        os.makedirs(target_dir, exist_ok=True)

        for f in files:
            src = f['path']
            dst = os.path.join(target_dir, f['name'])

            # 处理同名文件
            if os.path.exists(dst):
                base, ext = os.path.splitext(f['name'])
                counter = 1
                while os.path.exists(dst):
                    dst = os.path.join(target_dir, f"{base}_{counter}{ext}")
                    counter += 1

            try:
                if move:
                    shutil.move(src, dst)
                else:
                    shutil.copy2(src, dst)
                print(f"  [{action}] {f['name']} -> {category}/")
                success += 1
            except (OSError, shutil.Error) as e:
                print(f"  [失败] {f['name']}: {e}")
                failed += 1

    print(f"\n完成: {success} 成功, {failed} 失败")


def main():
    parser = argparse.ArgumentParser(description='媒体文件自动归类工具')
    parser.add_argument('directory', help='要扫描的目录路径')
    parser.add_argument('--output', type=str, default=None,
                        help='输出目录（默认在扫描目录下创建分类文件夹）')
    parser.add_argument('--execute', action='store_true',
                        help='执行归类（默认只预览）')
    parser.add_argument('--copy', action='store_true',
                        help='复制而非移动文件')
    parser.add_argument('--min-size', type=int, default=0,
                        help='最小文件大小(MB)')

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"错误: 目录不存在 - {args.directory}")
        sys.exit(1)

    output_dir = args.output or args.directory

    print(f"\n扫描目录: {args.directory}")
    print(f"输出目录: {output_dir}")
    print(f"操作模式: {'执行' if args.execute else '预览'}")

    classified, skipped = scan_and_classify(args.directory, args.min_size)

    if not classified:
        print("\n没有找到需要归类的文件。")
        return

    preview_plan(classified, output_dir)

    if args.execute:
        print(f"\n即将{'复制' if args.copy else '移动'}文件到分类目录:")
        confirm = input("确认执行? (yes/no): ").strip().lower()
        if confirm == 'yes':
            execute_organize(classified, output_dir, move=not args.copy)
        else:
            print("已取消。")
    else:
        print(f"\n提示: 添加 --execute 参数执行归类操作")


if __name__ == '__main__':
    main()
