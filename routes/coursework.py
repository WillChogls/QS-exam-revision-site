from flask import Blueprint, abort, render_template

import models
from routes.browse import require_level, require_subject

bp = Blueprint("coursework", __name__)


@bp.route("/<level>/<subject_slug>/coursework")
def coursework(level, subject_slug):
    level_name = require_level(level)
    subject = require_subject(subject_slug)
    items = models.coursework_for(level, subject["id"])
    if not items and not models.years_for(level, subject["id"]):
        abort(404)
    return render_template(
        "coursework.html", level=level, level_name=level_name, subject=subject,
        items=items,
    )
