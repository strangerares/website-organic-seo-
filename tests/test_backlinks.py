import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from seo_engine.backlinks.analyzer import ProspectAnalyzer, classify_category
from seo_engine.backlinks.database import ProspectDatabase
from seo_engine.backlinks.discovery import import_csv, imported_prospect
from seo_engine.backlinks.evaluator import OpportunityEvaluator
from seo_engine.backlinks.outreach import OutreachGenerator
from seo_engine.backlinks.reporting import export_csv, write_backlink_report
from seo_engine.utils.url_utils import validate_url


class FakeResponse:
    def __init__(self, url, status=200, text=""):
        self.url = url
        self.status_code = status
        self.text = text


class BacklinkDatabaseTests(unittest.TestCase):
    def test_database_add_duplicate_and_status(self):
        with tempfile.TemporaryDirectory() as directory:
            db = ProspectDatabase(str(Path(directory) / "backlinks.db"))
            prospect = {
                "domain": "example.com",
                "page_url": "https://example.com/rio-guide",
                "date_discovered": "2026-11-24T00:00:00Z",
                "discovery_source": "CSV import",
            }
            created, prospect_id = db.add_prospect(prospect)
            self.assertTrue(created)
            duplicate, duplicate_id = db.add_prospect(prospect)
            self.assertFalse(duplicate)
            self.assertEqual(prospect_id, duplicate_id)
            db.update_prospect(prospect_id, {"contact_status": "Evaluated", "evaluation_score": 82})
            self.assertEqual(db.get_prospect(prospect_id)["contact_status"], "Evaluated")
            db.close()


class DiscoveryTests(unittest.TestCase):
    def test_csv_import_and_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prospects.csv"
            path.write_text("Website Name,Page URL,Discovery Source\nRio Guide,https://example.com/rio,CSV\nOther,not-a-url,CSV\n", encoding="utf-8")
            prospects = import_csv(str(path))
            self.assertEqual(len(prospects), 1)
            self.assertEqual(prospects[0]["domain"], "example.com")

    def test_manual_invalid_url(self):
        with self.assertRaises(ValueError):
            imported_prospect("example.com/no-scheme")


class AnalysisAndScoringTests(unittest.TestCase):
    def test_category_and_evaluation_scoring(self):
        prospect = {
            "page_title": "Rio de Janeiro Travel Guide",
            "meta_description": "An English guide for USA and Canada visitors",
            "content_summary": "Brazil travel tips, hotels, airport transfer and private tours",
            "website_category": "Travel Blog / Tourism Resource",
            "opportunity_type": "Resource-page recommendation",
        }
        evaluation = OpportunityEvaluator().evaluate(prospect)
        self.assertGreaterEqual(evaluation["score"], 75)
        self.assertIn(evaluation["priority"], ("High", "Medium", "Low"))
        self.assertIn("rioprivatedriver.com", evaluation["suggested_target_page"])
        self.assertEqual(classify_category("Rio de Janeiro Brazil travel guide"), "Travel Blog / Tourism Resource")

    def test_ai_evaluation_uses_openai_environment_settings(self):
        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": '{"score": 70}'}}]}

        class Session:
            def post(self, url, **kwargs):
                self.request = (url, kwargs)
                return Response()

        session = Session()
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_API_MODEL": "test-model",
        }, clear=True):
            result = OpportunityEvaluator(session)._evaluate_with_ai({})

        self.assertEqual(result["score"], 70)
        _, request = session.request
        self.assertEqual(request["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(request["json"]["model"], "test-model")

    def test_inaccessible_response_is_recorded(self):
        class Session:
            def get(self, url, **kwargs):
                if url.endswith("/robots.txt"):
                    return FakeResponse(url, text="User-agent: *\nAllow: /")
                return FakeResponse(url, status=404, text="")

        prospect = {"page_url": "https://example.com/missing", "domain": "example.com"}
        result = ProspectAnalyzer(delay=0, session=Session()).analyze(prospect)
        self.assertEqual(result["last_error"], "HTTP 404")


class OutreachExportTests(unittest.TestCase):
    def test_outreach_generation_and_csv_export(self):
        prospect = {
            "website_name": "Rio Guide",
            "domain": "example.com",
            "page_url": "https://example.com/rio",
            "page_title": "Rio travel guide",
        }
        evaluation = {"suggested_target_page": "https://rioprivatedriver.com/"}
        draft = OutreachGenerator().generate(prospect, evaluation, "transportation")
        self.assertIn("Rio Private Driver", draft)
        self.assertIn("https://example.com/rio", draft)

        with tempfile.TemporaryDirectory() as directory:
            db = ProspectDatabase(str(Path(directory) / "backlinks.db"))
            data = dict(prospect)
            data.update({"date_discovered": "2026-11-24T00:00:00Z", "discovery_source": "Test"})
            created, prospect_id = db.add_prospect(data)
            self.assertTrue(created)
            db.update_prospect(prospect_id, {"outreach_draft": draft, "evaluation_score": 80})
            csv_path = Path(directory) / "export.csv"
            export_csv(db, str(csv_path))
            self.assertTrue(csv_path.exists())
            self.assertGreater(csv_path.stat().st_size, 0)
            report_path = Path(directory) / "report.html"
            write_backlink_report(db, str(report_path))
            self.assertIn("Backlink Opportunity Report", report_path.read_text(encoding="utf-8"))
            db.close()


if __name__ == "__main__":
    unittest.main()
