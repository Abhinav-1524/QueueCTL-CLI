import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "store.db"


class Database:
    """sqlite-backed job storage for queuectl"""

    def __init__(self, db_path: Path = DB_PATH):
        self.path = db_path
        self.con = sqlite3.connect(self.path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self._init()

    # ------------------------------------------------------------------
    # setup
    # ------------------------------------------------------------------
    def _init(self):
        """create table if not exists"""
        q = """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            status TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            priority INTEGER DEFAULT 0,
            run_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
        with self.con:
            self.con.execute(q)

    # ------------------------------------------------------------------
    # creation
    # ------------------------------------------------------------------
    def insert_job(self, job_id: str, command: str, max_retries: int, priority: int = 0, run_at: str | None = None):
        """add a new job"""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        run_at = self._normalize_runat(run_at) or now
        sql = """
        INSERT INTO jobs (id, command, status, attempts, max_retries, priority, run_at, created_at, updated_at)
        VALUES (?, ?, 'pending', 0, ?, ?, ?, ?, ?)
        """
        with self.con:
            self.con.execute(sql, (job_id, command, max_retries, priority, run_at, now, now))

    # ------------------------------------------------------------------
    # retrieval
    # ------------------------------------------------------------------
    def next_pending(self):
        """get next pending job"""
        cur = self.con.cursor()
        cur.execute(
            "SELECT * FROM jobs WHERE status='pending' ORDER BY created_at ASC LIMIT 1"
        )
        return cur.fetchone()

    def get_job(self, job_id: str):
        """fetch single job"""
        cur = self.con.cursor()
        cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
        return cur.fetchone()

    def list_by_status(self, status: str):
        """list jobs by status"""
        cur = self.con.cursor()
        if status.lower() == "all":
            cur.execute("SELECT * FROM jobs ORDER BY datetime(created_at) DESC")
        else:
            cur.execute("SELECT * FROM jobs WHERE status=? ORDER BY datetime(created_at) DESC", (status,))
        return cur.fetchall()

    # ------------------------------------------------------------------
    # updates
    # ------------------------------------------------------------------
    def update_status(self, job_id: str, state: str):
        """update job state"""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with self.con:
            self.con.execute(
                "UPDATE jobs SET status=?, updated_at=? WHERE id=?", (state, now, job_id)
            )

    def bump_attempts(self, job_id: str):
        """increment attempt count"""
        with self.con:
            self.con.execute("UPDATE jobs SET attempts = attempts + 1 WHERE id=?", (job_id,))

    def restore_processing(self):
        """reset stuck jobs to pending"""
        with self.con:
            self.con.execute(
                "UPDATE jobs SET status='pending', updated_at=CURRENT_TIMESTAMP WHERE status='processing'"
            )

    # ------------------------------------------------------------------
    # worker fetch
    # ------------------------------------------------------------------
    def acquire_job(self):
        """select and lock a pending job"""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        UPDATE jobs
        SET status='processing', updated_at=?
        WHERE id = (
            SELECT id FROM jobs
            WHERE status='pending'
            AND datetime(run_at) <= datetime('now', 'utc')
            ORDER BY priority DESC, datetime(run_at) ASC, created_at ASC
            LIMIT 1
        )
        RETURNING *
        """
        with self.con:
            cur = self.con.execute(sql, (ts,))
            return cur.fetchone()

    # ------------------------------------------------------------------
    # reports
    # ------------------------------------------------------------------
    def summary(self):
        """count jobs by state"""
        cur = self.con.cursor()
        cur.execute("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status")
        return {row["status"]: row["n"] for row in cur.fetchall()}

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_runat(run_at: str | None):
        """ensure UTC timestamp format"""
        if not run_at:
            return None
        try:
            dt = datetime.fromisoformat(run_at.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.astimezone()
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
