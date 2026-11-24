import sqlite3
from pathlib import Path
from typing import Optional


STATUSES = (
    "New", "Evaluated", "Qualified", "Draft Ready", "Contacted",
    "Replied", "Link Acquired", "Rejected",
)


class ProspectDatabase:
    def __init__(self, path: str = "backlinks.db"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.initialize()

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def initialize(self):
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_name TEXT,
            domain TEXT NOT NULL,
            page_url TEXT NOT NULL UNIQUE,
            page_title TEXT,
            meta_description TEXT,
            language TEXT,
            content_summary TEXT,
            website_category TEXT,
            opportunity_type TEXT,
            contact_page_url TEXT,
            public_email TEXT,
            discovery_source TEXT,
            date_discovered TEXT NOT NULL,
            evaluation_score INTEGER,
            evaluation_reasoning TEXT,
            outreach_angle TEXT,
            suggested_target_page TEXT,
            potential_concerns TEXT,
            priority TEXT,
            outreach_draft TEXT,
            contact_status TEXT NOT NULL DEFAULT 'New',
            outreach_date TEXT,
            follow_up_date TEXT,
            response TEXT,
            backlink_url TEXT,
            link_status TEXT,
            last_error TEXT,
            analyzed_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_prospect_status ON prospects(contact_status);
        CREATE INDEX IF NOT EXISTS idx_prospect_score ON prospects(evaluation_score);
        """)
        self.connection.commit()

    def add_prospect(self, data: dict) -> tuple[bool, int]:
        fields = (
            "website_name", "domain", "page_url", "page_title", "meta_description",
            "language", "content_summary", "website_category", "opportunity_type",
            "contact_page_url", "public_email", "discovery_source", "date_discovered",
            "last_error",
        )
        values = {field: data.get(field) for field in fields}
        existing = self.connection.execute(
            "SELECT id FROM prospects WHERE page_url = ?", (values["page_url"],)
        ).fetchone()
        if existing:
            return False, existing["id"]
        placeholders = ", ".join("?" for _ in fields)
        columns = ", ".join(fields)
        cursor = self.connection.execute(
            f"INSERT INTO prospects ({columns}) VALUES ({placeholders})",
            tuple(values[field] for field in fields),
        )
        self.connection.commit()
        return True, cursor.lastrowid

    def get_prospect(self, prospect_id: int) -> Optional[sqlite3.Row]:
        return self.connection.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,)).fetchone()

    def get_prospect_by_url(self, page_url: str) -> Optional[sqlite3.Row]:
        return self.connection.execute("SELECT * FROM prospects WHERE page_url = ?", (page_url,)).fetchone()

    def list_prospects(self, status: Optional[str] = None, limit: Optional[int] = None) -> list[sqlite3.Row]:
        sql = "SELECT * FROM prospects"
        params = []
        if status:
            sql += " WHERE contact_status = ?"
            params.append(status)
        sql += " ORDER BY CASE WHEN evaluation_score IS NULL THEN 1 ELSE 0 END, evaluation_score DESC, date_discovered DESC"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        return self.connection.execute(sql, params).fetchall()

    def update_prospect(self, prospect_id: int, fields: dict):
        allowed = {
            "website_name", "domain", "page_url", "page_title", "meta_description",
            "language", "content_summary", "website_category", "opportunity_type",
            "contact_page_url", "public_email", "discovery_source", "date_discovered",
            "evaluation_score", "evaluation_reasoning", "outreach_angle",
            "suggested_target_page", "potential_concerns", "priority", "outreach_draft",
            "contact_status", "outreach_date", "follow_up_date", "response",
            "backlink_url", "link_status", "last_error", "analyzed_at",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return
        assignments = ", ".join(f"{key} = ?" for key in updates)
        self.connection.execute(
            f"UPDATE prospects SET {assignments} WHERE id = ?",
            tuple(updates.values()) + (prospect_id,),
        )
        self.connection.commit()

    def count(self) -> int:
        return self.connection.execute("SELECT COUNT(*) FROM prospects").fetchone()[0]

    def counts_by_priority(self) -> dict:
        rows = self.connection.execute(
            "SELECT COALESCE(priority, 'Unscored') AS priority, COUNT(*) AS count FROM prospects GROUP BY COALESCE(priority, 'Unscored')"
        ).fetchall()
        return {row["priority"]: row["count"] for row in rows}

    def counts_by_status(self) -> dict:
        rows = self.connection.execute(
            "SELECT contact_status, COUNT(*) AS count FROM prospects GROUP BY contact_status"
        ).fetchall()
        return {row["contact_status"]: row["count"] for row in rows}

    def counts_by_category(self) -> dict:
        rows = self.connection.execute(
            "SELECT COALESCE(website_category, 'Uncategorized') AS category, COUNT(*) AS count FROM prospects GROUP BY COALESCE(website_category, 'Uncategorized')"
        ).fetchall()
        return {row["category"]: row["count"] for row in rows}
