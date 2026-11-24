import argparse
import sys

from .clustering import cluster_keyword
from .database import KeywordDatabase
from .discovery import import_keyword_csv, make_manual_keyword, seed_keywords
from .evaluator import KeywordEvaluator, ai_suggestion_record
from .mapper import map_keyword, recommend_article
from .reporting import export_keywords, write_keyword_report


def build_keyword_parser():
    parser = argparse.ArgumentParser(prog="main.py", description="Rio Organic SEO keyword research tools")
    subparsers = parser.add_subparsers(dest="keyword_command", required=True)

    command = subparsers.add_parser("keywords-import-csv", help="Import keyword metrics from CSV")
    command.add_argument("csv_path")
    command.add_argument("--source", default="CSV import")
    command.add_argument("--db", default="keywords.db")

    command = subparsers.add_parser("keywords-add", help="Manually add a seed or research keyword")
    command.add_argument("keyword")
    command.add_argument("--db", default="keywords.db")

    command = subparsers.add_parser("keywords-seeds", help="Add the built-in Rio keyword seeds")
    command.add_argument("--db", default="keywords.db")

    command = subparsers.add_parser("keywords-expand", help="AI-expand existing seed keywords")
    command.add_argument("--db", default="keywords.db")

    command = subparsers.add_parser("keywords-analyze", help="Classify, cluster, and map keywords")
    command.add_argument("--db", default="keywords.db")

    command = subparsers.add_parser("keywords-list", help="List keywords")
    command.add_argument("--intent")
    command.add_argument("--cluster")
    command.add_argument("--limit", type=int)
    command.add_argument("--db", default="keywords.db")

    command = subparsers.add_parser("keywords-export", help="Export keywords to CSV")
    command.add_argument("--output", default="keyword-research.csv")
    command.add_argument("--db", default="keywords.db")

    command = subparsers.add_parser("keywords-report", help="Generate an HTML keyword report")
    command.add_argument("--output", default="reports/keyword-research.html")
    command.add_argument("--db", default="keywords.db")

    return parser


def run_keyword_command(argv):
    args = build_keyword_parser().parse_args(argv)

    with KeywordDatabase(args.db) as database:
        if args.keyword_command == "keywords-import-csv":
            try:
                records = import_keyword_csv(args.csv_path, args.source)
            except (OSError, ValueError) as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 2
            imported = duplicates = 0
            for record in records:
                created, _ = database.add_keyword(record)
                imported += int(created)
                duplicates += int(not created)
            print(f"Imported: {imported}; duplicates skipped: {duplicates}")
            return 0

        if args.keyword_command in ("keywords-add", "keywords-seeds"):
            records = [make_manual_keyword(args.keyword)] if args.keyword_command == "keywords-add" else seed_keywords()
            added = duplicates = 0
            for record in records:
                created, _ = database.add_keyword(record)
                added += int(created)
                duplicates += int(not created)
            print(f"Added: {added}; duplicates skipped: {duplicates}")
            return 0

        if args.keyword_command == "keywords-expand":
            seeds = [row["keyword"] for row in database.list_keywords()]
            if not seeds:
                seeds = [record["keyword"] for record in seed_keywords()]
            suggestions = KeywordEvaluator().ai_expand(seeds)
            added = duplicates = 0
            for item in suggestions:
                record = ai_suggestion_record(item)
                if not record:
                    continue
                created, _ = database.add_keyword(record)
                added += int(created)
                duplicates += int(not created)
            print(f"AI suggestions added: {added}; duplicates skipped: {duplicates}; credentials unavailable or no response: {int(not suggestions)}")
            return 0

        if args.keyword_command == "keywords-analyze":
            evaluator = KeywordEvaluator()
            for row in database.list_keywords():
                record = evaluator.enrich(dict(row))
                cluster = cluster_keyword(record["keyword"])
                target, missing_page, _ = map_keyword(cluster, record["keyword"])
                article = recommend_article(cluster, record["keyword"])
                database.update_keyword(row["id"], {
                    "search_intent": record["search_intent"],
                    "opportunity_score": record["opportunity_score"],
                    "long_tail": record["long_tail"],
                    "topic_cluster": cluster,
                    "recommended_target_page": target,
                    "missing_page": missing_page,
                    "article_opportunity": article,
                    "related_keywords": record["related_keywords"],
                })
            print(f"Analyzed {database.count()} keywords")
            return 0

        if args.keyword_command == "keywords-list":
            rows = database.list_keywords(intent=args.intent, cluster=args.cluster)
            if args.limit:
                rows = rows[:args.limit]
            for row in rows:
                print(" | ".join((
                    str(row["id"]), row["keyword"], str(row["search_intent"] or "-"),
                    str(row["topic_cluster"] or "-"), str(row["recommended_target_page"] or "-"),
                    str(row["data_type"]),
                )))
            return 0

        if args.keyword_command == "keywords-export":
            export_keywords(database, args.output)
            print(f"Exported {database.count()} keywords to {args.output}")
            return 0

        if args.keyword_command == "keywords-report":
            write_keyword_report(database, args.output)
            print(f"Keyword report: {args.output}")
            return 0
