#!/usr/bin/env python3
"""
文件去重工具 - 扫描指定目录，按文件大小 + MD5 哈希查找重复文件

用法:
    # 扫描并输出报告（不删除）
    python dedup.py E:/Movies

    # 扫描并自动删除重复文件（保留每组第一个）
    python dedup.py E:/Movies --delete

    # 只扫描视频文件
    python dedup.py E:/Movies --video-only

    # 指定最小文件大小（默认 1MB，过滤小文件）
    python dedup.py E:/Movies --min-size 10

@author media-center
@version V1.0
@since 2026-05-22
"""

import os
import sys
import hashlib
import argparse
from collections import defaultdict
from datetime import datetime

VIDEO_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.ts',
    '.rmvb', '.rm', '.m4v', '.mpg', '.mpeg', '.webm', '.3gp', '.iso'
}

MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | {
    '.mp3', '.flac', '.wav', '.aac', '.ogg', '.wma',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.srt', '.ass', '.ssa', '.sub', '.nfo'
}


def md5_file(filepath, chunk_size=8192):
    """计算文件 MD5（只读前 10MB 加速大文件）"""
    h = hashlib.md5()
    read_limit = 10 * 1024 * 1024
    read_total = 0
    try:
        with open(filepath, 'rb') as f:
            while read_total < read_limit:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
                read_total += len(chunk)
    except (PermissionError, OSError) as e:
        print(f"  [跳过] 无法读取: {filepath} ({e})")
        return None
    return h.hexdigest()


def scan_files(directory, video_only=False, min_size_mb=1):
    """扫描目录下的所有文件"""
    min_size = min_size_mb * 1024 * 1024
    files = []
    for root, dirs, filenames in os.walk(directory):
        for name in filenames:
            filepath = os.path.join(root, name)
            ext = os.path.splitext(name)[1].lower()
            if video_only and ext not in VIDEO_EXTENSIONS:
                continue
            try:
                size = os.path.getsize(filepath)
                if size >= min_size:
                    files.append((filepath, size))
            except OSError:
                continue
    return files


def find_duplicates(files):
    """按 大小分组 → MD5 精确去重"""
    # 第一轮：按文件大小分组
    size_groups = defaultdict(list)
    for filepath, size in files:
        size_groups[size].append(filepath)

    # 只保留大小相同的组（可能是重复的）
    candidates = {size: paths for size, paths in size_groups.items() if len(paths) > 1}

    # 第二轮：对同大小文件计算 MD5
    duplicates = []
    total_candidates = sum(len(paths) for paths in candidates.values())
    checked = 0

    for size, paths in candidates.items():
        hash_groups = defaultdict(list)
        for path in paths:
            checked += 1
            print(f"\r  校验中... {checked}/{total_candidates}", end='', flush=True)
            file_hash = md5_file(path)
            if file_hash:
                hash_groups[file_hash].append(path)

        for file_hash, group in hash_groups.items():
            if len(group) > 1:
                duplicates.append({
                    'size': size,
                    'hash': file_hash,
                    'files': group
                })

    print()
    return duplicates


def format_size(size_bytes):
    """字节转人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def generate_report(duplicates, output_file=None):
    """生成去重报告"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"  文件去重报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 70)

    total_waste = 0
    total_dup_files = 0

    for i, dup in enumerate(duplicates, 1):
        waste = dup['size'] * (len(dup['files']) - 1)
        total_waste += waste
        total_dup_files += len(dup['files']) - 1

        lines.append(f"\n--- 重复组 #{i} | 文件大小: {format_size(dup['size'])} | 浪费: {format_size(waste)} ---")
        for j, f in enumerate(dup['files']):
            marker = "[保留]" if j == 0 else "[重复]"
            lines.append(f"  {marker} {f}")

    lines.append("\n" + "=" * 70)
    lines.append(f"  共发现 {len(duplicates)} 组重复，{total_dup_files} 个冗余文件")
    lines.append(f"  可回收空间: {format_size(total_waste)}")
    lines.append("=" * 70)

    report = "\n".join(lines)
    print(report)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存到: {output_file}")

    return total_waste, total_dup_files


def delete_duplicates(duplicates, dry_run=True):
    """删除重复文件（保留每组第一个）"""
    deleted_count = 0
    freed_space = 0

    for dup in duplicates:
        keep = dup['files'][0]
        for f in dup['files'][1:]:
            if dry_run:
                print(f"  [模拟删除] {f}")
            else:
                try:
                    os.remove(f)
                    print(f"  [已删除] {f}")
                    deleted_count += 1
                    freed_space += dup['size']
                except OSError as e:
                    print(f"  [失败] {f}: {e}")

    if not dry_run:
        print(f"\n已删除 {deleted_count} 个文件，回收 {format_size(freed_space)}")


def main():
    parser = argparse.ArgumentParser(description='文件去重工具 - 查找并清理重复文件')
    parser.add_argument('directory', help='要扫描的目录路径')
    parser.add_argument('--delete', action='store_true', help='自动删除重复文件（保留每组第一个）')
    parser.add_argument('--video-only', action='store_true', help='只扫描视频文件')
    parser.add_argument('--min-size', type=int, default=1, help='最小文件大小(MB)，默认 1MB')
    parser.add_argument('--report', type=str, default=None, help='报告输出文件路径')

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"错误: 目录不存在 - {args.directory}")
        sys.exit(1)

    print(f"\n扫描目录: {args.directory}")
    print(f"过滤条件: {'仅视频' if args.video_only else '所有文件'}, 最小 {args.min_size}MB")
    print()

    # 扫描
    print("正在扫描文件...")
    files = scan_files(args.directory, args.video_only, args.min_size)
    print(f"  找到 {len(files)} 个文件\n")

    if not files:
        print("没有符合条件的文件。")
        return

    # 查重
    print("正在计算哈希...")
    duplicates = find_duplicates(files)

    if not duplicates:
        print("\n没有发现重复文件。")
        return

    # 报告
    report_file = args.report or os.path.join(args.directory, f"dedup-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt")
    generate_report(duplicates, report_file)

    # 删除
    if args.delete:
        print("\n即将删除以下重复文件（每组保留第一个）:")
        confirm = input("确认删除? (yes/no): ").strip().lower()
        if confirm == 'yes':
            delete_duplicates(duplicates, dry_run=False)
        else:
            print("已取消。")
    else:
        print(f"\n提示: 添加 --delete 参数可自动删除重复文件")


if __name__ == '__main__':
    main()
