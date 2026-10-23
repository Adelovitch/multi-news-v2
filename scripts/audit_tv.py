#!/usr/bin/env python3
"""Audit Multi News TV public directory metadata; no video playback or scraping."""
import collections, datetime, json, re, urllib.request
from pathlib import Path
from urllib.parse import urlparse

BASE="https://iptv-org.github.io/api/"
NEWS=re.compile(r"news|noticias|notícias|notizie|nachrichten|actualités|nouvelles|haber|nyheter|nieuws|новости|أخبار|france ?24|bfm|cnews|franceinfo|euronews|deutsche welle|bbc news|sky news|al jazeera|cnn|cnbc|bloomberg|africanews|africa ?24|lci|trt world|telesur|rtve 24h|abc news|fox news|nbc news|cbs news|nhk world|wion|ndtv|press tv|i24news|cgtn|channel newsasia|afp tv",re.I)
EXCLUDE=re.compile(r"sport|sports|weather|météo|music|musique|shopping|kids|junior|cinéma|cinema",re.I)
def get(name):
    req=urllib.request.Request(BASE+name+".json",headers={"User-Agent":"MultiNewsTV/1.2 (public catalogue audit)"})
    with urllib.request.urlopen(req,timeout=35) as f:return json.load(f)
def valid(u):
    try:
        p=urlparse(u or "")
        return p.scheme in ("https","http") and bool(p.netloc)
    except ValueError:return False
def main():
    channels,feeds,logos=(get(x) for x in ("channels","feeds","logos"))
    languages=collections.defaultdict(set)
    for f in feeds:
        if f.get("channel"):languages[f["channel"]].update(f.get("languages") or [])
    available_logos={x["channel"] for x in logos if x.get("in_use") and x.get("channel") and valid(x.get("url"))}
    selected=[x for x in channels if "news" in (x.get("categories") or []) and NEWS.search(x.get("name") or "") and not EXCLUDE.search(x.get("name") or "") and not x.get("is_nsfw") and not x.get("closed") and valid(x.get("website")) and x.get("country")]
    by_site=collections.defaultdict(list)
    for x in selected:
        u=urlparse(x["website"])
        by_site[(u.netloc.lower().removeprefix("www."),u.path.rstrip("/"))].append(x["name"])
    duplicates=[v for v in by_site.values() if len(v)>1]
    missing_languages=[x["name"] for x in selected if not languages[x["id"]]]
    missing_logos=[x["name"] for x in selected if x["id"] not in available_logos]
    non_https=[{"name":x["name"],"url":x["website"]} for x in selected if urlparse(x["website"]).scheme!="https"]
    count_countries=collections.Counter(x["country"] for x in selected)
    report={"timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"method":"IPTV-org catalogue metadata; no publisher authentication, playback, geolocation, or rights checks performed","catalogue_total":len(channels),"news_selected":len(selected),"countries":len(count_countries),"missing_language_count":len(missing_languages),"missing_logo_count":len(missing_logos),"duplicate_official_url_groups":duplicates[:80],"non_https_websites":non_https[:80],"missing_language_samples":missing_languages[:25],"missing_logo_samples":missing_logos[:25],"top_countries":count_countries.most_common(20),"manual_checks_required":["official site actually belongs to channel","live stream availability","free access versus free account versus paid subscription","geographical restrictions","official embedded-player permission"]}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/tv-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("TV AUDIT "+json.dumps({k:report[k] for k in ("catalogue_total","news_selected","countries","missing_language_count","missing_logo_count")},ensure_ascii=False))
    print("TV AUDIT duplicate official URLs: "+str(len(duplicates)))
    print("TV AUDIT result in reports/tv-audit.json (artifact); access/rights not verified")
if __name__=="__main__":main()
