"""Command-line entry point for the Rio Organic SEO auditor."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from seo_engine.crawler.crawler import Crawler
from seo_engine.auditor.technical_audit import TechnicalAudit
from seo_engine.reporting.html_report import write_html_report
from seo_engine.reporting.json_report import write_json_report
from seo_engine.reporting.csv_report import write_csv_report
from seo_engine.utils.url_utils import validate_url


def build_parser():
    parser = argparse.ArgumentParser(description="Crawl a public website and generate a read-only technical SEO audit.")
    parser.add_argument("--url", required=True, help="Absolute website URL to audit")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum pages to crawl (default: 100)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between page requests (default: 1.0)")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout in seconds (default: 15.0)")
    parser.add_argument("--output", default="reports", help="Parent report directory (default: reports)")
    return parser


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0].startswith("keywords-"):
        from seo_engine.keywords.cli import run_keyword_command
        return run_keyword_command(argv)
    if argv and argv[0].startswith("backlinks-"):
        from seo_engine.backlinks.cli import run_backlink_command
        return run_backlink_command(argv)

    args = build_parser().parse_args(argv)
    if args.max_pages < 1:
        print("Error: --max-pages must be at least 1.", file=sys.stderr)
        return 2
    if args.delay < 0:
        print("Error: --delay cannot be negative.", file=sys.stderr)
        return 2
    if args.timeout <= 0:
        print("Error: --timeout must be greater than zero.", file=sys.stderr)
        return 2

    try:
        start_url = validate_url(args.url)
    except ValueError as exc:
        print(f"Error: invalid URL: {exc}", file=sys.stderr)
        return 2

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_host = start_url.split("//", 1)[1].split("/", 1)[0].replace(":", "-")
    report_dir = Path(args.output) / f"{timestamp}-{safe_host}"
    report_dir.mkdir(parents=True, exist_ok=True)

    print(f"Auditing {start_url} (maximum {args.max_pages} pages, {args.delay:.1f}s delay)...")
    crawler = Crawler(max_pages=args.max_pages, delay=args.delay, timeout=args.timeout)
    try:
        crawl = crawler.crawl(start_url)
    except Exception as exc:
        print(f"Error: crawl could not start: {exc}", file=sys.stderr)
        return 1

    audit = TechnicalAudit(session=crawler.session).audit(crawl)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": "Rio Organic SEO Auditor",
        "engine_version": "1.0.0",
        "start_url": start_url,
        "max_pages": args.max_pages,
        "delay_seconds": args.delay,
        "timeout_seconds": args.timeout,
    }
    result = {"audit_metadata": metadata, "crawl": crawl, "audit": audit}

    html_path = report_dir / "audit.html"
    json_path = report_dir / "audit.json"
    csv_path = report_dir / "pages.csv"
    write_html_report(result, str(html_path))
    write_json_report(result, str(json_path))
    write_csv_report(audit, str(csv_path))

    print("Audit complete.")
    print(f"Pages crawled: {len(crawl['pages'])}")
    print(f"Successful requests: {crawl['successful_requests']}")
    print(f"Failed requests: {crawl['failed_requests']}")
    print(f"Detected findings: {len(audit['issues'])}")
    print(f"Diagnostic health metric: {audit['health_score']}/100 (not a Google ranking score)")
    print(f"Reports: {report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
