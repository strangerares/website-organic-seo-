import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from seo_engine.keywords.database import KeywordDatabase
from seo_engine.keywords.discovery import import_keyword_csv, make_manual_keyword, seed_keywords
from seo_engine.keywords.intent import classify_intent, is_long_tail
from seo_engine.keywords.clustering import cluster_keyword
from seo_engine.keywords.cli import run_keyword_command
from seo_engine.keywords.mapper import map_keyword, recommend_article
from seo_engine.keywords.evaluator import KeywordEvaluator, ai_suggestion_record
from seo_engine.keywords.reporting import export_keywords, write_keyword_report


class KeywordImportTests(unittest.TestCase):
    def test_manual_seed_and_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            db = KeywordDatabase(str(Path(directory) / "keywords.db"))
            record = make_manual_keyword("GIG airport private transfer")
            created, keyword_id = db.add_keyword(record)
            self.assertTrue(created)
            duplicate, duplicate_id = db.add_keyword(record)
            self.assertFalse(duplicate)
            self.assertEqual(keyword_id, duplicate_id)
            self.assertEqual(db.get_keyword(keyword_id)["search_volume"], "Unavailable")
            db.close()

    def test_csv_import_preserves_metric_source_and_unavailable_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keywords.csv"
            path.write_text(
                "keyword,search_volume,cpc,source,date_retrieved\nRio airport transfer,1200,2.50,Provider A,2026-11-24\n",
                encoding="utf-8",
            )
            records = import_keyword_csv(str(path), "CSV import")
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record["search_volume"], "1200")
            self.assertEqual(record["cpc"], "2.50")
            self.assertEqual(record["keyword_difficulty"], "Unavailable")
            self.assertEqual(record["source"], "Provider A")
            self.assertEqual(record["date_retrieved"], "2026-11-24")

    def test_seed_list_contains_requested_terms(self):
        seeds = seed_keywords()
        self.assertEqual(len(seeds), 10)
        self.assertIn("private driver rio de janeiro", {row["keyword"] for row in seeds})

    def test_seed_clusters_are_specific(self):
        from seo_engine.keywords.clustering import cluster_keyword
        self.assertEqual(cluster_keyword("private driver rio de janeiro"), "Private Drivers")
        self.assertEqual(cluster_keyword("rio de janeiro airport transfer"), "Airport Transfers")
        self.assertEqual(cluster_keyword("rio to cabo frio private transfer"), "Cabo Frio")
        self.assertEqual(cluster_keyword("Rio to BÚZIOS private transfer"), "Búzios")
        self.assertNotEqual(cluster_keyword("gigabyte private transfer"), "GIG Airport")


class KeywordClassificationTests(unittest.TestCase):
    def test_intent_long_tail_and_cluster(self):
        self.assertEqual(classify_intent("GIG airport private transfer"), "Transactional")
        self.assertEqual(classify_intent("Rio airport transfer guide"), "Informational")
        self.assertEqual(classify_intent("how to get from GIG airport"), "Informational")
        self.assertEqual(classify_intent("best private driver in Rio"), "Commercial")
        self.assertEqual(classify_intent("book a private driver in Rio"), "Transactional")
        self.assertTrue(is_long_tail("rio to arraial do cabo private transfer"))
        self.assertEqual(cluster_keyword("GIG airport private transfer"), "GIG Airport")

    def test_page_mapping_and_article_opportunity(self):
        cluster = cluster_keyword("Rio to Búzios private transfer")
        target, missing, _ = map_keyword(cluster, "Rio to Búzios private transfer")
        self.assertIn("buzios", target)
        self.assertIn("Búzios", missing)
        self.assertIn("Búzios", recommend_article(cluster, "Rio to Búzios private transfer"))

    def test_live_page_mapping_uses_relevant_crawled_page(self):
        pages = [
            {
                "url": "https://rioprivatedriver.com/",
                "final_url": "https://rioprivatedriver.com/",
                "status": 200,
                "headers": {"Content-Type": "text/html"},
                "html": "<html><head><title>Rio Private Driver</title></head><body><h1>Private Driver in Rio</h1></body></html>",
            },
            {
                "url": "https://rioprivatedriver.com/airport-transfers/",
                "final_url": "https://rioprivatedriver.com/airport-transfers/",
                "status": 200,
                "headers": {"Content-Type": "text/html"},
                "html": "<html><head><title>Rio Airport Transfers</title><link rel='canonical' href='/airport-transfers/'></head><body><h1>Rio de Janeiro Airport Transfer Service</h1></body></html>",
            },
        ]

        target, missing, _ = map_keyword(
            "Airport Transfers",
            "Rio de Janeiro airport transfer",
            crawled_pages=pages,
        )

        self.assertEqual(target, "https://rioprivatedriver.com/airport-transfers")
        self.assertEqual(missing, "")

    def test_live_page_mapping_skips_noindex_and_error_pages(self):
        pages = [
            {
                "url": "https://rioprivatedriver.com/gig-airport-transfer/",
                "final_url": "https://rioprivatedriver.com/gig-airport-transfer/",
                "status": 200,
                "headers": {"Content-Type": "text/html"},
                "html": "<html><head><title>GIG Airport Transfer</title><meta name='robots' content='noindex'></head><body><h1>GIG Airport Transfer</h1></body></html>",
            },
            {
                "url": "https://rioprivatedriver.com/gig-airport-transfer-old/",
                "final_url": "https://rioprivatedriver.com/gig-airport-transfer-old/",
                "status": 404,
                "headers": {"Content-Type": "text/html"},
                "html": "<html><head><title>GIG Airport Transfer</title></head><body><h1>GIG Airport Transfer</h1></body></html>",
            },
        ]

        target, missing, _ = map_keyword(
            "GIG Airport",
            "GIG airport private transfer",
            crawled_pages=pages,
        )

        self.assertEqual(target, "https://rioprivatedriver.com/gig-airport-transfer/")
        self.assertEqual(missing, "Create GIG airport transfer landing page")

    def test_keywords_analyze_can_map_against_crawler_results(self):
        page = {
            "url": "https://rioprivatedriver.com/airport-transfers/",
            "final_url": "https://rioprivatedriver.com/airport-transfers/",
            "status": 200,
            "headers": {"Content-Type": "text/html"},
            "html": "<html><head><title>Rio Airport Transfer</title></head><body><h1>Rio de Janeiro Airport Transfer</h1></body></html>",
        }
        with tempfile.TemporaryDirectory() as directory:
            db_path = str(Path(directory) / "keywords.db")
            with KeywordDatabase(db_path) as database:
                database.add_keyword(make_manual_keyword("Rio de Janeiro airport transfer"))

            with patch("seo_engine.keywords.cli.Crawler") as crawler:
                crawler.return_value.crawl.return_value = {"pages": [page]}
                self.assertEqual(run_keyword_command([
                    "keywords-analyze",
                    "--db", db_path,
                    "--crawl",
                ]), 0)
                crawler.assert_called_once_with(max_pages=50, delay=1.0, timeout=15.0)
                crawler.return_value.crawl.assert_called_once_with("https://rioprivatedriver.com/")

            with KeywordDatabase(db_path) as database:
                record = database.get_by_text("Rio de Janeiro airport transfer")
                self.assertEqual(
                    record["recommended_target_page"],
                    "https://rioprivatedriver.com/airport-transfers/",
                )
                self.assertFalse(record["missing_page"])


class KeywordEvaluationAndReportingTests(unittest.TestCase):
    def test_ai_expansion_uses_openai_environment_settings(self):
        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": '{"keywords": []}'}}]}

        class Session:
            def post(self, url, **kwargs):
                self.request = (url, kwargs)
                return Response()

        session = Session()
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_API_MODEL": "test-model",
        }, clear=True):
            self.assertEqual(KeywordEvaluator(session).ai_expand(["seed"]), [])

        _, request = session.request
        self.assertEqual(request["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(request["json"]["model"], "test-model")

    def test_ai_suggestion_has_unavailable_metrics_and_source(self):
        record = ai_suggestion_record({
            "keyword": "Rio airport pickup for cruise passengers",
            "search_intent": "transactional",
            "long_tail": True,
            "cluster": "Airport Transfers",
            "recommended_target_page": "https://rioprivatedriver.com/our-services/",
            "reasoning": "Relevant visitor need",
        })
        self.assertEqual(record["data_type"], "AI-generated suggestion")
        self.assertEqual(record["search_volume"], "Unavailable")
        self.assertEqual(record["keyword_difficulty"], "Unavailable")
        self.assertTrue(record["ai_suggestion"])

    def test_export_and_html_report(self):
        with tempfile.TemporaryDirectory() as directory:
            db = KeywordDatabase(str(Path(directory) / "keywords.db"))
            record = make_manual_keyword("Rio airport transfer")
            record.update({"search_intent": "Transactional", "topic_cluster": "Airport Transfers", "recommended_target_page": "https://rioprivatedriver.com/our-services/"})
            db.add_keyword(record)
            db.add_keyword(ai_suggestion_record({
                "keyword": "Rio airport pickup for cruise passengers",
                "search_intent": "Transactional",
                "cluster": "Airport Transfers",
                "reasoning": "Relevant visitor need",
            }))
            csv_path = Path(directory) / "keywords.csv"
            html_path = Path(directory) / "keywords.html"
            export_keywords(db, str(csv_path))
            write_keyword_report(db, str(html_path))
            self.assertGreater(csv_path.stat().st_size, 0)
            self.assertIn("Unavailable", csv_path.read_text(encoding="utf-8"))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Keyword Research Report", html)
            self.assertIn("AI provenance", html)
            self.assertIn("AI-generated", html)
            self.assertIn("Not scored", html)
            self.assertIn("AI-generated suggestions are ideation", html)
            db.close()


class EnvironmentLoadingTests(unittest.TestCase):
    def test_cli_loads_project_env_without_overriding_process_environment(self):
        with patch("main.load_dotenv") as load_dotenv:
            with self.assertRaises(SystemExit):
                main.main(["--help"])

        load_dotenv.assert_called_once_with(
            Path(main.__file__).resolve().parent / ".env",
            override=False,
        )


if __name__ == "__main__":
    unittest.main()
