import unittest
from datetime import datetime, timezone
from scripts.quality_audit import audit

NOW=datetime(2026,10,22,12,tzinfo=timezone.utc)

class QualityAuditTests(unittest.TestCase):
    def test_counts_language_media_and_missing_images(self):
        sample={"articles":[
          {"url":"https://example.org/1","title":"A","language":"fr","kind":"presse","source":"RFI","date":"2026-10-22T10:00:00+00:00","image":""},
          {"url":"https://example.org/2","title":"B","language":"en","kind":"magazine","source":"ScienceDaily","date":"2026-10-20T10:00:00+00:00","image":"https://example.org/p.jpg"}],
          "sources":[{"source":"RFI","ok":True},{"source":"ScienceDaily","ok":False}]}
        result=audit(sample,NOW)
        self.assertEqual(result["total_articles"],2)
        self.assertEqual(result["articles_by_kind"]["magazine"],1)
        self.assertEqual(result["missing_images"],1)
        self.assertIn("ScienceDaily",result["failed_sources"])
        self.assertEqual(result["issues"],[])
    def test_metadata_coverage_by_source_and_language(self):
        data={"articles":[
            {"url":"https://example.org/a","language":"fr","source":"RFI","image":"https://example.org/i.jpg","author":"Alice","categories":["Monde"]},
            {"url":"https://example.org/b","language":"fr","source":"RFI","image":"","author":"","categories":[]},
            {"url":"https://example.org/c","language":"en","source":"BBC","image":"","author":"Bob","categories":[]},
        ],"sources":[]}
        report=audit(data,NOW)["metadata_coverage"]
        self.assertEqual(report["all"]["image"],{"count":1,"percent":33.3})
        self.assertEqual(report["by_language"]["fr"]["author"],{"count":1,"percent":50.0})
        self.assertEqual(report["by_source"]["RFI"]["categories"],{"count":1,"percent":50.0})
        self.assertEqual(report["by_source"]["BBC"]["author"],{"count":1,"percent":100.0})

    def test_old_catalogue_warns_after_morning_window(self):
        data={"articles":[],"sources":[],"updated_at":"2026-10-21T04:00:00+00:00"}
        report=audit(data,datetime(2026,10,22,10,tzinfo=timezone.utc))
        self.assertTrue(any("not refreshed" in w for w in report["warnings"]))
        self.assertIn("No configured language has articles",report["issues"])

    def test_old_catalogue_does_not_warn_before_morning(self):
        data={"articles":[],"sources":[],"updated_at":"2026-10-21T04:00:00+00:00"}
        report=audit(data,datetime(2026,10,22,6,tzinfo=timezone.utc))
        self.assertFalse(any("not refreshed" in w for w in report["warnings"]))

    def test_duplicate_urls_are_detected(self):
        a={"url":"https://example.org/news?utm_source=rss","language":"fr","kind":"presse"}
        b={"url":"https://example.org/news","language":"fr","kind":"presse"}
        result=audit({"articles":[a,b],"sources":[]},NOW)
        self.assertEqual(result["duplicate_urls"],1)
        self.assertTrue(result["issues"])
    def test_invalid_url_detected(self):
        result=audit({"articles":[{"url":"javascript:alert(1)"}],"sources":[]},NOW)
        self.assertEqual(result["invalid_urls"],1)
        self.assertTrue(result["issues"])

if __name__=="__main__":
    unittest.main()
