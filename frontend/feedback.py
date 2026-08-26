import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "feedback.db")


def init_db():
    """Creates the feedback table if it doesn't already exist. Safe to call every time."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id TEXT NOT NULL,
            service_name TEXT NOT NULL,
            issue_type TEXT NOT NULL,       -- 'extra_document_asked' or 'document_not_needed'
            document_name TEXT NOT NULL,
            notes TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_feedback(service_id: str, service_name: str, issue_type: str,
                   document_name: str, notes: str = "") -> None:
    """Stores one citizen-reported discrepancy."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO feedback (service_id, service_name, issue_type, document_name, notes, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (service_id, service_name, issue_type, document_name, notes,
          datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_all_feedback() -> list:
    """Returns all stored feedback, most recent first. Useful for review / demo."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM feedback ORDER BY timestamp DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_discrepancy_count(service_id: str, document_name: str) -> int:
    """
    Counts how many times a specific document has been reported as a
    discrepancy for a service. This is the number the proposal's
    'confidence-weighted correction' logic would check against a
    threshold (e.g. 3+ reports = flag for review).
    """
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("""
        SELECT COUNT(*) FROM feedback
        WHERE service_id = ? AND document_name = ?
    """, (service_id, document_name)).fetchone()[0]
    conn.close()
    return count


if __name__ == "__main__":
    init_db()
    print("Feedback database initialized at:", DB_PATH)

    # Quick manual test
    save_feedback(
        service_id="S001",
        service_name="Passport - Fresh Application",
        issue_type="extra_document_asked",
        document_name="Police Verification Certificate",
        notes="Was asked for this even though it wasn't in the predicted list",
    )
    print("\nAll feedback so far:")
    for row in get_all_feedback():
        print(f"  [{row['timestamp']}] {row['service_name']} — "
              f"{row['issue_type']}: {row['document_name']}")