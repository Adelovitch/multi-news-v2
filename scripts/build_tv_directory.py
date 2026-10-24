#!/usr/bin/env python3
"""Generate a small public directory from IPTV-org metadata, with safe fallback."""
import collections
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

BASE = "https://iptv-org.github.io/api/"
NEWS = re.compile(r"news|noticias|notícias|notizie|nachrichten|actualités|nouvelles|haber|nyheter|nieuws|новости|أخبار|france ?24|bfm|cnews|franceinfo|euronews|deutsche welle|bbc news|sky news|al jazeera|cnn|cnbc|bloomberg|africanews|africa ?24|lci|trt world|telesur|rtve 24h|abc news|fox news|nbc news|cbs news|nhk world|wion|ndtv|press tv|i24news|cgtn|channel newsasia|afp tv", re.I)
EXCLUDE = re.compile(r"sport|sports|weather|météo|music|musique|shopping|kids|junior|cinéma|cinema", re.I)
TARGET = Path("data/tv-directory.json")

def safe(url):
    try:
        parsed = urlparse(url or "")
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except ValueError:
        return False

def fetch(name):
    req = urllib.request.Request(BASE + name + ".json", headers={"User-Agent": "MultiNewsTV/1.0 (directory metadata)"})
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.load(response)

def build(raw, feeds, logos):
    langs = collections.defaultdict(set)
    for item in feeds:
        if item.get("channel"):
            langs[item["channel"]].update(l for l in (item.get("languages") or []) if isinstance(l,str))
    logo_map = {}
    for item in logos:
        if item.get("in_use") and item.get("channel") and safe(item.get("url")):
            logo_map.setdefault(item["channel"], item["url"])
    result = []
    for x in raw:
        name=x.get("name") or ""
        if ("news" not in (x.get("categories") or []) or not NEWS.search(name) or EXCLUDE.search(name)
            or x.get("is_nsfw") or x.get("closed") or not safe(x.get("website")) or not x.get("country")):
            continue
        result.append({"name":name,"website":x["website"],"country":x["country"],
                       "logo":logo_map.get(x.get("id")),"languages":sorted(langs[x.get("id")])})
    return sorted(result, key=lambda x:x["name"].casefold())

def main():
    try:
        directory = build(fetch("channels"), fetch("feeds"), fetch("logos"))
        if len(directory)<100:
            raise ValueError(f"Unexpectedly sparse directory: {len(directory)}")
        TARGET.parent.mkdir(parents=True,exist_ok=True)
        TARGET.write_text(json.dumps(directory, ensure_ascii=False, separators=(",",":"))+"\n", encoding="utf-8")
        print(f"Directory refreshed: {len(directory)} channels, {TARGET.stat().st_size} bytes")
    except Exception as exc:
        if TARGET.exists():
            print(f"Warning: directory refresh failed; retaining prior snapshot: {exc}", file=sys.stderr)
        else:
            print(f"ERROR: no directory snapshot and refresh failed: {exc}", file=sys.stderr)
            raise

if __name__=="__main__":
    main()
