#!/usr/bin/env python3
"""
列出索引中的 patch 系列，可按 hint 过滤，可显示封面文件路径。

Usage:
  python3 lkml-list.py <subsystem> [--hint interesting|maybe|skip|all] [--files]

Examples:
  python3 lkml-list.py mm
  python3 lkml-list.py mm --hint interesting
  python3 lkml-list.py mm --hint interesting --files
  python3 lkml-list.py mm --hint maybe --files
"""
import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description='列出 patch 系列')
    parser.add_argument('subsystem')
    parser.add_argument(
        '--hint',
        choices=['interesting', 'maybe', 'skip', 'all'],
        default='all',
        help='按 hint 过滤（默认 all）',
    )
    parser.add_argument(
        '--files', action='store_true',
        help='显示每条系列的封面/单 patch 文件路径',
    )
    args = parser.parse_args()

    index_file = f'/tmp/{args.subsystem}_index.json'
    if not os.path.exists(index_file):
        print(
            f"索引文件不存在：{index_file}\n"
            f"请先运行：python3 lkml-index.py {args.subsystem}",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(index_file) as f:
        data = json.load(f)

    for s in data['series']:
        if args.hint != 'all' and s['hint'] != args.hint:
            continue

        file_keys = list(s['files'].keys())
        print(f"[{s['hint']}] {s['subject']} | files={file_keys}")

        if args.files:
            cover_key = '0' if '0' in s['files'] else '-1'
            label = 'cover' if cover_key == '0' else 'patch'
            print(f"  {label}: {s['files'][cover_key]}")


if __name__ == '__main__':
    main()
