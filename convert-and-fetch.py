#!/usr/bin/env python3
# convert_and_fetch.py
import re
import urllib.request
from urllib.parse import urlparse
from datetime import datetime
import os

if not isinstance(UPSTREAM_URLS, list):
    raise SystemExit("UPSTREAM_URLS must be a list of URL strings")

UPSTREAM_URLS = [
[
    "https://cebeerre.github.io/dnsblocklists/webservices/4chan_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/500px_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/9gag_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/bluesky_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/facebook_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/linkedin_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/mail_ru_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/ok_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/pinterest_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/reddit_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/snapchat_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/tiktok_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/tinder_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/twitch_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/twitter_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/vk_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/whatsapp_asterisk.txt",
    "https://cebeerre.github.io/dnsblocklists/webservices/youtube_asterisk.txt"
]

]

WHITELIST_FILE = "whitelist.txt"   # optional, keep in repo to exclude domains
CHANGELOG_FILE = "changelog.txt"

def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "github-actions/convert-script"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def normalize_line(line):
    line = line.strip()
    if not line:
        return None
    if line.startswith(('#', '!', '//')):
        return None
    # remove scheme and path
    if '://' in line:
        try:
            parsed = urlparse(line)
            line = parsed.netloc or parsed.path
        except Exception:
            pass
    line = line.split('/')[0].strip()
    # remove port
    line = re.sub(r':\d+$', '', line)
    # remove leading wildcard/dot/www
    line = re.sub(r'^\*\.', '', line)
    line = re.sub(r'^\.', '', line)
    line = re.sub(r'^www\.', '', line, flags=re.I)
    # keep only domain-like tokens and require at least one dot
    if re.match(r'^[A-Za-z0-9.-]+$', line) and '.' in line:
        domain = line.lower().strip('.')
        return f'||{domain}^'
    return None

def load_whitelist(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return {l.strip().lower() for l in f if l.strip() and not l.startswith('#')}
    except FileNotFoundError:
        return set()

def safe_output_name(url):
    name = url.rstrip('/').split('/')[-1]
    if not name:
        name = "source.txt"
    # remove _asterisk suffix if present
    name = re.sub(r'_asterisk$', '', name)
    # ensure .txt extension
    if not name.lower().endswith('.txt'):
        name = name + '.txt'
    return name

def write_file(path, lines):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for l in lines:
            f.write(l + '\n')

def main():
    print(f"DEBUG: will fetch {len(UPSTREAM_URLS)} upstream URLs")
    whitelist = load_whitelist(WHITELIST_FILE)
    changelog = []
    total_written = 0
    for url in UPSTREAM_URLS:
        try:
            # ensure url is a single string
            if isinstance(url, (list, tuple)):
                raise ValueError("UPSTREAM_URLS contains a list/tuple element instead of a string")
            raw = fetch_url(url)
        except Exception as e:
            changelog.append(f"{datetime.utcnow().isoformat()}Z\tERROR\t{url}\t{e}")
            print(f"DEBUG: failed to fetch {url}: {e}")
            continue

        seen = set()
        converted = []
        for raw_line in raw.splitlines():
            out = normalize_line(raw_line)
            if not out:
                continue
            domain = out[2:-1]
            if domain in whitelist:
                continue
            if out not in seen:
                seen.add(out)
                converted.append(out)

        outname = safe_output_name(url)  # e.g., "facebook.txt"
        converted_sorted = sorted(converted)
        write_file(outname, converted_sorted)
        changelog.append(f"{datetime.utcnow().isoformat()}Z\tOK\t{url}\t{outname}\t{len(converted_sorted)}")
        print(f"DEBUG: wrote {len(converted_sorted)} entries to {outname}")
        total_written += len(converted_sorted)

    # final summary
    changelog.append(f"{datetime.utcnow().isoformat()}Z\tMASTER\tTOTAL_ENTRIES\t{total_written}")
    write_file(CHANGELOG_FILE, changelog)
    print("DEBUG: finished convert-and-fetch.py")
    print(f"Done. Wrote total {total_written} entries across sources.")

