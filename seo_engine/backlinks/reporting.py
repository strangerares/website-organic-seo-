import csv
from datetime import datetime, timezone
from html import escape
from pathlib import Path


EXPORT_FIELDS = (
    "id", "website_name", "domain", "page_url", "page_title", "meta_description",
    "language", "content_summary", "website_category", "opportunity_type",
    "contact_page_url", "public_email", "discovery_source", "date_discovered",
    "evaluation_score", "evaluation_reasoning", "outreach_angle",
    "suggested_target_page", "potential_concerns", "priority", "outreach_draft",
    "contact_status", "outreach_date", "follow_up_date", "response",
    "backlink_url", "link_status", "last_error", "analyzed_at",
)


def export_csv(database, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_FIELDS)
        writer.writeheader()
        for row in database.list_prospects():
            writer.writerow({field: row[field] for field in EXPORT_FIELDS})


def write_backlink_report(database, path: str):
    prospects = database.list_prospects()
    priorities = database.counts_by_priority()
    statuses = database.counts_by_status()
    categories = database.counts_by_category()
    acquired = [row for row in prospects if row["contact_status"] == "Link Acquired"]

    def table(rows):
        lines = ["<table><thead><tr><th>Score</th><th>Priority</th><th>Prospect</th><th>Category</th><th>Status</th><th>Page</th></tr></thead><tbody>"]
        for row in rows:
            lines.append("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><a href='{url}'>{url}</a></td></tr>".format(
                escape(str(row["evaluation_score"] or "-")),
                escape(str(row["priority"] or "Unscored")),
                escape(str(row["website_name"] or row["domain"])),
                escape(str(row["website_category"] or "Uncategorized")),
                escape(str(row["contact_status"])),
                url=escape(str(row["page_url"]), quote=True),
            ))
        lines.append("</tbody></table>")
        return "".join(lines)

    def count_table(title, counts):
        items = "".join(f"<li><strong>{escape(str(key))}</strong>: {escape(str(value))}</li>" for key, value in sorted(counts.items()))
        return f"<section><h2>{title}</h2><ul>{items}</ul></section>"

    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Rio Organic SEO Backlink Report</title>
    <style>body{{font-family:system-ui,sans-serif;color:#18211d;margin:0;background:#f4f7f5}}main{{max-width:1200px;margin:auto;padding:24px}}section{{background:white;padding:16px;margin:16px 0}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #dbe3df;padding:8px;text-align:left}}th{{background:#eaf0ec}}.metrics{{display:flex;gap:12px;flex-wrap:wrap}}.metric{{background:white;border-left:4px solid #2d7d57;padding:12px 16px}}</style></head><body><main>
    <h1>Backlink Opportunity Report</h1><p>Generated {escape(datetime.now(timezone.utc).isoformat())}</p>
    <div class='metrics'><div class='metric'><strong>{database.count()}</strong><br>Total prospects</div><div class='metric'><strong>{len(acquired)}</strong><br>Acquired backlinks</div></div>
    {count_table("Prospects by priority", priorities)}
    {count_table("Prospect categories", categories)}
    {count_table("Outreach status", statuses)}
    <section><h2>Best opportunities</h2>{table([row for row in prospects if row['evaluation_score'] is not None][:20])}</section>
    <section><h2>Acquired backlinks</h2>{table(acquired)}</section>
    </main></body></html>"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(html, encoding="utf-8")
