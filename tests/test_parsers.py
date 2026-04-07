"""
Tests for individual file parsers.
"""

import csv
import json
import sqlite3
import tempfile
from pathlib import Path

import pytest


# ── text parser ────────────────────────────────────────────────────────────────

def test_parse_text_utf8(tmp_path):
    from bot.indexer.parsers.text import parse_text
    f = tmp_path / "hello.txt"
    f.write_text("Hello, world!", encoding="utf-8")
    assert parse_text(f) == "Hello, world!"


def test_parse_text_latin1(tmp_path):
    from bot.indexer.parsers.text import parse_text
    f = tmp_path / "latin.txt"
    f.write_bytes("Héllo".encode("latin-1"))
    result = parse_text(f)
    assert "ll" in result  # at minimum the ASCII part is there


# ── data parsers ──────────────────────────────────────────────────────────────

def test_parse_json(tmp_path):
    from bot.indexer.parsers.data import parse_json
    f = tmp_path / "data.json"
    f.write_text(json.dumps({"key": "value", "num": 42}), encoding="utf-8")
    result = parse_json(f)
    assert "key" in result
    assert "value" in result
    assert "42" in result


def test_parse_json_invalid(tmp_path):
    from bot.indexer.parsers.data import parse_json
    f = tmp_path / "bad.json"
    f.write_text("not json at all {{{", encoding="utf-8")
    # Should not raise; returns raw text instead
    result = parse_json(f)
    assert "not json" in result


def test_parse_csv(tmp_path):
    from bot.indexer.parsers.data import parse_csv
    f = tmp_path / "data.csv"
    f.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
    result = parse_csv(f)
    assert "Alice" in result
    assert "Bob" in result
    assert "name" in result


def test_parse_tsv(tmp_path):
    from bot.indexer.parsers.data import parse_tsv
    f = tmp_path / "data.tsv"
    f.write_text("col1\tcol2\nfoo\tbar\n", encoding="utf-8")
    result = parse_tsv(f)
    assert "foo" in result
    assert "bar" in result


def test_parse_yaml(tmp_path):
    from bot.indexer.parsers.data import parse_yaml
    f = tmp_path / "config.yaml"
    f.write_text("project:\n  name: MyBot\n  version: 1\n", encoding="utf-8")
    result = parse_yaml(f)
    assert "MyBot" in result
    assert "version" in result


# ── markup parsers ────────────────────────────────────────────────────────────

def test_parse_html(tmp_path):
    from bot.indexer.parsers.markup import parse_html
    f = tmp_path / "page.html"
    f.write_text(
        "<html><body><h1>Title</h1><p>Hello <b>World</b></p></body></html>",
        encoding="utf-8",
    )
    result = parse_html(f)
    assert "Title" in result
    assert "Hello" in result
    assert "World" in result


def test_parse_xml(tmp_path):
    from bot.indexer.parsers.markup import parse_xml
    f = tmp_path / "data.xml"
    f.write_text(
        '<?xml version="1.0"?><root><item>Alpha</item><item>Beta</item></root>',
        encoding="utf-8",
    )
    result = parse_xml(f)
    assert "Alpha" in result
    assert "Beta" in result


# ── sql parser ────────────────────────────────────────────────────────────────

def test_parse_sql(tmp_path):
    from bot.indexer.parsers.sql import parse_sql
    f = tmp_path / "schema.sql"
    f.write_text("CREATE TABLE users (id INTEGER, name TEXT);", encoding="utf-8")
    result = parse_sql(f)
    assert "CREATE TABLE" in result
    assert "users" in result


# ── sqlite parser ─────────────────────────────────────────────────────────────

def test_parse_sqlite(tmp_path):
    from bot.indexer.parsers.sqlite_db import parse_sqlite
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, label TEXT)")
    conn.execute("INSERT INTO items VALUES (1, 'hello')")
    conn.execute("INSERT INTO items VALUES (2, 'world')")
    conn.commit()
    conn.close()

    result = parse_sqlite(db_path)
    assert "items" in result
    assert "hello" in result
    assert "world" in result


# ── code parser ───────────────────────────────────────────────────────────────

def test_parse_code(tmp_path):
    from bot.indexer.parsers.code import parse_code
    f = tmp_path / "script.py"
    f.write_text("def hello():\n    print('hi')\n", encoding="utf-8")
    result = parse_code(f)
    assert "def hello" in result
