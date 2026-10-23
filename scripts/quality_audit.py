"""Quality report for the static Multi News catalogue. No network access required."""
import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlparse
from scripts.collect import canonical_url, SOURCES, MAGAZINES, is_recent

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"articles.json"
REPORT=ROOT/"reports"/"quality-report.json"

def audit(data, now=None):
    now=now or datetime.now(timezone.utc)
    articles=data.get("articles",[])
    sources=data.get("sources",[])
    problems=[]
    warnings=[]
    updated_at=data.get('updated_at')
    age_hours=None
    if updated_at:
        try:
            stamp=datetime.fromisoformat(updated_at)
            if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=timezone.utc)
            age_hours=round((now-stamp).total_seconds()/3600,1)
        except (ValueError,TypeError): warnings.append('Invalid catalogue update timestamp')
    else: warnings.append('Missing catalogue update timestamp')
    # Evaluate after the European morning collection window, not at midnight.
    paris=now.astimezone(ZoneInfo('Europe/Paris'))
    if paris.hour>=10 and age_hours is not None and age_hours>18:
        warnings.append(f'Catalogue not refreshed for {age_hours} hours')
    seen=set()
    languages=Counter()
    kinds=Counter()
    distribution=Counter()
    missing_dates=missing_images=duplicate_urls=invalid_urls=stale=0
    for a in articles:
        if not isinstance(a,dict):
            problems.append("Non-object article")
            continue
        url=a.get("url","")
        if not isinstance(url,str) or urlparse(url).scheme not in ("https","http") or not urlparse(url).netloc:
            invalid_urls+=1
            continue
        normalized=canonical_url(url)
        if normalized in seen:
            duplicate_urls+=1
        seen.add(normalized)
        if not a.get("date"):
            missing_dates+=1
        if not a.get("image"):
            missing_images+=1
        if not is_recent(a,now):
            stale+=1
        languages[a.get("language","?")]+=1
        kinds[a.get("kind","presse")]+=1
        distribution[a.get("source","?")]+=1
    failed=[s.get("source","?") for s in sources if isinstance(s,dict) and s.get("ok") is False]
    expected={lang for lang,_,_ in SOURCES}
    covered={lang for lang in expected if languages[lang]}
    if invalid_urls or duplicate_urls:
        problems.append("Invalid or duplicated URLs")
    if not covered:
        problems.append("No configured language has articles")
    result={
        "generated_at":now.isoformat(),
        "catalogue_updated_at":updated_at,
        "catalogue_age_hours":age_hours,
        "warnings":warnings,
        "total_articles":len(articles),
        "configured_sources":len(SOURCES),
        "source_status_records":len(sources),
        "failed_sources":failed,
        "articles_by_language":dict(sorted(languages.items())),
        "articles_by_kind":dict(sorted(kinds.items())),
        "articles_by_source":dict(sorted(distribution.items())),
        "missing_dates":missing_dates,
        "missing_images":missing_images,
        "duplicate_urls":duplicate_urls,
        "invalid_urls":invalid_urls,
        "stale_articles":stale,
        "languages_without_articles":sorted(expected-covered),
        "issues":problems,
    }
    return result

def main():
    data=json.loads(DATA.read_text(encoding="utf-8"))
    report=audit(data)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("MULTI NEWS QUALITY AUDIT")
    for field in ("total_articles","configured_sources","missing_dates","missing_images","duplicate_urls","invalid_urls","stale_articles"):
        print(f"{field}: {report[field]}")
    print("languages:",report["articles_by_language"])
    print("catalogue age (hours):",report["catalogue_age_hours"])
    print("freshness warnings:",report["warnings"])
    print("types:",report["articles_by_kind"])
    print("sources with errors:",report["failed_sources"])
    print("languages without articles:",report["languages_without_articles"])
    if report["issues"]:
        raise SystemExit("Quality gate failed: "+", ".join(report["issues"]))

if __name__=="__main__":
    main()
