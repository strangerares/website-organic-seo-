import csv
from datetime import datetime, timezone
from html import escape
from pathlib import Path


EXPORT_FIELDS = (
    "id", "keyword", "country", "language", "search_intent", "search_volume",
    "keyword_difficulty", "cpc", "competition", "source", "data_type",
    "date_retrieved", "related_keywords", "recommended_target_page",
    "opportunity_score", "long_tail", "topic_cluster", "ai_suggestion",
    "ai_reasoning", "missing_page", "article_opportunity",
)


def display_metric(row, field):
    value = row[field] if row[field] is not None else "Unavailable"
    return str(value).strip() or "Unavailable"


def export_keywords(database, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_FIELDS)
        writer.writeheader()
        for row in database.list_keywords():
            writer.writerow({field: (
                display_metric(row, field) if field in ("search_volume", "keyword_difficulty", "cpc", "competition") else row[field]
            ) for field in EXPORT_FIELDS})


def write_keyword_report(database, path: str):
    rows = database.list_keywords()
    intents = database.counts_by_intent()
    clusters = database.counts_by_cluster()

    def count_section(title, counts):
        items = "".join(f"<li><strong>{escape(str(key))}</strong>: {escape(str(value))}</li>" for key, value in sorted(counts.items()))
        return f"<section><h2>{escape(title)}</h2><ul>{items}</ul></section>"

    keyword_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            escape(str(row["keyword"])),
            escape(str(row["search_intent"] or "Informational")),
            escape(str(row["topic_cluster"] or "Unclustered")),
            escape(display_metric(row, "search_volume")),
            escape(display_metric(row, "keyword_difficulty")),
            escape(display_metric(row, "cpc")),
            escape(display_metric(row, "competition")),
            escape(str(row["recommended_target_page"] or "Unmapped")),
            escape(str(row["source"])),
            escape(str(row["data_type"])),
            escape(str(row["opportunity_score"]) if row["opportunity_score"] is not None else "Not scored"),
            "AI-generated" if row["ai_suggestion"] else "Not AI-generated",
            escape(str(row["ai_reasoning"] or "")),
        )
        for row in rows
    )

    missing = sorted(set(str(row["missing_page"]) for row in rows if row["missing_page"]))
    articles = sorted(set(str(row["article_opportunity"]) for row in rows if row["article_opportunity"]))

    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1"><title>Rio Organic SEO Keyword Research</title>
    <style>body{{font-family:system-ui,sans-serif;color:#18211d;margin:0;background:#f4f7f5}}main{{max-width:1200px;margin:auto;padding:24px}}section{{background:white;padding:16px;margin:16px 0}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{border:1px solid #dbe3df;padding:8px;text-align:left;vertical-align:top}}th{{background:#eaf0ec}}.metrics{{display:flex;gap:12px;flex-wrap:wrap}}.metric{{background:white;border-left:4px solid #2d7d57;padding:12px 16px}}</style></head><body><main>
    <h1>Keyword Research Report</h1><p>Generated {escape(datetime.now(timezone.utc).isoformat())}</p>
    <div class="metrics"><div class="metric"><strong>{len(rows)}</strong><br>Total keywords</div><div class="metric"><strong>{len([row for row in rows if row['ai_suggestion']])}</strong><br>AI suggestions</div><div class="metric"><strong>{len(missing)}</strong><br>Missing page recommendations</div></div>
    {count_section("Keywords by search intent", intents)}
    {count_section("Topic clusters", clusters)}
    <section><h2>Missing service pages</h2><ul>{''.join(f'<li>{escape(item)}</li>' for item in missing)}</ul></section>
    <section><h2>Article opportunities</h2><ul>{''.join(f'<li>{escape(item)}</li>' for item in articles)}</ul></section>
    <p>AI-generated suggestions are ideation, not verified demand. Unavailable metrics are not estimates.</p>
    <section><h2>Keywords</h2><table><thead><tr><th>Keyword</th><th>Intent</th><th>Cluster</th><th>Volume</th><th>Difficulty</th><th>CPC</th><th>Competition</th><th>Target page</th><th>Source</th><th>Data type</th><th>Opportunity score</th><th>AI provenance</th><th>AI reasoning</th></tr></thead><tbody>{keyword_rows}</tbody></table></section>
    </main></body></html>"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(html, encoding="utf-8")
