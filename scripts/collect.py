"""Collect public RSS headlines into a static JSON catalogue (standard library only)."""
import json
import re
import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "articles.json"
SOURCES = [
    ("fr","France 24","https://www.france24.com/fr/rss"),
    ("fr","RFI","https://www.rfi.fr/fr/rss"),
    ("en","BBC World","https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("en","The Guardian","https://www.theguardian.com/world/rss"),
    ("es","BBC Mundo","https://feeds.bbci.co.uk/mundo/rss.xml"),
    ("de","Deutsche Welle","https://rss.dw.com/rdf/rss-de-all"),
    ("ar","France 24 Arabic","https://www.france24.com/ar/rss"),
]
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
def parse(blob,lang,source):
    root=ET.fromstring(blob)
    items=root.findall(".//item")
    if not items:items=root.findall(".//{http://www.w3.org/2005/Atom}entry")
    articles=[]
    for entry in items[:50]:
        title=field(entry,"title","{http://www.w3.org/2005/Atom}title")
        url=field(entry,"link")
        if not url:
            for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
                if link.get("rel","alternate")=="alternate":url=link.get("href","");break
        u=urlparse(url)
        if not title or u.scheme not in ("http","https") or not u.netloc:continue
        image=""
        for item in entry.iter():
            if item.tag in ("{http://search.yahoo.com/mrss/}thumbnail","{http://search.yahoo.com/mrss/}content") and item.get("url"):
                image=item.get("url");break
            if item.tag=="enclosure" and item.get("type","").startswith("image/"):
                image=item.get("url","");break
        if image and urlparse(image).scheme not in ("http","https"):image=""
        articles.append(dict(title=title[:250],url=url,description=field(entry,"description","{http://www.w3.org/2005/Atom}summary")[:320],date=iso(field(entry,"pubDate","{http://www.w3.org/2005/Atom}updated","{http://purl.org/dc/elements/1.1/}date")),source=source,language=lang,image=image))
    return articles
def collect():
    articles=[];seen=set();status=[]
    for lang,source,url in SOURCES:
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"MultiNews/2.0 RSS aggregator"})
            with urllib.request.urlopen(req,timeout=15) as response:blob=response.read(2_000_000)
            found=parse(blob,lang,source)
            for article in found:
                key=article["url"].split("#")[0]
                if key not in seen:seen.add(key);articles.append(article)
            status.append({"source":source,"ok":True,"count":len(found)})
        except Exception as exc:
            status.append({"source":source,"ok":False,"error":str(exc)[:120]})
    articles.sort(key=lambda a:a["date"] or "",reverse=True)
    return {"updated_at":datetime.now(timezone.utc).isoformat(),"articles":articles[:350],"sources":status}
def main():
    result=collect()
    if not result["articles"]:raise SystemExit("No live RSS items collected; refusing to publish an empty feed.")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Articles:",len(result["articles"]),"Live sources:",sum(s["ok"] for s in result["sources"]))
if __name__=="__main__":main()
