import unittest
from datetime import datetime, timezone, timedelta
from scripts.collect import parse, extract_image, canonical_url, iso, SOURCES, MAGAZINES

class CollectorTests(unittest.TestCase):
    def test_normal_rss(self):
        rss=b'<rss><channel><item><title>Example</title><link>https://example.org/a</link><pubDate>Thu, 22 Oct 2026 11:00:00 GMT</pubDate></item></channel></rss>'
        data=parse(rss,"fr","Sample")
        self.assertEqual(len(data),1)
        self.assertEqual(data[0]["title"],"Example")
        self.assertEqual(data[0]["kind"],"presse")
        self.assertTrue(data[0]["date"].startswith("2026-10-22"))
    def test_rdf(self):
        rss=b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/"><item><title>Test</title><link>https://example.org/b</link></item></rdf:RDF>'
        self.assertEqual(parse(rss,"de","DW")[0]["title"],"Test")
    def test_media_thumbnail(self):
        rss=b'<rss xmlns:media="http://search.yahoo.com/mrss/"><channel><item><title>T</title><link>https://example.org/x</link><media:thumbnail url="https://example.org/img.jpg"/></item></channel></rss>'
        self.assertEqual(parse(rss,"en","Test")[0]["image"],"https://example.org/img.jpg")
    def test_magazine_type(self):
        rss=b'<rss><channel><item><title>T</title><link>https://example.org/x</link></item></channel></rss>'
        self.assertEqual(parse(rss,"fr","Futura Sciences")[0]["kind"],"magazine")
    def test_tracking_removed(self):
        self.assertEqual(canonical_url("https://EXAMPLE.org/a/?utm_source=rss&x=1#frag"),"https://example.org/a?x=1")
    def test_invalid_url_ignored(self):
        rss=b'<rss><channel><item><title>T</title><link>javascript:alert(1)</link></item></channel></rss>'
        self.assertEqual(parse(rss,"en","S"),[])
    def test_languages(self):
        self.assertEqual({s[0] for s in SOURCES},{"fr","en","es","de","ar"})

if __name__ == "__main__":
    unittest.main()
