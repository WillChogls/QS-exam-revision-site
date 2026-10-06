"""SQLite schema and query helpers.

Only metadata is stored. Question papers and marking instructions are linked
on sqa.org.uk, not rehosted.
"""
import sqlite3

from flask import current_app, g

# URL slug -> display name. Order here is display order.
LEVELS = {
    "n5": "National 5",
    "higher": "Higher",
    "ah": "Advanced Higher",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS subjects (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS papers (
    id             INTEGER PRIMARY KEY,
    level          TEXT NOT NULL CHECK (level IN ('n5', 'higher', 'ah')),
    subject_id     INTEGER NOT NULL REFERENCES subjects(id),
    year           INTEGER NOT NULL,
    paper_number   INTEGER NOT NULL,
    title          TEXT NOT NULL,
    qp_url         TEXT NOT NULL,
    mi_url         TEXT,  -- NULL if SQA hasn't published marking instructions
    UNIQUE (level, subject_id, year, paper_number)
);

-- Extras that go with a paper: answer booklets, audio, transcripts, maps, data sheets.
CREATE TABLE IF NOT EXISTS paper_files (
    id        INTEGER PRIMARY KEY,
    paper_id  INTEGER NOT NULL REFERENCES papers(id),
    label     TEXT NOT NULL,
    url       TEXT NOT NULL,
    file_type TEXT NOT NULL  -- PDF, MP3, ZIP, ...
);

CREATE TABLE IF NOT EXISTS coursework (
    id          INTEGER PRIMARY KEY,
    level       TEXT NOT NULL CHECK (level IN ('n5', 'higher', 'ah')),
    subject_id  INTEGER NOT NULL REFERENCES subjects(id),
    year        INTEGER NOT NULL,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    deadline    TEXT,  -- ISO date, or NULL if none set
    url         TEXT NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db):
    db.executescript(SCHEMA)


# --- Queries -----------------------------------------------------------------

def get_subject(slug):
    return get_db().execute("SELECT * FROM subjects WHERE slug = ?", (slug,)).fetchone()


def all_subjects():
    return get_db().execute("SELECT * FROM subjects ORDER BY name").fetchall()


def subjects_for_level(level):
    return get_db().execute(
        """SELECT DISTINCT s.* FROM subjects s
           WHERE s.id IN (SELECT subject_id FROM papers WHERE level = ?)
              OR s.id IN (SELECT subject_id FROM coursework WHERE level = ?)
           ORDER BY s.name""",
        (level, level),
    ).fetchall()


def years_for(level, subject_id):
    rows = get_db().execute(
        "SELECT DISTINCT year FROM papers WHERE level = ? AND subject_id = ? ORDER BY year DESC",
        (level, subject_id),
    ).fetchall()
    return [r["year"] for r in rows]


def all_years():
    rows = get_db().execute("SELECT DISTINCT year FROM papers ORDER BY year DESC").fetchall()
    return [r["year"] for r in rows]


_PAPER_SELECT = """SELECT p.*, s.name AS subject_name, s.slug AS subject_slug
                   FROM papers p JOIN subjects s ON s.id = p.subject_id"""


def get_paper(paper_id):
    return get_db().execute(f"{_PAPER_SELECT} WHERE p.id = ?", (paper_id,)).fetchone()


def search_papers(level=None, subject_slug=None, year=None):
    clauses, params = [], []
    if level:
        clauses.append("p.level = ?")
        params.append(level)
    if subject_slug:
        clauses.append("s.slug = ?")
        params.append(subject_slug)
    if year:
        clauses.append("p.year = ?")
        params.append(year)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return get_db().execute(
        f"{_PAPER_SELECT}{where} ORDER BY p.year DESC, s.name, p.level, p.paper_number",
        params,
    ).fetchall()


def paper_files(paper_id):
    return get_db().execute(
        "SELECT * FROM paper_files WHERE paper_id = ? ORDER BY id", (paper_id,)
    ).fetchall()


def coursework_for(level, subject_id):
    return get_db().execute(
        """SELECT * FROM coursework WHERE level = ? AND subject_id = ?
           ORDER BY year DESC, title""",
        (level, subject_id),
    ).fetchall()
