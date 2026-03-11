#!/usr/bin/env python3
"""
读取并打印单封邮件的纯文本正文。

Usage:
  python3 lkml-read.py <filepath>
"""
import email
import sys


def main():
    if len(sys.argv) < 2:
        print('Usage: lkml-read.py <filepath>', file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], 'rb') as f:
        msg = email.message_from_binary_file(f)

    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                pl = part.get_payload(decode=True)
                if pl:
                    body = pl.decode('utf-8', errors='replace')
                    break
    else:
        pl = msg.get_payload(decode=True)
        if pl:
            body = pl.decode('utf-8', errors='replace')

    print(body)


if __name__ == '__main__':
    main()
