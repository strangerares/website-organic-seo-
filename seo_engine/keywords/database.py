import sqlite3
from pathlib import Path
from typing import Optional


class KeywordDatabase:
    def __init__(self, path: str = "keywords.db"):
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
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            country TEXT,
            language TEXT,
            search_intent TEXT,
            search_volume TEXT,
            keyword_difficulty TEXT,
            cpc TEXT,
            competition TEXT,
            source TEXT NOT NULL,
            data_type TEXT NOT NULL,
            date_retrieved TEXT,
            related_keywords TEXT,
            recommended_target_page TEXT,
            opportunity_score INTEGER,
            long_tail INTEGER DEFAULT 0,
            topic_cluster TEXT,
            ai_suggestion INTEGER DEFAULT 0,
            ai_reasoning TEXT,
            missing_page TEXT,
            article_opportunity TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_keyword_intent ON keywords(search_intent);
        CREATE INDEX IF NOT EXISTS idx_keyword_cluster ON keywords(topic_cluster);
        CREATE INDEX IF NOT EXISTS idx_keyword_score ON keywords(opportunity_score);
        """)
        self.connection.commit()

    def add_keyword(self, data: dict) -> tuple[bool, int]:
        existing = self.connection.execute(
            "SELECT id FROM keywords WHERE keyword = ?", (data["keyword"].strip().lower(),)
        ).fetchone()
        if existing:
            return False, existing["id"]
        fields = (
            "keyword", "country", "language", "search_intent", "search_volume",
            "keyword_difficulty", "cpc", "competition", "source", "data_type",
            "date_retrieved", "related_keywords", "recommended_target_page",
            "opportunity_score", "long_tail", "topic_cluster", "ai_suggestion",
            "ai_reasoning", "missing_page", "article_opportunity", "created_at",
        )
        values = {field: data.get(field) for field in fields}
        placeholders = ", ".join("?" for _ in fields)
        columns = ", ".join(fields)
        cursor = self.connection.execute(
            f"INSERT INTO keywords ({columns}) VALUES ({placeholders})",
            tuple(values[field] for field in fields),
        )
        self.connection.commit()
        return True, cursor.lastrowid

    def get_keyword(self, keyword_id: int) -> Optional[sqlite3.Row]:
        return self.connection.execute("SELECT * FROM keywords WHERE id = ?", (keyword_id,)).fetchone()

    def get_by_text(self, keyword: str) -> Optional[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM keywords WHERE keyword = ?", (keyword.strip().lower(),)
        ).fetchone()

    def list_keywords(self, intent: Optional[str] = None, cluster: Optional[str] = None) -> list[sqlite3.Row]:
        sql = "SELECT * FROM keywords"
        params = []
        clauses = []
        if intent:
            clauses.append("search_intent = ?")
            params.append(intent)
        if cluster:
            clauses.append("topic_cluster = ?")
            params.append(cluster)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY CASE WHEN opportunity_score IS NULL THEN 1 ELSE 0 END, opportunity_score DESC, keyword ASC"
        return self.connection.execute(sql, params).fetchall()

    def update_keyword(self, keyword_id: int, fields: dict):
        allowed = {
            "country", "language", "search_intent", "search_volume", "keyword_difficulty",
            "cpc", "competition", "source", "data_type", "date_retrieved", "related_keywords",
            "recommended_target_page", "opportunity_score", "long_tail", "topic_cluster",
            "ai_suggestion", "ai_reasoning", "missing_page", "article_opportunity",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return
        assignments = ", ".join(f"{key} = ?" for key in updates)
        self.connection.execute(
            f"UPDATE keywords SET {assignments} WHERE id = ?",
            tuple(updates.values()) + (keyword_id,),
        )
        self.connection.commit()

    def count(self) -> int:
        return self.connection.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]

    def counts_by_intent(self) -> dict:
        rows = self.connection.execute(
            "SELECT COALESCE(search_intent, 'Unclassified') AS value, COUNT(*) AS count FROM keywords GROUP BY COALESCE(search_intent, 'Unclassified')"
        ).fetchall()
        return {row["value"]: row["count"] for row in rows}

    def counts_by_cluster(self) -> dict:
        rows = self.connection.execute(
            "SELECT COALESCE(topic_cluster, 'Unclustered') AS value, COUNT(*) AS count FROM keywords GROUP BY COALESCE(topic_cluster, 'Unclustered')"
        ).fetchall()
        return {row["value"]: row["count"] for row in rows}
