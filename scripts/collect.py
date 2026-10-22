"""Collect public RSS headlines into a static JSON catalogue (standard library only)."""
import json
import re
import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse, urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "articles.json"
SOURCES = [
    ("fr","France 24","https://www.france24.com/fr/rss"),
    ("fr","RFI","https://www.rfi.fr/fr/rss"),
    ("fr","Le Figaro","https://www.lefigaro.fr/rss/figaro_flash-actu.xml"),
    ("fr","Mediapart","https://www.mediapart.fr/articles/feed"),
    ("en","BBC World","https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("en","The Guardian","https://www.theguardian.com/world/rss"),
    ("en","Sky News","https://feeds.skynews.com/feeds/rss/world.xml"),
    ("en","Al Jazeera English","https://www.aljazeera.com/xml/rss/all.xml"),
    ("en","France 24 English","https://www.france24.com/en/rss"),
    ("es","BBC Mundo","https://feeds.bbci.co.uk/mundo/rss.xml"),
    ("es","El País","https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"),
    ("es","DW Español","https://rss.dw.com/rdf/rss-sp-top"),
    ("es","El Mundo","https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml"),
    ("de","Deutsche Welle","https://rss.dw.com/rdf/rss-de-all"),
    ("de","Tagesschau","https://www.tagesschau.de/xml/rss2/"),
    ("ar","France 24 Arabic","https://www.france24.com/ar/rss"),
    ("ar","DW Arabic","https://rss.dw.com/rdf/rss-ar-all"),
    ("fr","Futura Sciences","https://www.futura-sciences.com/rss/actualites.xml"),
    ("en","ScienceDaily","https://www.sciencedaily.com/rss/all.xml"),
    ("en","Smithsonian Magazine","https://www.smithsonianmag.com/rss/latest_articles/"),
]
MAGAZINES = {"Futura Sciences", "ScienceDaily", "Smithsonian Magazine"}
MAX_PER_SOURCE = 20
MAX_AGE_DAYS = 14

def clean(value):
    return html.unescape(re.sub(r"<[^>]*>","",value or "")).strip()
def iso(value):
    if not value:return None
    try:return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except (TypeError,ValueError,OverflowError):
        try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc).isoformat()
        except (TypeError,ValueError,OverflowError):return None
def field(entry,*names):
    for name in names:
        node=entry.find(name)
        if node is not None and node.text:return clean(node.text)
    return ""
def extract_image(entry):
    """Find images in RSS media fields, enclosures, or embedded article HTML."""
    candidates = []
    for node in entry.iter():
        local = node.tag.rsplit("}", 1)[-1].lower()
        namespace = node.tag.split("}")[0][1:] if "}" in node.tag else ""
        if local in ("thumbnail", "content") and namespace == "http://search.yahoo.com/mrss/":
            candidates.append(node.get("url", ""))
        elif local == "enclosure" and node.get("type", "").lower().startswith("image/"):
            candidates.append(node.get("url", ""))
        elif local == "image" and node.get("href"):
            candidates.append(node.get("href", ""))
    for node in entry.iter():
        local = node.tag.rsplit("}", 1)[-1].lower()
        if local not in ("description", "encoded", "summary", "content"):
            continue
        content = html.unescape(node.text or "")
        for match in re.finditer(r"<img\b[^>]*?\b(?:src|data-src)\s*=\s*['\"]([^'\"]+)['\"]", content, re.IGNORECASE):
            candidates.append(match.group(1))
    for candidate in candidates:
        url = html.unescape(candidate.strip())
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return url
    return ""


def parse(blob,lang,source):
    root=ET.fromstring(blob)
    items=root.findall(".//item") or root.findall(".//{http://purl.org/rss/1.0/}item")
    if not items:items=root.findall(".//{http://www.w3.org/2005/Atom}entry")
    articles=[]
    for entry in items[:50]:
        title=field(entry,"title","{http://purl.org/rss/1.0/}title","{http://www.w3.org/2005/Atom}title")
        url=field(entry,"link","{http://purl.org/rss/1.0/}link")
        if not url:
            for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
                if link.get("rel","alternate")=="alternate":url=link.get("href","");break
        u=urlparse(url)
        if not title or u.scheme not in ("http","https") or not u.netloc:continue
        image=extract_image(entry)
        articles.append(dict(title=title[:250],url=url,description=field(entry,"description","{http://purl.org/rss/1.0/}description","{http://www.w3.org/2005/Atom}summary")[:320],date=iso(field(entry,"pubDate","{http://www.w3.org/2005/Atom}updated","{http://purl.org/dc/elements/1.1/}date")),source=source,language=lang,image=image,kind=("magazine" if source in MAGAZINES else "presse")))
    return articles
def canonical_url(url):
    """Remove fragments and common tracking parameters for stable deduplication."""
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if not key.lower().startswith("utm_") and key.lower() not in
             {"fbclid", "gclid", "mc_cid", "mc_eid"}]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                       parts.path.rstrip("/") or "/", urlencode(query), ""))

def collect():
    articles=[];seen=set();status=[]
    cutoff=datetime.now(timezone.utc)-timedelta(days=MAX_AGE_DAYS)
    for lang,source,url in SOURCES:
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"MultiNews/2.0 RSS aggregator"})
            with urllib.request.urlopen(req,timeout=15) as response:blob=response.read(2_000_000)
            found=parse(blob,lang,source)
            valid=[]
            for article in found:
                if article["date"]:
                    try:
                        published=datetime.fromisoformat(article["date"])
                        if published < cutoff:
                            continue
                    except (TypeError,ValueError):
                        continue
                valid.append(article)
            valid.sort(key=lambda a:a["date"] or "", reverse=True)
            added=0
            for article in valid[:MAX_PER_SOURCE]:
                key=canonical_url(article["url"])
                if key not in seen:
                    seen.add(key)
                    articles.append(article)
                    added+=1
            status.append({"source":source,"kind":("magazine" if source in MAGAZINES else "presse"),"ok":bool(valid),"count":len(valid),"added":added})
        except Exception as exc:
            status.append({"source":source,"kind":("magazine" if source in MAGAZINES else "presse"),"ok":False,"error":str(exc)[:120]})
    articles.sort(key=lambda a:a["date"] or "",reverse=True)
    return {"updated_at":datetime.now(timezone.utc).isoformat(),"articles":articles[:400],"sources":status}
def main():
    result=collect()
    if not result["articles"]:raise SystemExit("No live RSS items collected; refusing to publish an empty feed.")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Articles:",len(result["articles"]),"Live sources:",sum(s["ok"] for s in result["sources"]))
if __name__=="__main__":main()
