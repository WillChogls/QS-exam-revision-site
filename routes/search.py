from flask import Blueprint, render_template, request

import models

bp = Blueprint("search", __name__)


@bp.route("/search")
def search():
    level = request.args.get("level", "")
    subject = request.args.get("subject", "")
    year = request.args.get("year", type=int)
    if level not in models.LEVELS:
        level = ""
    searched = bool(level or subject or year)
    results = models.search_papers(level or None, subject or None, year)
    return render_template(
        "search.html",
        subjects=models.all_subjects(), years=models.all_years(),
        selected={"level": level, "subject": subject, "year": year},
        searched=searched, results=results,
    )
