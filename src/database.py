import logging
import os
from typing import Any, Dict, List, Optional

import duckdb

LOGGER = logging.getLogger(__name__)


class DuckDBManager:
    DB_FILE = "dubber_progress.db"

    def __init__(self, db_path: str = "/tmp"):
        self.db_path = os.path.join(db_path, self.DB_FILE)
        try:
            self.conn = duckdb.connect(self.db_path)
            LOGGER.info(f"Connected to DuckDB at {self.db_path}")
            self.create_tables()
        except Exception as e:
            LOGGER.error(f"Failed to connect to DuckDB: {e}")
            self.conn = None

    def create_tables(self):
        """Creates database tables if they don't exist."""
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR PRIMARY KEY,
                    source_file_path VARCHAR,
                    target_language VARCHAR,
                    dubbed_file_path VARCHAR,
                    last_saved_at TIMESTAMP
                );
            """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS segments (
                    segment_id VARCHAR PRIMARY KEY,
                    user_id VARCHAR,
                    start_ms BIGINT,
                    end_ms BIGINT,
                    transcript VARCHAR,
                    translation VARCHAR,
                    speaker VARCHAR,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """
            )
        LOGGER.info("Tables 'users' and 'segments' are ready.")

    def save_progress(
        self,
        user_id: str,
        source_file_path: Optional[str],
        target_language: Optional[str],
        dubbed_file_path: Optional[str],
        segments: List[Dict[str, Any]],
    ):
        """Saves or updates user progress."""
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (user_id, source_file_path, target_language, dubbed_file_path, last_saved_at)
                VALUES (?, ?, ?, ?, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    source_file_path = EXCLUDED.source_file_path,
                    target_language = EXCLUDED.target_language,
                    dubbed_file_path = EXCLUDED.dubbed_file_path,
                    last_saved_at = EXCLUDED.last_saved_at;
                """,
                (user_id, source_file_path, target_language, dubbed_file_path),
            )

            # Clear old segments for this user
            cur.execute("DELETE FROM segments WHERE user_id = ?", (user_id,))

            # Insert new segments
            if segments:
                for segment in segments:
                    cur.execute(
                        """
                        INSERT INTO segments (segment_id, user_id, start_ms, end_ms, transcript, translation, speaker)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            segment.get("id"),
                            user_id,
                            segment.get("start"),
                            segment.get("end"),
                            segment.get("transcript"),
                            segment.get("translation"),
                            segment.get("speaker"),
                        ),
                    )
        LOGGER.info(f"Progress saved for user_id: {user_id}")

    def restore_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Restores user progress from the database."""
        if not self.conn:
            return None
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT source_file_path, target_language, dubbed_file_path FROM users WHERE user_id = ?",
                (user_id,),
            )
            user_data = cur.fetchone()
            if not user_data:
                LOGGER.warning(f"No progress found for user_id: {user_id}")
                return None

            progress = {
                "source_file_path": user_data[0],
                "target_language": user_data[1],
                "dubbed_file_path": user_data[2],
            }

            cur.execute(
                "SELECT segment_id, start_ms, end_ms, transcript, translation, speaker FROM segments WHERE user_id = ? ORDER BY start_ms",
                (user_id,),
            )
            segments_data = cur.fetchall()

            segments = []
            for seg_data in segments_data:
                segments.append(
                    {
                        "id": seg_data[0],
                        "start": seg_data[1],
                        "end": seg_data[2],
                        "transcript": seg_data[3],
                        "translation": seg_data[4],
                        "speaker": seg_data[5],
                        "path": "",  # 'path' is for runtime audio chunks, not saved
                    }
                )

            progress["segments"] = segments
            LOGGER.info(f"Progress restored for user_id: {user_id}")
            return progress

    def reset_progress(self, user_id: str):
        """Deletes all progress for a given user."""
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            # Delete from segments first due to foreign key constraint
            cur.execute("DELETE FROM segments WHERE user_id = ?", (user_id,))
            cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        LOGGER.info(f"Progress reset for user_id: {user_id}")

    def __del__(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
