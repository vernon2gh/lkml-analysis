#!/usr/bin/env python3
"""
Stage-1: Lightweight index of linux-mm patch series.

For each patch series within the time window, records:
  - date, title, author, total_patches
  - files: {seq: filepath}  -- absolute paths to the actual .eml files

No diff content is extracted here. The analysis step reads files on demand.

Usage:
  python3 extract_patches.py [--days 30] [--maildir ~/Mail/lei/mm]
  > /tmp/mm_index.json

Then to read a specific series during analysis:
  python3 extract_patches.py --read <filepath>
  --> prints the email body (cover letter body + diffs)
"""

import os
import sys
import json
import email
import email.header
import email.utils
import re
import argparse
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def decode_subject(raw):
    parts = email.header.decode_header(raw or "")
    result = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or 'utf-8', errors='replace')
        else:
            result += str(part)
    return result


def normalize_title(subj):
    """Strip [PATCH ...] prefix to get a stable series key."""
    s = re.sub(r'\[.*?\]\s*', '', subj).strip()
    s = re.sub(r'^Re:\s*', '', s, flags=re.I).strip()
    return s[:120]


def get_seq(subj):
    """Return (current, total) or (-1,-1) for single patch."""
    m = re.search(r'\[.*?(\d+)/(\d+).*?\]', subj)
    if m:
        return int(m.group(1)), int(m.group(2))
    return -1, -1


def get_ver(subj):
    m = re.search(r'\[.*?v(\d+).*?\]', subj, re.I)
    return int(m.group(1)) if m else 1


def is_noise_subject(subj):
    """Quick subject-only filter. Returns True if this series should be skipped entirely."""
    if re.search(r'\bRe:\b', subj, re.I):
        return True
    if re.search(r'\b(FAILED|stable|akpm-mm|linux-next|htmldoc|sparse|kbuild)\b', subj, re.I):
        return True
    if re.search(r'\b(typo|maintainer|mailmap|spdx|grammar|spelling|MAINTAINERS)\b', subj):
        return True
    return False


def hint_from_subject(subj):
    """
    Quick subject-based classification hint for the analysis agent.
    Returns one of:
      'skip'       -- almost certainly not worth analyzing (cleanup, trivial refactor, doc)
      'maybe'      -- unclear from subject alone, agent should skim cover letter
      'interesting'-- likely a new feature, optimization, or important fix
    """
    s = subj.lower()

    # Patterns that strongly suggest low-value content
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
        r'\bsimplif',       # simplify, simplification
        r'\bdedup\b',
    ]
    for pat in skip_patterns:
        if re.search(pat, s):
            return 'skip'

    # Patterns that strongly suggest interesting content
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
    """Read and return full text body of an email file."""
    with open(fpath, 'rb') as f:
        msg = email.message_from_binary_file(f)
    body = ""
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
# --read mode: print a single email's body
# ---------------------------------------------------------------------------

def cmd_read(fpath):
    print(read_email_body(fpath))


# ---------------------------------------------------------------------------
# Main index-building mode
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--maildir', default=os.path.expanduser('~/Mail/lei/mm'))
    parser.add_argument('--read', metavar='FILE',
                        help='Print body of a single email file and exit')
    args = parser.parse_args()

    if args.read:
        cmd_read(os.path.expanduser(args.read))
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    maildir = os.path.expanduser(args.maildir)
    subdirs = [os.path.join(maildir, d) for d in ('cur', 'new')]

    # --- Phase 1: scan all files, parse Date + Subject only ---
    candidates = []  # (fpath, subj, dt, ver)
    nack_candidates = []  # (fpath, subj, dt)

    for d in subdirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            fpath = os.path.join(d, fname)
            try:
                with open(fpath, 'rb') as f:
                    # Only parse headers to be fast
                    msg = email.message_from_binary_file(f)
                date_raw = msg.get("Date", "")
                dt = email.utils.parsedate_to_datetime(date_raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt = dt.astimezone(timezone.utc)
                if dt < cutoff:
                    continue

                subj_raw = msg.get("Subject", "")
                subj = decode_subject(subj_raw)

                # Track Re: for NACK detection
                if re.search(r'\bRe:\b', subj, re.I):
                    nack_candidates.append((fpath, subj, dt))
                    continue

                # Must be a PATCH or RFC PATCH
                if not re.search(r'^\s*\[.*(PATCH|RFC).*\]', subj, re.I):
                    continue

                candidates.append((fpath, subj, dt, get_ver(subj)))

            except Exception:
                pass

    # --- Phase 2: build Message-ID → file mapping & threading ---
    # First pass: index all PATCH emails by Message-ID
    msgid_map = {}  # message_id -> (fpath, subj, dt, ver, cur, total)
    cover_list = []  # covers/single patches

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

    # Second pass: for each cover, collect its child patches via threading
    # series_map: cover_msgid -> {seq: (fpath, subj, dt, ver)}
    series_map = {}

    # Build reverse index: parent_msgid -> [child_msgid]
    children_map = {}  # parent -> [child]
    for mid, info in msgid_map.items():
        fpath, subj, dt, ver, cur, total, in_reply_to, references = info
        parent = in_reply_to or (references[-1] if references else '')
        if parent:
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(mid)

    for cover_msgid, cover_fpath, cover_subj, cover_dt, cover_ver, cover_cur, cover_total in cover_list:
        norm = normalize_title(cover_subj)

        if norm in series_map:
            existing = series_map[norm]
            ex_ver = existing.get('_ver', 1)
            if cover_ver <= ex_ver:
                # 版本号更小或相同，降级到 prev_covers
                existing.setdefault('prev_covers', []).append({
                    'ver': cover_ver, 'file': cover_fpath, 'date': cover_dt.strftime('%m-%d')
                })
                continue
            # 版本号更大，替换主版本，旧主版本降级
            prev = {'ver': ex_ver,
                    'file': existing.get('cover_fpath', ''),
                    'date': existing['cover_dt'].strftime('%m-%d') if existing.get('cover_dt') else ''}
            prev_covers = existing.get('prev_covers', []) + [prev]
            series_map[norm] = {'_ver': cover_ver, 'prev_covers': prev_covers}
        else:
            series_map[norm] = {'_ver': cover_ver, 'prev_covers': []}

        entry = series_map[norm]
        entry['cover_msgid'] = cover_msgid
        entry['cover_fpath'] = cover_fpath
        entry['cover_subj'] = cover_subj
        entry['cover_dt'] = cover_dt

        seq_key = 0 if cover_cur == 0 else -1
        entry['seqs'] = {seq_key: cover_fpath}

        # Collect direct children (patches 1/N, 2/N, ...)
        for child_mid in children_map.get(cover_msgid, []):
            if child_mid not in msgid_map:
                continue
            cfpath, csubj, cdt, cver, ccur, ctotal, _, _ = msgid_map[child_mid]
            if ccur > 0:
                entry['seqs'][ccur] = cfpath

    # --- Phase 3: build output records ---
    series_list = []

    for norm, entry in series_map.items():
        seqs = entry.get('seqs', {})
        cover_fpath = entry.get('cover_fpath')
        cover_subj = entry.get('cover_subj', norm)
        cover_dt = entry.get('cover_dt')

        if not cover_fpath or not cover_dt:
            continue

        # Build file map: seq -> filepath, sorted numerically
        files = {str(k): v for k, v in sorted(seqs.items(), key=lambda x: int(x[0]))}

        # Determine total patches (max numbered seq)
        numbered = [k for k in seqs if k > 0]
        total_patches = max(numbered) if numbered else 1

        author_raw = ""
        try:
            with open(cover_fpath, 'rb') as f:
                msg = email.message_from_binary_file(f)
            author_raw = msg.get("From", "")
        except Exception:
            pass

        # Parse version and RFC flag from subject
        ver_m = re.search(r'\[.*?v(\d+).*?\]', cover_subj, re.I)
        version = f"v{ver_m.group(1)}" if ver_m else "v1"
        is_rfc = bool(re.search(r'\bRFC\b', cover_subj, re.I))
        status = f"{'RFC ' if is_rfc else ''}PATCH {version}（{total_patches} 个 patch）"

        # Clean author: "Name <email>" -> "Name"
        author_clean = re.sub(r'\s*<[^>]+>', '', author_raw).strip().strip('"')

        # prev_covers: 旧版本封面列表，按日期降序排列（最近的旧版在前）
        prev_covers = sorted(entry.get('prev_covers', []),
                             key=lambda x: x['date'], reverse=True)

        series_list.append({
            'date': cover_dt.strftime('%m-%d'),
            'title': norm,
            'subject': cover_subj,
            'author': author_clean,
            'author_full': author_raw,
            'status': status,
            'total_patches': total_patches,
            'hint': hint_from_subject(cover_subj),
            'files': files,               # 最新版本的所有 patch 文件
            'prev_covers': prev_covers,   # 旧版本封面：[{'ver': N, 'file': path}, ...]
        })

    series_list.sort(key=lambda x: x['date'], reverse=True)

    # --- Phase 4: detect NACKs (scan Re: email bodies) ---
    nacks = {}
    for fpath, subj, dt in nack_candidates:
        try:
            body = read_email_body(fpath)
        except Exception:
            continue
        if not re.search(r'\bNACK\b|\bNAK\b', body, re.I):
            continue
        norm = normalize_title(subj)
        nack_line = ""
        for line in body.splitlines():
            if re.search(r'\bNACK\b|\bNAK\b', line, re.I) and not line.startswith('>'):
                nack_line = line.strip()
                break
        if norm not in nacks:
            nacks[norm] = []
        try:
            with open(fpath, 'rb') as f:
                msg = email.message_from_binary_file(f)
            author = msg.get("From", "")
        except Exception:
            author = ""
        nacks[norm].append({'author': author, 'text': nack_line[:150]})

    output = {
        'cutoff_days': args.days,
        'total': len(series_list),
        'nacks': nacks,
        'series': series_list,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
