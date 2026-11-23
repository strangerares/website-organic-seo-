import csv
from pathlib import Path


def write_csv_report(audit: dict, path: str):
    fieldnames = ["url", "status", "title", "title_length", "meta_description", "description_length", "h1", "h2", "h3", "canonical", "meta_robots", "noindex", "nofollow", "https", "language", "viewport", "internal_link_count", "external_link_count", "missing_alt_image_count", "issue_count"]
    issues_by_url = {}
    for item in audit["issues"]:
        for url in str(item["affected_url"]).split(", "):
            issues_by_url[url] = issues_by_url.get(url, 0) + 1

    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for page in audit["pages"]:
            row = {
                "url": page["url"], "status": page["status"], "title": page["title"], "title_length": page["title_length"],
                "meta_description": page["meta_description"], "description_length": page["description_length"],
                "h1": " | ".join(page["h1"]), "h2": " | ".join(page["h2"]), "h3": " | ".join(page["h3"]),
                "canonical": page["canonical"], "meta_robots": page["meta_robots"], "noindex": page["noindex"],
                "nofollow": page["nofollow"], "https": page["https"], "language": page["language"],
                "viewport": page["viewport"], "internal_link_count": len(page["internal_links"]),
                "external_link_count": len(page["external_links"]),
                "missing_alt_image_count": sum(image["missing_alt"] for image in page["images"]),
                "issue_count": issues_by_url.get(page["url"], 0),
            }
            writer.writerow(row)
