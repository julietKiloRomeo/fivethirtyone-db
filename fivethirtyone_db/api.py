from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from .auth import login_required
from . import db

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/lifts/<lift_name>")
@login_required
def get_lift(lift_name):

    lifts = list(db.all_sets(athlete=g.user))
    for lift in lifts:
        lift["rep_str"] = lift["reps"] or f"({lift['base_reps']}+)"

    return [lift for lift in lifts if lift["lift_name"] == lift_name]


@bp.route("/lift/rm/<id>")
@login_required
def rm_lift(id):
    print(f"delete lift #{id}!")
    return redirect(request.referrer)
