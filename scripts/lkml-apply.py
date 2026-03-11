#!/usr/bin/env python3
"""
将 patch 系列应用到测试分支，供深度代码分析。

Usage:
  python3 lkml-apply.py <message-id> [--branch <name>]

  --branch   测试分支名（默认 analysis/mm-<YYYY-MM>）

内核源码树默认为当前目录（运行前请 cd 到内核源码树）。

依赖：pip install b4

Examples:
  python3 lkml-apply.py 20260302123456.12345-0-author@example.com
"""
import argparse
import datetime
import glob
import os
import subprocess
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _shared import load_config


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def main():
    parser = argparse.ArgumentParser(description='打入 patch 系列到测试分支')
    parser.add_argument('msgid', help='patch 系列封面的 Message-ID')
    parser.add_argument('--branch', help='测试分支名')
    args = parser.parse_args()

    linux_dir = os.getcwd()
    month  = datetime.date.today().strftime('%Y-%m')
    branch = args.branch or f'analysis/mm-{month}'

    print(f"linux_dir : {linux_dir}")
    print(f"branch    : {branch}")
    print(f"message-id: {args.msgid}")

    # 更新 mainline
    print("\n==> git fetch origin ...")
    run(['git', '-C', linux_dir, 'fetch', 'origin', '--quiet'])
    latest = subprocess.check_output(
        ['git', '-C', linux_dir, 'log', '--oneline', '-1', 'origin/master'], text=True
    ).strip()
    print(f"    latest: {latest}")

    # 创建测试分支
    print(f"\n==> 创建分支 '{branch}' ...")
    refs = subprocess.run(
        ['git', '-C', linux_dir, 'show-ref', '--quiet', f'refs/heads/{branch}']
    )
    if refs.returncode == 0:
        run(['git', '-C', linux_dir, 'branch', '-D', branch])
    run(['git', '-C', linux_dir, 'checkout', '-b', branch, 'origin/master', '--quiet'])

    # 用 b4 am 下载 mbox
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\n==> b4 am 下载 patch 系列 ...")
        run(['b4', 'am', '-o', tmpdir, args.msgid])

        mbx_files = glob.glob(os.path.join(tmpdir, '*.mbx'))
        if not mbx_files:
            print("    未找到 .mbx 文件，退出", file=sys.stderr)
            run(['git', '-C', linux_dir, 'checkout', 'master', '--quiet'])
            run(['git', '-C', linux_dir, 'branch', '-D', branch])
            sys.exit(1)

        mbx = mbx_files[0]
        print(f"    mbox: {os.path.basename(mbx)}")

        print(f"\n==> git am ...")
        run(['git', '-C', linux_dir, 'am', mbx])

    print("\n==> 已应用的 commits：")
    run(['git', '-C', linux_dir, 'log', '--oneline', 'origin/master..HEAD'])
    print(f"\n分析完成后清理：git checkout master && git branch -D '{branch}'")


if __name__ == '__main__':
    main()
