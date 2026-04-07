"""
Tests for the IndexDatabase (SQLite FTS5 layer).
"""

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


def test_upsert_and_search(db):
    db.upsert_file("/data/hello.txt", ".txt", 100, "The quick brown fox jumps")
    results = db.search("quick fox")
    assert len(results) == 1
    assert results[0]["path"] == "/data/hello.txt"


def test_update_existing(db):
    db.upsert_file("/data/doc.txt", ".txt", 50, "original content")
    db.upsert_file("/data/doc.txt", ".txt", 60, "updated content here")
    results = db.search("updated content")
    assert len(results) == 1
    # Should not appear under old content
    results_old = db.search("original content")
    assert len(results_old) == 0


def test_remove_file(db):
    db.upsert_file("/data/temp.txt", ".txt", 10, "temporary data")
    db.remove_file("/data/temp.txt")
    assert db.search("temporary data") == []


def test_clear_all(db):
    db.upsert_file("/data/a.txt", ".txt", 10, "alpha content")
    db.upsert_file("/data/b.txt", ".txt", 20, "beta content")
    db.clear_all()
    assert db.search("alpha") == []
    assert db.search("beta") == []


def test_get_stats(db):
    db.upsert_file("/data/a.txt", ".txt", 100, "hello world")
    db.upsert_file("/data/b.py", ".py", 200, "def foo(): pass")
    stats = db.get_stats()
    assert stats["total_files"] == 2
    assert stats["unique_extensions"] == 2
    assert stats["total_bytes"] == 300


def test_get_indexed_paths(db):
    db.upsert_file("/data/x.txt", ".txt", 5, "x content")
    db.upsert_file("/data/y.txt", ".txt", 5, "y content")
    paths = db.get_indexed_paths()
    assert "/data/x.txt" in paths
    assert "/data/y.txt" in paths


def test_search_no_results(db):
    db.upsert_file("/data/a.txt", ".txt", 10, "hello world")
    assert db.search("zzznomatch") == []


def test_search_special_chars_dont_raise(db):
    db.upsert_file("/data/a.txt", ".txt", 10, "test content")
    # These would crash raw FTS5 but should be handled gracefully
    results = db.search('test AND "complex" OR (query)')
    assert isinstance(results, list)
