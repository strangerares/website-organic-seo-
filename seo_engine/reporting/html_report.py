from html import escape
from pathlib import Path


def write_html_report(result: dict, path: str):
    crawl = result["crawl"]
    audit = result["audit"]
    issues = audit["issues"]

    issue_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            escape(str(item["severity"])), escape(item["code"]), escape(item["description"]),
            escape(item["affected_url"]), escape(item["why_it_matters"]), escape(item["recommendation"]),
        )
        for item in sorted(issues, key=lambda i: ["Critical", "High", "Medium", "Low", "Informational"].index(i["severity"]))
    )

    page_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            escape(page["url"]), page["status"], escape(page["title"]), page["title_length"],
            escape(page["meta_description"]), escape(" | ".join(page["h1"])), len(page["internal_links"]),
            len(page["external_links"]), sum(image["missing_alt"] for image in page["images"]),
        )
        for page in audit["pages"]
    )

    counts = {severity: sum(1 for item in issues if item["severity"] == severity) for severity in ["Critical", "High", "Medium", "Low", "Informational"]}
    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rio Organic SEO Audit</title><style>
body{{font-family:system-ui,sans-serif;color:#18211d;margin:0;background:#f4f7f5}}main{{max-width:1200px;margin:auto;padding:24px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{border:1px solid #dbe3df;padding:8px;text-align:left;vertical-align:top}}th{{background:#eaf0ec}}h1,h2{{color:#193c2d}}.summary{{display:flex;gap:12px;flex-wrap:wrap}}.metric{{background:white;border-left:4px solid #2d7d57;padding:12px 16px;min-width:140px}}.code{{font-family:ui-monospace,monospace}}
</style></head><body><main>
<h1>Rio Organic SEO Website Audit</h1><p>Target: <a href="{target}">{target}</a> &middot; Generated: {generated}</p>
<div class="summary"><div class="metric"><strong>{pages}</strong><br>Pages crawled</div><div class="metric"><strong>{success}</strong><br>Successful requests</div><div class="metric"><strong>{failed}</strong><br>Failed requests</div><div class="metric"><strong>{score}</strong><br>Diagnostic health metric</div></div>
<p>{score_explanation}</p>
<h2>Issue overview</h2><p>Critical: {critical} &middot; High: {high} &middot; Medium: {medium} &middot; Low: {low} &middot; Informational: {informational}</p>
<table><thead><tr><th>Severity</th><th>Code</th><th>Description</th><th>Affected URL</th><th>Why it matters</th><th>Recommendation</th></tr></thead><tbody>{issue_rows}</tbody></table>
<h2>Page-by-page findings</h2><table><thead><tr><th>URL</th><th>Status</th><th>Title</th><th>Title chars</th><th>Meta description</th><th>H1</th><th>Internal links</th><th>External links</th><th>Images missing ALT</th></tr></thead><tbody>{page_rows}</tbody></table>
<h2>Audit methodology</h2><p>Public HTML pages discovered from the seed URL, declared XML sitemaps, and same-domain links. No Google indexability conclusion is implied. robots.txt, HTTP responses, HTML elements, and in-domain image headers are measured observations.</p>
</main></body></html>""".format(
        target=escape(crawl["start_url"]), generated=escape(result["audit_metadata"]["generated_at"]), pages=len(crawl["pages"]),
        success=crawl["successful_requests"], failed=crawl["failed_requests"], score=audit["health_score"],
        score_explanation=escape(audit["health_score_explanation"]), critical=counts["Critical"], high=counts["High"],
        medium=counts["Medium"], low=counts["Low"], informational=counts["Informational"], issue_rows=issue_rows, page_rows=page_rows,
    )
    Path(path).write_text(html, encoding="utf-8")
