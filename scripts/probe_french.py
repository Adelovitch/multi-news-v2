"""Probe French RSS candidates from GitHub Actions before adding them to production."""
import urllib.request
from datetime import datetime,timezone
from scripts.collect import parse,is_recent
FEEDS=[
 ("Libération","https://www.liberation.fr/arc/outboundfeeds/rss-all/?outputType=xml"),
 ("20 Minutes","https://www.20minutes.fr/feeds/rss-une.xml"),
 ("Ouest-France","https://www.ouest-france.fr/rss-en-continu.xml"),
 ("Courrier international","https://www.courrierinternational.com/feed/all/rss.xml"),
 ("TV5MONDE","https://information.tv5monde.com/rss.xml"),
 ("Euronews","https://fr.euronews.com/rss?level=theme&name=news"),
 ("Les Échos","https://www.lesechos.fr/rss/rss_une.xml"),
 ("La Tribune","https://www.latribune.fr/rss/rubriques/economie.html"),
 ("Capital","https://www.capital.fr/rss"),
 ("Numerama","https://www.numerama.com/feed/"),
 ("Clubic","https://www.clubic.com/feed/news.rss"),
 ("01net","https://www.01net.com/feed/"),
 ("France Culture","https://www.radiofrance.fr/franceculture/rss"),
 ("Radio France","https://www.radiofrance.fr/franceinfo/rss"),
 ("Reporterre","https://reporterre.net/spip.php?page=backend"),
 ("Actu-Environnement","https://www.actu-environnement.com/flux/rss/actualites.xml"),
]
for name,url in FEEDS:
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"MultiNews/2.0 RSS aggregator"})
  with urllib.request.urlopen(req,timeout=9) as response: blob=response.read(2000000)
  articles=parse(blob,"fr",name)
  recent=[a for a in articles if is_recent(a,datetime.now(timezone.utc))]
  print(f"PROBE {name}: total={len(articles)} recent={len(recent)}")
 except Exception as exc:print(f"PROBE {name}: ERROR {str(exc)[:120]}")
