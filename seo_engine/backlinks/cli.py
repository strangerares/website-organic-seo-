import argparse
import sys
from datetime import datetime, timezone

from seo_engine.backlinks.analyzer import ProspectAnalyzer
from seo_engine.backlinks.database import ProspectDatabase, STATUSES
from seo_engine.backlinks.discovery import generate_search_queries, import_csv, imported_prospect
from seo_engine.backlinks.evaluator import OpportunityEvaluator
from seo_engine.backlinks.outreach import OutreachGenerator
from seo_engine.backlinks.reporting import export_csv, write_backlink_report


def add_backlink_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--db", default="backlinks.db", help="SQLite database path (default: backlinks.db)")


def build_backlink_parser():
    parser = argparse.ArgumentParser(prog="main.py", description="Rio Organic SEO backlink opportunity tools")
    subparsers = parser.add_subparsers(dest="backlink_command", required=True)

    command = subparsers.add_parser("backlinks-import-csv", help="Import prospect URLs from CSV")
    command.add_argument("csv_path")
    add_backlink_arguments(command)

    command = subparsers.add_parser("backlinks-add", help="Manually add a prospect URL")
    command.add_argument("url")
    command.add_argument("--source", default="Manual URL")
    add_backlink_arguments(command)

    command = subparsers.add_parser("backlinks-analyze", help="Analyze and score prospects")
    command.add_argument("--id", type=int)
    command.add_argument("--delay", type=float, default=1.0)
    command.add_argument("--timeout", type=float, default=15.0)
    add_backlink_arguments(command)

    command = subparsers.add_parser("backlinks-outreach", help="Generate an outreach draft")
    command.add_argument("--id", type=int, required=True)
    command.add_argument("--angle", choices=("resource-page", "guest-article", "transportation", "partnership"), default="resource-page")
    add_backlink_arguments(command)

    command = subparsers.add_parser("backlinks-list", help="List prospects")
    command.add_argument("--status")
    command.add_argument("--limit", type=int)
    add_backlink_arguments(command)

    command = subparsers.add_parser("backlinks-export", help="Export prospects and evaluations to CSV")
    command.add_argument("--output", default="backlink-prospects.csv")
    add_backlink_arguments(command)

    command = subparsers.add_parser("backlinks-stats", help="Show backlink acquisition statistics")
    add_backlink_arguments(command)

    command = subparsers.add_parser("backlinks-report", help="Generate an HTML backlink report")
    command.add_argument("--output", default="reports/backlink-opportunities.html")
    add_backlink_arguments(command)

    command = subparsers.add_parser("backlinks-queries", help="Print relevant search queries")

    command = subparsers.add_parser("backlinks-status", help="Update a prospect workflow status")
    command.add_argument("id", type=int)
    command.add_argument("status", choices=STATUSES)
    add_backlink_arguments(command)

    return parser


def run_backlink_command(argv):
    args = build_backlink_parser().parse_args(argv)
    if args.backlink_command == "backlinks-queries":
        for query in generate_search_queries():
            print(query)
        return 0

    with ProspectDatabase(args.db) as database:
        if args.backlink_command == "backlinks-import-csv":
            try:
                prospects = import_csv(args.csv_path)
            except (OSError, csv_error()) as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 2
            imported = duplicates = invalid = 0
            for prospect in prospects:
                created, _ = database.add_prospect(prospect)
                if created:
                    imported += 1
                else:
                    duplicates += 1
            print(f"Imported: {imported}; duplicates skipped: {duplicates}; invalid or missing URLs skipped: {invalid}")
            return 0

        if args.backlink_command == "backlinks-add":
            try:
                prospect = imported_prospect(args.url, args.source)
            except ValueError as exc:
                print(f"Error: invalid URL: {exc}", file=sys.stderr)
                return 2
            created, prospect_id = database.add_prospect(prospect)
            if created:
                print(f"Added prospect ID {prospect_id}: {prospect['page_url']}")
            else:
                print(f"Prospect already exists: ID {prospect_id}: {prospect['page_url']}")
            return 0

        if args.backlink_command == "backlinks-analyze":
            rows = [database.get_prospect(args.id)] if args.id else database.list_prospects(status="New")
            analyzer = ProspectAnalyzer(delay=args.delay, timeout=args.timeout)
            evaluator = OpportunityEvaluator()
            analyzed = 0
            for row in rows:
                if row is None:
                    continue
                prospect = dict(row)
                result = analyzer.analyze(prospect)
                fields = {
                    "website_name": result.get("website_name"),
                    "domain": result.get("domain"),
                    "page_url": result.get("page_url"),
                    "page_title": result.get("page_title"),
                    "meta_description": result.get("meta_description"),
                    "language": result.get("language"),
                    "content_summary": result.get("content_summary"),
                    "website_category": result.get("website_category"),
                    "opportunity_type": result.get("opportunity_type"),
                    "contact_page_url": result.get("contact_page_url"),
                    "public_email": result.get("public_email"),
                    "last_error": result.get("last_error"),
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                }
                if result.get("last_error"):
                    database.update_prospect(row["id"], fields)
                    continue
                evaluation = evaluator.evaluate(result)
                fields.update({
                    "evaluation_score": evaluation["score"],
                    "evaluation_reasoning": evaluation["reasoning"],
                    "outreach_angle": evaluation["outreach_angle"],
                    "suggested_target_page": evaluation["suggested_target_page"],
                    "potential_concerns": evaluation["potential_concerns"],
                    "priority": evaluation["priority"],
                    "contact_status": "Qualified" if evaluation["score"] >= 50 else "Evaluated",
                })
                database.update_prospect(row["id"], fields)
                analyzed += 1
            print(f"Analyzed: {analyzed}; inaccessible or blocked entries retained with errors")
            return 0

        if args.backlink_command == "backlinks-outreach":
            row = database.get_prospect(args.id)
            if row is None:
                print(f"Error: prospect ID {args.id} not found", file=sys.stderr)
                return 2
            prospect = dict(row)
            evaluation = {
                "suggested_target_page": prospect.get("suggested_target_page") or "https://rioprivatedriver.com/",
            }
            draft = OutreachGenerator().generate(prospect, evaluation, args.angle)
            database.update_prospect(args.id, {"outreach_draft": draft, "contact_status": "Draft Ready"})
            print(draft)
            return 0

        if args.backlink_command == "backlinks-list":
            for row in database.list_prospects(status=args.status, limit=args.limit):
                print(" | ".join((
                    str(row["id"]), str(row["evaluation_score"] if row["evaluation_score"] is not None else "-"),
                    str(row["priority"] or "-"), str(row["contact_status"]),
                    str(row["domain"]), str(row["page_url"]),
                )))
            return 0

        if args.backlink_command == "backlinks-export":
            export_csv(database, args.output)
            print(f"Exported {database.count()} prospects to {args.output}")
            return 0

        if args.backlink_command == "backlinks-stats":
            print(f"Total prospects: {database.count()}")
            print("Priorities:", database.counts_by_priority())
            print("Statuses:", database.counts_by_status())
            print("Acquired backlinks:", len([row for row in database.list_prospects() if row["contact_status"] == "Link Acquired"]))
            return 0

        if args.backlink_command == "backlinks-report":
            write_backlink_report(database, args.output)
            print(f"Backlink report: {args.output}")
            return 0

        if args.backlink_command == "backlinks-status":
            row = database.get_prospect(args.id)
            if row is None:
                print(f"Error: prospect ID {args.id} not found", file=sys.stderr)
                return 2
            database.update_prospect(args.id, {"contact_status": args.status})
            print(f"Prospect {args.id} status: {args.status}")
            return 0


def csv_error():
    import csv
    return csv.Error
