"""Diagnose image metadata for selected RSS sources without storing article contents."""
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from scripts.collect import SOURCES,parse
TARGETS={"Libération","Euronews","Deutsche Welle","ScienceDaily"}
for lang,name,url in SOURCES:
 if name not in TARGETS: continue
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"MultiNews/2.0 RSS aggregator"})
  with urllib.request.urlopen(req,timeout=15) as res: blob=res.read(2_000_000)
  root=ET.fromstring(blob)
  entries=root.findall(".//item") or root.findall(".//{http://purl.org/rss/1.0/}item")
  if not entries: entries=root.findall(".//{http://www.w3.org/2005/Atom}entry")
  counts=Counter()
  for entry in entries[:20]:
   for node in entry.iter():
    key=node.tag.rsplit("}",1)[-1]
    if key in ("enclosure","image","thumbnail","content","description","encoded","link"):
     counts[f"{key}:url={bool(node.get('url'))}:href={bool(node.get('href'))}"]+=1
  parsed=parse(blob,lang,name)
  print(f"DIAG {name}: entries={len(entries)}, images={sum(bool(a['image']) for a in parsed)}, tags={dict(counts)}",flush=True)
 except Exception as exc:print(f"DIAG {name}: ERROR {type(exc).__name__}: {str(exc)[:100]}",flush=True)
