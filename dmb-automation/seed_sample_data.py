"""
Dev helper: seed the local SQLite `album_metadata` table with one sample album so the
Robot suite can be run by hand (`robot automation/create_album.robot`) without the worker.
In production the worker writes this table instead (see worker.py).
"""
import os
import sqlite3

base_path  = os.path.dirname(os.path.abspath(__file__))
db_path    = os.path.join(base_path, "resources", "database", "dmb_database.db")
cover_path = os.path.join(base_path, "assets", "sample_cover.jpg")
music_path = os.path.join(base_path, "assets", "sample_track.wav")

print(f"📁 DB path:    {db_path}")
print(f"📁 Cover path: {cover_path}  (exists: {os.path.exists(cover_path)})")
print(f"🎵 Track path: {music_path}  (exists: {os.path.exists(music_path)})")

os.makedirs(os.path.dirname(db_path), exist_ok=True)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Schema must match what worker.py writes and db_queries.robot reads.
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS album_metadata (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        title            TEXT NOT NULL,
        artist_name      TEXT NOT NULL,
        legal_name       TEXT NOT NULL,
        cover_image_path TEXT NOT NULL,
        music_file_path  TEXT NOT NULL,
        release_date     TEXT NOT NULL,
        genre            TEXT
    )
    """
)
cursor.execute("DELETE FROM album_metadata")
cursor.execute(
    """
    INSERT INTO album_metadata
        (title, artist_name, legal_name, cover_image_path, music_file_path, release_date, genre)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    ("Sample Album One", "Artist A", "Mitrxv", cover_path, music_path, "2026-12-05", "HipHop / Rap [Urban]"),
)

conn.commit()
conn.close()
print("✅ album_metadata seeded with one sample row.")
