"""Probe candidate magazine RSS feeds; never publish unverified feeds automatically."""
import json
import urllib.request
from datetime import datetime, timezone
from scripts.collect import parse, is_recent

CANDIDATES = [
 ("fr","La Recherche","https://www.larecherche.fr/flux-rss.xml"),
 ("fr","La Chronique Spatiale","https://lachroniquespatiale.com/feed/"),
 ("fr","Journal du Geek – Espace","https://www.journaldugeek.com/category/espace/feed/"),
 ("fr","Sciences et Avenir","https://feeds.feedburner.com/sciencesetavenir/trJm3d6pPw4"),
 ("en","Quanta Magazine","https://api.quantamagazine.org/feed/"),
 ("en","Cosmos Magazine","https://cosmosmagazine.com/feed"),
 ("en","Science News","https://www.sciencenews.org/feed"),
 ("en","Popular Science","https://www.popsci.com/feed/"),
 ("es","Microsiervos","https://www.microsiervos.com/index.xml"),
 ("es","Xataka","https://www.xataka.com/index.xml"),
 ("es","Genbeta","https://www.genbeta.com/index.xml"),
 ("es","Applesfera","https://www.applesfera.com/index.xml"),
 ("es","Muy Interesante","https://muyinteresante.okdiario.com/feed"),
 ("de","Spektrum der Wissenschaft","https://www.spektrum.de/alias/rss/spektrum-de-rss-feed/996406"),
 ("de","bild der wissenschaft","https://www.wissenschaft.de/feed/"),
 ("de","Quarks","https://www.quarks.de/feed/"),
 ("de","GEO Natur","https://www.geo.de/feed/rss/natur/"),
 ("de","Heise Wissenschaft","https://www.heise.de/rss/heise-atom.xml"),
 ("ar","عالم التقنية","https://www.tech-wd.com/wd/feed/"),
 ("ar","البوابة العربية للأخبار التقنية","https://aitnews.com/feed/"),
 ("ar","عرب هاردوير","https://arabhardware.net/feed"),
 ("ar","أردرويد","https://ardroid.com/feed/"),
 ("ar","تقنية بلا حدود","https://www.unlimit-tech.com/feed/"),
 ("ar","تقني بلس","https://tiqnyplus.com/feed/"),
]

def main():
    results=[]
    for lang,name,url in CANDIDATES:
        row={"language":lang,"source":name,"url":url}
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"MultiNews/2.0 RSS aggregator","Accept":"application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"})
            with urllib.request.urlopen(req,timeout=8) as response:
                blob=response.read(2_000_000)
            found=parse(blob,lang,name)
            recent=sum(is_recent({**a,"kind":"magazine"},datetime.now(timezone.utc)) for a in found)
            row.update(ok=recent>0,items=len(found),recent=recent)
        except Exception as exc:
            row.update(ok=False,error=str(exc)[:110])
        results.append(row)
        print(json.dumps(row,ensure_ascii=False),flush=True)
    print("VALIDATED:",sum(x["ok"] for x in results),"/",len(results))

if __name__=="__main__":
    main()
