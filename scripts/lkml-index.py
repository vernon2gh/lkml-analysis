#!/usr/bin/env python3
"""
建立子系统 patch 系列索引，保存到 /tmp/<subsystem>_index.json。

Usage:
  python3 lkml-index.py <subsystem> [--days N] [--maildir <path>]

Output:
  /tmp/<subsystem>_index.json
  打印：总数 + hint 分布（interesting / maybe / skip）

Examples:
  python3 lkml-index.py mm --days 30
  python3 lkml-index.py mm-stable --maildir ~/Mail/lei/mm-stable --days 30
"""
import argparse
import email
import email.header
import email.utils
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _shared import load_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_mail_base():
    return load_config()['mail_base_dir']


def decode_subject(raw):
    parts = email.header.decode_header(raw or '')
    result = ''
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or 'utf-8', errors='replace')
        else:
            result += str(part)
    return result


def normalize_title(subj):
    s = re.sub(r'\[.*?\]\s*', '', subj).strip()
    s = re.sub(r'^Re:\s*', '', s, flags=re.I).strip()
    return s[:120]


def get_seq(subj):
    m = re.search(r'\[.*?(\d+)/(\d+).*?\]', subj)
    if m:
        return int(m.group(1)), int(m.group(2))
    return -1, -1


def get_ver(subj):
    m = re.search(r'\[.*?v(\d+).*?\]', subj, re.I)
    return int(m.group(1)) if m else 1


def is_noise_subject(subj):
    if re.search(r'\bRe:\b', subj, re.I):
        return True
    if re.search(r'\b(FAILED|stable|akpm-mm|linux-next|htmldoc|sparse|kbuild)\b', subj, re.I):
        return True
    if re.search(r'\b(typo|maintainer|mailmap|spdx|grammar|spelling|MAINTAINERS)\b', subj):
        return True
    return False


def hint_from_subject(subj):
    s = subj.lower()
    skip_patterns = [
        r'\bcleanup\b', r'\bclean[ -]up\b', r'\bclean up\b',
        r'\brefactor\b', r'\brefactoring\b',
        r'\brename\b', r'\bmove\b.*\bto\b',
        r'\bwhitespace\b', r'\bindentation\b', r'\bformatting\b',
        r'\bcomment\b', r'\bdoc\b', r'\bdocument',
        r'\bkconfig\b', r'\bspdx\b',
        r'\bno.functional.change\b', r'\bnfc\b',
        r'\bcosmetic\b', r'\btrivial\b',
        r'\bspelling\b', r'\bgrammar\b',
        r'\bsimplif', r'\bdedup\b',
    ]
    for pat in skip_patterns:
        if re.search(pat, s):
            return 'skip'

    interesting_patterns = [
        r'\badd\b', r'\bnew\b', r'\bintroduce\b', r'\bimplement\b',
        r'\bsupport\b', r'\benable\b', r'\ballow\b',
        r'\boptimiz', r'\bperformance\b', r'\bspeedup\b', r'\bfaster\b',
        r'\breduce\b', r'\bavoid\b', r'\bimprove\b',
        r'\bfix\b.*\bcorrupt', r'\bfix\b.*\bcras', r'\bfix\b.*\boom\b',
        r'\bfix\b.*\bleak\b', r'\bfix\b.*\brace\b',
        r'\bmechanism\b', r'\bpolicy\b', r'\balgorithm\b',
        r'\bsyscall\b', r'\binterface\b', r'\bapi\b',
        r'\bmmap\b', r'\bhugetlb\b', r'\bthp\b', r'\bfolio\b',
        r'\bmglru\b', r'\bzswap\b', r'\bmemcg\b', r'\bnuma\b',
        r'\bswap\b', r'\bcompaction\b', r'\bmigrat',
    ]
    for pat in interesting_patterns:
        if re.search(pat, s):
            return 'interesting'

    return 'maybe'


def read_email_body(fpath):
    with open(fpath, 'rb') as f:
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
    return body


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------

def build_index(maildir, days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    subdirs = [os.path.join(maildir, d) for d in ('cur', 'new')]

    candidates = []
    nack_candidates = []

    for d in subdirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            fpath = os.path.join(d, fname)
            try:
                with open(fpath, 'rb') as f:
                    msg = email.message_from_binary_file(f)
                date_raw = msg.get('Date', '')
                dt = email.utils.parsedate_to_datetime(date_raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt = dt.astimezone(timezone.utc)
                if dt < cutoff:
                    continue

                subj = decode_subject(msg.get('Subject', ''))

                if re.search(r'\bRe:\b', subj, re.I):
                    nack_candidates.append((fpath, subj, dt))
                    continue

                if not re.search(r'^\s*\[.*(PATCH|RFC).*\]', subj, re.I):
                    continue

                candidates.append((fpath, subj, dt, get_ver(subj)))
            except Exception:
                pass

    msgid_map = {}
    cover_list = []

    for fpath, subj, dt, ver in candidates:
        if is_noise_subject(subj):
            continue
        try:
            with open(fpath, 'rb') as f:
                msg = email.message_from_binary_file(f)
            msgid = (msg.get('Message-ID') or '').strip().strip('<>')
            in_reply_to = (msg.get('In-Reply-To') or '').strip().strip('<>')
            references = [r.strip('<>') for r in (msg.get('References') or '').split()]
        except Exception:
            msgid, in_reply_to, references = '', '', []

        cur, total = get_seq(subj)
        if msgid:
            msgid_map[msgid] = (fpath, subj, dt, ver, cur, total, in_reply_to, references)
        if cur == 0 or cur == -1:
            cover_list.append((msgid, fpath, subj, dt, ver, cur, total))

    children_map = {}
    for mid, info in msgid_map.items():
        fpath, subj, dt, ver, cur, total, in_reply_to, references = info
        parent = in_reply_to or (references[-1] if references else '')
        if parent:
            children_map.setdefault(parent, []).append(mid)

    series_map = {}
    for cover_msgid, cover_fpath, cover_subj, cover_dt, cover_ver, cover_cur, cover_total in cover_list:
        norm = normalize_title(cover_subj)

        if norm in series_map:
            existing = series_map[norm]
            ex_ver = existing.get('_ver', 1)
            if cover_ver <= ex_ver:
                existing.setdefault('prev_covers', []).append(
                    {'ver': cover_ver, 'file': cover_fpath, 'date': cover_dt.strftime('%m-%d')}
                )
                continue
            prev = {'ver': ex_ver, 'file': existing.get('cover_fpath', ''),
                    'date': existing['cover_dt'].strftime('%m-%d') if existing.get('cover_dt') else ''}
            prev_covers = existing.get('prev_covers', []) + [prev]
            series_map[norm] = {'_ver': cover_ver, 'prev_covers': prev_covers}
        else:
            series_map[norm] = {'_ver': cover_ver, 'prev_covers': []}

        entry = series_map[norm]
        entry.update(cover_msgid=cover_msgid, cover_fpath=cover_fpath,
                     cover_subj=cover_subj, cover_dt=cover_dt)

        seq_key = 0 if cover_cur == 0 else -1
        entry['seqs'] = {seq_key: cover_fpath}

        for child_mid in children_map.get(cover_msgid, []):
            if child_mid not in msgid_map:
                continue
            cfpath, csubj, cdt, cver, ccur, ctotal, _, _ = msgid_map[child_mid]
            if ccur > 0:
                entry['seqs'][ccur] = cfpath

    series_list = []
    for norm, entry in series_map.items():
        seqs = entry.get('seqs', {})
        cover_fpath = entry.get('cover_fpath')
        cover_subj  = entry.get('cover_subj', norm)
        cover_dt    = entry.get('cover_dt')
        if not cover_fpath or not cover_dt:
            continue

        files = {str(k): v for k, v in sorted(seqs.items(), key=lambda x: int(x[0]))}
        numbered = [k for k in seqs if k > 0]
        total_patches = max(numbered) if numbered else 1

        author_raw = ''
        try:
            with open(cover_fpath, 'rb') as f:
                msg = email.message_from_binary_file(f)
            author_raw = msg.get('From', '')
        except Exception:
            pass

        ver_m = re.search(r'\[.*?v(\d+).*?\]', cover_subj, re.I)
        version   = f"v{ver_m.group(1)}" if ver_m else 'v1'
        is_rfc    = bool(re.search(r'\bRFC\b', cover_subj, re.I))
        status    = f"{'RFC ' if is_rfc else ''}PATCH {version}（{total_patches} 个 patch）"
        author_clean = re.sub(r'\s*<[^>]+>', '', author_raw).strip().strip('"')
        prev_covers  = sorted(entry.get('prev_covers', []), key=lambda x: x['date'], reverse=True)

        series_list.append({
            'date':          cover_dt.strftime('%m-%d'),
            'title':         norm,
            'subject':       cover_subj,
            'author':        author_clean,
            'author_full':   author_raw,
            'status':        status,
            'total_patches': total_patches,
            'hint':          hint_from_subject(cover_subj),
            'files':         files,
            'prev_covers':   prev_covers,
        })

    series_list.sort(key=lambda x: x['date'], reverse=True)

    # NACK detection
    nacks = {}
    for fpath, subj, dt in nack_candidates:
        try:
            body = read_email_body(fpath)
        except Exception:
            continue
        if not re.search(r'\bNACK\b|\bNAK\b', body, re.I):
            continue
        norm = normalize_title(subj)
        nack_line = next(
            (line.strip() for line in body.splitlines()
             if re.search(r'\bNACK\b|\bNAK\b', line, re.I) and not line.startswith('>')),
            ''
        )
        try:
            with open(fpath, 'rb') as f:
                msg = email.message_from_binary_file(f)
            author = msg.get('From', '')
        except Exception:
            author = ''
        nacks.setdefault(norm, []).append({'author': author, 'text': nack_line[:150]})

    return {'cutoff_days': days, 'total': len(series_list), 'nacks': nacks, 'series': series_list}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='建立 patch 系列轻量索引')
    parser.add_argument('subsystem')
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--maildir', help='直接指定 maildir 路径（自定义子系统时使用）')
    args = parser.parse_args()

    if args.maildir:
        maildir = os.path.expanduser(args.maildir)
    else:
        maildir = os.path.join(load_mail_base(), args.subsystem)

    index_file = f'/tmp/{args.subsystem}_index.json'

    data = build_index(maildir, args.days)

    with open(index_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    hints = {'interesting': 0, 'maybe': 0, 'skip': 0}
    for s in data['series']:
        hints[s.get('hint', 'skip')] += 1

    print(f"索引已保存：{index_file}")
    print(
        f"共 {data['total']} 条系列  |  "
        f"interesting={hints['interesting']}  "
        f"maybe={hints['maybe']}  "
        f"skip={hints['skip']}"
    )


if __name__ == '__main__':
    main()
