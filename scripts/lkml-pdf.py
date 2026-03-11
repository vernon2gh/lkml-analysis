#!/usr/bin/env python3
"""
将 Markdown 报告转换为 PDF。

Usage:
  python3 lkml-pdf.py <report.md>

依赖：npm install -g md-to-pdf --prefix ~/.local
"""
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_PATH   = os.path.join(SCRIPT_DIR, '..', 'assets', 'pdf_style.css')


def main():
    if len(sys.argv) < 2:
        print('Usage: lkml-pdf.py <report.md>', file=sys.stderr)
        sys.exit(1)

    md_file  = os.path.abspath(sys.argv[1])
    pdf_file = md_file.replace('.md', '.pdf')
    css_path = os.path.abspath(CSS_PATH)

    cmd = ['md-to-pdf', md_file, '--stylesheet', css_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    print(f'PDF saved to: {pdf_file}')


if __name__ == '__main__':
    main()
