import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "app.db"


class TeaDatabase:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    user_name TEXT PRIMARY KEY,
                    tea1 TEXT NOT NULL DEFAULT '',
                    tea2 TEXT NOT NULL DEFAULT '',
                    tea3 TEXT NOT NULL DEFAULT '',
                    tea4 TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> dict:
        return {
            "user_name": row["user_name"],
            "teas": [row["tea1"], row["tea2"], row["tea3"], row["tea4"]],
        }

    def get_profile(self, user_name: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM profiles WHERE user_name = ?",
                (user_name.strip(),),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_profile(row)

    def get_last_profile(self) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM profiles
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return self._row_to_profile(row)

    def save_user_name(self, user_name: str) -> None:
        user_name = user_name.strip()
        profile = self.get_profile(user_name)
        teas = profile["teas"] if profile else ["", "", "", ""]
        self.save_profile(user_name, teas)

    def save_profile(self, user_name: str, teas: list[str]) -> None:
        user_name = user_name.strip()
        tea_values = [tea.strip() for tea in teas[:4]]
        while len(tea_values) < 4:
            tea_values.append("")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO profiles (
                    user_name, tea1, tea2, tea3, tea4, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_name) DO UPDATE SET
                    tea1 = excluded.tea1,
                    tea2 = excluded.tea2,
                    tea3 = excluded.tea3,
                    tea4 = excluded.tea4,
                    updated_at = excluded.updated_at
                """,
                (
                    user_name,
                    tea_values[0],
                    tea_values[1],
                    tea_values[2],
                    tea_values[3],
                    self._now(),
                ),
            )
