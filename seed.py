"""Create the database from data/sqa_papers.json (made by scrape_sqa.py).

Run: python seed.py   (wipes and recreates revision.db; no network needed)

Each SQA file is sorted into one of:
  - a main exam paper (question paper, Paper 1, Reading, Listening, ...)
  - an extra attached to a paper (answer booklet, audio, transcript, map, sheet, ...)
  - a coursework document (assignment briefs, pro formas, coursework MIs, ...)
Marking instructions are matched to papers by name; a generic "mi" covers every
paper in that exam that has no closer match.
"""
import json
import os
import re
import sqlite3
import unicodedata
from collections import defaultdict

import models

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "revision.db")
DATA_PATH = os.path.join(ROOT, "data", "sqa_papers.json")

# Substring matches against " name " (padded), so a leading/trailing space means a word boundary.
COURSEWORK_WORDS = ("assignment", "assigment", "coursework", "proforma", "pro forma",
                    " cat ", "practical activity", "practical actvity", "research",
                    "planning for commercial", "practical modelling", "spreadsheet",
                    "marking grid", "marking key")
EXTRA_WORDS = ("booklet", "sheet", " map", "supplementary", "transcript", "audio",
               "excerpt", "electronic file", "information and instructions", " cover",
               " text ", "workbook", "worksheet")


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def key(name):
    """Normalised name for matching papers, extras and MIs."""
    k = re.sub(r"[^a-z0-9]", "", name.lower()).replace("paipear", "paper").removeprefix("25percent")
    return k.replace("readingforruae", "ruae").replace("ruae", "readingforunderstandinganalysisandevaluation")


def has_word(name, words):
    n = f" {name.lower()} "
    return any(w in n for w in words)


def pretty(name):
    if name == "QP":
        return "Question paper"
    return re.sub(r"\b(Paper|Section)(\d)", r"\1 \2", name).strip()


def common_prefix(a, b):
    return len(os.path.commonprefix([a, b]))


def build(records):
    """Group records into papers (with extras + MI) and coursework rows."""
    diets = defaultdict(list)
    for r in records:
        diets[(r["level"], r["subject"], r["year"])].append(r)

    papers, coursework = [], []
    for (level, subject, year), files in diets.items():
        qps = [f for f in files if f["type"] == "PAST_PAPER"]
        mis = [f for f in files if f["type"] != "PAST_PAPER"]

        mains, extras = [], []
        for f in qps:
            if has_word(f["paper"], COURSEWORK_WORDS):
                coursework.append((level, subject, year, pretty(f["paper"]), f["url"]))
            elif has_word(f["paper"], EXTRA_WORDS):
                extras.append(f)
            else:
                mains.append({"file": f, "key": key(f["paper"]), "mi": None, "extras": []})

        if not mains:  # e.g. coursework-only courses
            for f in extras:
                coursework.append((level, subject, year, pretty(f["paper"]), f["url"]))
            extras = []

        generic_mi = None
        for f in mis:
            k = key(f["paper"])
            match = next((m for m in mains if m["key"] == k), None) or next(
                (m for m in mains if m["mi"] is None and (m["key"].startswith(k) or k.startswith(m["key"]))), None)
            if has_word(f["paper"], COURSEWORK_WORDS):
                coursework.append((level, subject, year, f"{pretty(f['paper'])} (marking instructions)", f["url"]))
            elif match:
                match["mi"] = f["url"]
            elif k == "mi" or len(mains) == 1:
                generic_mi = generic_mi or f["url"]
            else:
                coursework.append((level, subject, year, f"{pretty(f['paper'])} (marking instructions)", f["url"]))
        for m in mains:
            m["mi"] = m["mi"] or generic_mi

        # Attach each extra to the paper it shares the longest name prefix with;
        # extras that match nothing (e.g. a shared data booklet) go on every paper.
        for f in extras:
            k = key(f["paper"])
            best = max(mains, key=lambda m: common_prefix(m["key"], k))
            targets = [best] if common_prefix(best["key"], k) >= 5 else mains
            for m in targets:
                m["extras"].append((pretty(f["paper"]), f["url"], f["fileType"]))

        mains.sort(key=lambda m: m["key"])
        for number, m in enumerate(mains, 1):
            papers.append({
                "level": level, "subject": subject, "year": year, "number": number,
                "title": pretty(m["file"]["paper"]), "qp_url": m["file"]["url"],
                "mi_url": m["mi"], "extras": m["extras"],
            })
    return papers, coursework


def seed(db, records):
    db.executescript("""DROP TABLE IF EXISTS paper_files; DROP TABLE IF EXISTS coursework;
                        DROP TABLE IF EXISTS papers; DROP TABLE IF EXISTS subjects;""")
    models.init_db(db)

    names = sorted({r["subject"] for r in records})
    db.executemany("INSERT INTO subjects (name, slug) VALUES (?, ?)", [(n, slugify(n)) for n in names])
    subject_ids = {name: id_ for id_, name in db.execute("SELECT id, name FROM subjects")}

    papers, coursework = build(records)
    for p in papers:
        cur = db.execute(
            """INSERT INTO papers (level, subject_id, year, paper_number, title, qp_url, mi_url)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (p["level"], subject_ids[p["subject"]], p["year"], p["number"], p["title"], p["qp_url"], p["mi_url"]),
        )
        db.executemany(
            "INSERT INTO paper_files (paper_id, label, url, file_type) VALUES (?, ?, ?, ?)",
            [(cur.lastrowid, *extra) for extra in p["extras"]],
        )
    db.executemany(
        "INSERT INTO coursework (level, subject_id, year, title, url) VALUES (?, ?, ?, ?, ?)",
        [(lvl, subject_ids[s], y, t, u) for lvl, s, y, t, u in coursework],
    )
    db.commit()


if __name__ == "__main__":
    with open(DATA_PATH) as f:
        records = json.load(f)
    with sqlite3.connect(DB_PATH) as conn:
        seed(conn, records)
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ("subjects", "papers", "paper_files", "coursework")}
        no_mi = conn.execute("SELECT COUNT(*) FROM papers WHERE mi_url IS NULL").fetchone()[0]
    print(f"Seeded {DB_PATH}: {counts}, papers without MI: {no_mi}")
