import unittest
from datetime import datetime, timezone, timedelta
from scripts.collect import parse, extract_image, canonical_url, iso, SOURCES, MAGAZINES

class CollectorTests(unittest.TestCase):
    def test_rss_author_and_categories(self):
        rss=b'<rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel><item><title>T</title><link>https://example.org/a</link><dc:creator>Marie Dupont</dc:creator><category>Science</category><category>Culture</category></item></channel></rss>'
        a=parse(rss,"fr","Test")[0]
        self.assertEqual(a["author"],"Marie Dupont")
        self.assertEqual(a["categories"],["Science","Culture"])
    def test_atom_author_and_category(self):
        feed=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>News</title><link href="https://example.org/1" /><author><name>Reporter</name></author><category term="Tech"/></entry></feed>'
        a=parse(feed,"en","Test")[0]
        self.assertEqual(a["author"],"Reporter")
        self.assertEqual(a["categories"],["Tech"])
    def test_missing_metadata_is_optional(self):
        rss=b'<rss><channel><item><title>News</title><link>https://example.org/x</link></item></channel></rss>'
        a=parse(rss,"fr","Test")[0]
        self.assertEqual(a["author"],"")
        self.assertEqual(a["categories"],[])
    def test_radio_source_classification(self):
        rss=b'<rss><channel><item><title>News</title><link>https://example.org/news</link></item></channel></rss>'
        a=parse(rss,"fr","Radio France")[0]
        self.assertEqual(a["kind"],"radio")
        self.assertEqual(a["audio_url"],"")
    def test_audio_enclosure_classification(self):
        rss=b'<rss><channel><item><title>Show</title><link>https://example.org/show</link><enclosure url="https://example.org/show.mp3" type="audio/mpeg"/></item></channel></rss>'
        a=parse(rss,"en","Example")[0]
        self.assertEqual(a["kind"],"radio")
        self.assertEqual(a["audio_url"],"https://example.org/show.mp3")
    def test_regular_source_stays_press(self):
        rss=b'<rss><channel><item><title>News</title><link>https://example.org/news</link></item></channel></rss>'
        self.assertEqual(parse(rss,"fr","RFI")[0]["kind"],"presse")
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
    def test_atom_image_enclosure(self):
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>T</title><link href="https://example.org/a"/><link rel="enclosure" type="image/jpeg" href="https://example.org/photo.jpg"/></entry></feed>'
        self.assertEqual(parse(atom,"en","Test")[0]["image"],"https://example.org/photo.jpg")
    def test_image_url_attribute(self):
        rss=b'<rss><channel><item><title>T</title><link>https://example.org/a</link><image url="https://example.org/photo.jpg"/></item></channel></rss>'
        self.assertEqual(parse(rss,"en","Test")[0]["image"],"https://example.org/photo.jpg")
    def test_magazine_type(self):
        rss=b'<rss><channel><item><title>T</title><link>https://example.org/x</link></item></channel></rss>'
        self.assertEqual(parse(rss,"fr","Futura Sciences")[0]["kind"],"magazine")
    def test_tracking_removed(self):
        self.assertEqual(canonical_url("https://EXAMPLE.org/a/?utm_source=rss&x=1#frag"),"https://example.org/a?x=1")
    def test_invalid_url_ignored(self):
        rss=b'<rss><channel><item><title>T</title><link>javascript:alert(1)</link></item></channel></rss>'
        self.assertEqual(parse(rss,"en","S"),[])
    def test_languages(self):
        self.assertEqual({s[0] for s in SOURCES},{"fr","en","es","de","ar","it","pt"})

    def test_new_languages_source_configuration(self):
        self.assertIn(("it","Il Fatto Quotidiano","https://www.ilfattoquotidiano.it/feed/"),SOURCES)
        self.assertIn(("pt","Observador","https://observador.pt/feed/"),SOURCES)
        self.assertIn("Geopop",MAGAZINES)
        self.assertIn(("pt","RTP Notícias","https://www.rtp.pt/noticias/rss/"),SOURCES)

    def test_added_french_sources(self):
        expected={"Libération","20 Minutes","Ouest-France","Courrier international",
                  "TV5MONDE","Euronews","Numerama","Clubic","01net",
                  "France Culture","Radio France","Reporterre"}
        names={name for lang,name,url in SOURCES if lang=="fr"}
        self.assertTrue(expected.issubset(names))
        self.assertEqual(len(names),len([1 for lang,_,_ in SOURCES if lang=="fr"]))

    def test_local_morning_slots(self):
        from scripts.collect import schedule_slot
        now=datetime(2026,10,22,6,15,tzinfo=timezone.utc)
        self.assertEqual(schedule_slot("BBC World","presse",now,{},[]),"2026-10-22:7")
        self.assertEqual(schedule_slot("France 24","presse",now,{},[]),"2026-10-22:8")
        self.assertEqual(schedule_slot("Al Jazeera English","presse",now,{},[]),"2026-10-22:8")
    def test_late_scheduled_run_catches_up(self):
        from scripts.collect import schedule_slot
        now=datetime(2026,10,22,15,15,tzinfo=timezone.utc)
        self.assertEqual(schedule_slot("BBC World","presse",now,{},[]),"2026-10-22:8")
        self.assertEqual(schedule_slot("ScienceDaily","magazine",now,{},[]),"2026-10-22:magazine")
    def test_no_duplicate_slot(self):
        from scripts.collect import schedule_slot
        now=datetime(2026,10,22,6,15,tzinfo=timezone.utc)
        self.assertIsNone(schedule_slot("BBC World","presse",now,{"last_slot":"2026-10-22:7"},[]))
    def test_magazine_frequency(self):
        from scripts.collect import magazine_interval
        self.assertEqual(magazine_interval("Sample",[]),7)
        data=[{"source":"Sample","date":f"2026-10-{d:02d}T12:00:00+00:00"} for d in (1,3,5,7)]
        self.assertEqual(magazine_interval("Sample",data),1)
    def test_magazine_slot(self):
        from scripts.collect import schedule_slot
        now=datetime(2026,10,22,7,15,tzinfo=timezone.utc)
        self.assertEqual(schedule_slot("ScienceDaily","magazine",now,{},[]),"2026-10-22:magazine")

if __name__ == "__main__":
    unittest.main()
