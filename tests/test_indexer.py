"""
Tests for the FileIndexer.
"""

import json
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture()
def db(tmp_path):
    from bot.database import IndexDatabase
    instance = IndexDatabase(tmp_path / "index.db")
    instance.connect()
    yield instance
    instance.close()


@pytest.fixture()
def data_dir(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture()
def indexer(db, data_dir):
    from bot.indexer.indexer import FileIndexer
    return FileIndexer(db=db, data_dir=data_dir)


def test_index_text_file(db, data_dir, indexer):
    (data_dir / "readme.txt").write_text("Hello indexer world", encoding="utf-8")
    stats = indexer.reindex()
    assert stats.added == 1
    results = db.search("indexer world")
    assert len(results) == 1
    assert results[0]["path"].endswith("readme.txt")


def test_index_json_file(db, data_dir, indexer):
    (data_dir / "config.json").write_text(
        json.dumps({"app": "MyApp", "version": "2.0"}), encoding="utf-8"
    )
    indexer.reindex()
    results = db.search("MyApp")
    assert len(results) == 1


def test_index_multiple_files(db, data_dir, indexer):
    (data_dir / "a.txt").write_text("alpha beta gamma", encoding="utf-8")
    (data_dir / "b.txt").write_text("delta epsilon zeta", encoding="utf-8")
    stats = indexer.reindex()
    assert stats.added == 2


def test_full_reindex_clears_old(db, data_dir, indexer):
    (data_dir / "old.txt").write_text("old content here", encoding="utf-8")
    indexer.reindex(full=True)
    # Remove old file and add a new one
    (data_dir / "old.txt").unlink()
    (data_dir / "new.txt").write_text("new content here", encoding="utf-8")
    indexer.reindex(full=True)
    assert db.search("old content") == []
    assert len(db.search("new content")) == 1


def test_incremental_reindex_keeps_old(db, data_dir, indexer):
    (data_dir / "existing.txt").write_text("existing file content", encoding="utf-8")
    indexer.reindex()  # first pass
    (data_dir / "another.txt").write_text("another new file", encoding="utf-8")
    stats = indexer.reindex()  # incremental
    # The new file should be added; the old one should be updated or stay
    assert stats.added >= 1


def test_skip_unsupported_extension(db, data_dir, indexer):
    (data_dir / "binary.exe").write_bytes(b"\x00\x01\x02\x03")
    (data_dir / "note.txt").write_text("searchable text", encoding="utf-8")
    stats = indexer.reindex()
    # Only the .txt file should be indexed
    assert stats.added == 1


def test_empty_data_dir(db, data_dir, indexer):
    stats = indexer.reindex()
    assert stats.added == 0
    assert stats.failed == 0


def test_nonexistent_data_dir(db, tmp_path):
    from bot.indexer.indexer import FileIndexer
    missing = tmp_path / "does_not_exist"
    idx = FileIndexer(db=db, data_dir=missing)
    stats = idx.reindex()
    assert stats.added == 0
    # Directory should be created
    assert missing.exists()
