from flask import Blueprint, abort, render_template

import models

bp = Blueprint("browse", __name__)


def require_level(level):
    if level not in models.LEVELS:
        abort(404)
    return models.LEVELS[level]


def require_subject(slug):
    subject = models.get_subject(slug)
    if subject is None:
        abort(404)
    return subject


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/<level>/")
def level(level):
    level_name = require_level(level)
    return render_template(
        "level.html", level=level, level_name=level_name,
        subjects=models.subjects_for_level(level),
    )


@bp.route("/<level>/<subject_slug>/")
def subject(level, subject_slug):
    level_name = require_level(level)
    subject = require_subject(subject_slug)
    years = models.years_for(level, subject["id"])
    has_coursework = bool(models.coursework_for(level, subject["id"]))
    if not years and not has_coursework:
        abort(404)
    return render_template(
        "subject.html", level=level, level_name=level_name, subject=subject,
        years=years, has_coursework=has_coursework,
    )


@bp.route("/<level>/<subject_slug>/<int:year>/")
def year(level, subject_slug, year):
    level_name = require_level(level)
    subject = require_subject(subject_slug)
    papers = models.search_papers(level, subject_slug, year)
    if not papers:
        abort(404)
    return render_template(
        "year.html", level=level, level_name=level_name, subject=subject,
        year=year, papers=papers,
    )


@bp.route("/paper/<int:paper_id>")
def paper(paper_id):
    paper = models.get_paper(paper_id)
    if paper is None:
        abort(404)
    return render_template(
        "paper.html", paper=paper, level_name=models.LEVELS[paper["level"]],
        files=models.paper_files(paper_id),
    )
