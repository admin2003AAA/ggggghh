# 📁 Telegram File Indexer Bot

A professional, production-ready Telegram bot built with Python that automatically
indexes files in a local `data/` directory and provides fast full-text search over
their contents via Telegram commands.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Full-text search** | SQLite FTS5 with Unicode tokenisation |
| **30+ file formats** | Text, docs, data, code, databases (see list below) |
| **Auto-indexing** | Scans `data/` on startup; incremental or full re-index on demand |
| **Access control** | Optional whitelist of allowed Telegram user IDs |
| **Production-ready** | Clean architecture, async handlers, graceful shutdown, logging |

---

## 📂 Project Structure

```
.
├── bot/
│   ├── config.py          # Environment-based configuration
│   ├── main.py            # Bot entry-point and application wiring
│   ├── database/
│   │   └── __init__.py    # SQLite FTS5 index database
│   ├── indexer/
│   │   ├── indexer.py     # Core file walker and indexer
│   │   └── parsers/       # One module per file-format family
│   │       ├── text.py    # txt, md, log, rst
│   │       ├── markup.py  # html, htm, xml
│   │       ├── data.py    # json, yaml, csv, tsv
│   │       ├── pdf.py     # pdf
│   │       ├── docx.py    # docx
│   │       ├── xlsx.py    # xlsx, xlsm
│   │       ├── sqlite_db.py # sqlite, sqlite3, db
│   │       ├── sql.py     # sql
│   │       └── code.py    # py, js, ts, css, scss, go, …
│   └── handlers/
│       └── commands.py    # /start /help /reindex /search
├── data/                  # Drop your files here for indexing
├── tests/                 # pytest test suite
├── main.py                # Top-level launcher
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start

### 1. Clone & install dependencies

```bash
git clone https://github.com/admin2003AAA/ggggghh.git
cd ggggghh
pip install -r requirements.txt
```

### 2. Configure the bot

```bash
cp .env.example .env
# Edit .env — at minimum set BOT_TOKEN
```

Create a bot via [@BotFather](https://t.me/BotFather) and paste the token into `.env`.

### 3. Add files to index

```bash
cp /your/documents/* data/
```

### 4. Run

```bash
python main.py
```

The bot will:
1. Connect (or create) the SQLite FTS5 index database.
2. Scan `data/` and index all supported files.
3. Start polling Telegram for commands.

---

## 🤖 Telegram Commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/help` | List commands and supported formats |
| `/reindex` | Re-scan `data/` and rebuild the index |
| `/search <query>` | Full-text search across all indexed files |

**Example:**
```
/search project requirements
/search def authenticate
```

---

## 📄 Supported File Formats

| Category | Extensions |
|---|---|
| Plain text | `txt` `md` `markdown` `log` `rst` |
| Data / config | `json` `yaml` `yml` `csv` `tsv` |
| Markup | `html` `htm` `xml` |
| Documents | `pdf` `docx` |
| Spreadsheets | `xlsx` `xlsm` |
| Databases | `sqlite` `sqlite3` `db` `sql` |
| Source code | `py` `js` `ts` `jsx` `tsx` `css` `scss` `sass` `sh` `bash` `zsh` `go` `java` `c` `cpp` `h` `hpp` `cs` `rb` `php` `swift` `kt` `rs` `r` `lua` |
| Config files | `toml` `ini` `cfg` `conf` `env` |

Adding support for a new format is as simple as creating a new parser module and
registering the extension in `bot/indexer/parsers/__init__.py`.

---

## ⚙️ Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `BOT_TOKEN` | *(required)* | Telegram bot token from @BotFather |
| `ALLOWED_USERS` | *(empty = all)* | Comma-separated list of allowed Telegram user IDs |
| `DATA_DIR` | `./data` | Directory to index |
| `INDEX_DB_PATH` | `./index.db` | Path to the SQLite FTS5 index file |
| `MAX_FILE_SIZE_MB` | `50` | Files larger than this are skipped |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `MAX_SEARCH_RESULTS` | `10` | Maximum results returned per `/search` |

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

All 28 tests cover the parsers, database layer, and indexer logic.

---

## 🏗️ Architecture Highlights

- **SQLite FTS5** — built-in full-text search with `unicode61` tokeniser; no external
  search engine required.
- **Async-safe indexer** — heavy I/O runs in a thread-pool executor so the Telegram
  event loop is never blocked.
- **Parser registry** — a simple `dict[ext → callable]` makes it trivial to add new
  formats.
- **Incremental indexing** — on `/reindex`, only changed/new files are processed by
  default; pass `full=True` internally to wipe and rebuild.

