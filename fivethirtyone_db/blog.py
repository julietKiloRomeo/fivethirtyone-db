from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .auth import login_required
from . import db

bp = Blueprint('blog', __name__)

@bp.route('/')
@login_required
def index():

    lifts = list(db.all_sets(athlete=g.user))
    # [
    #    {'id': 321, 'weight': 27.5, 'reps': 5, 'lift_name': 'bench', 'athlete_name': 'camilla', 'date': datetime.date(2022, 11, 8), 'is_max': 1, 'base_max': None, 'base_reps': None, 'cycle': None},
    #    {'id': 321, 'weight': 27.5, 'reps': 5, 'lift_name': 'bench', 'athlete_name': 'camilla', 'date': datetime.date(2022, 11, 8), 'is_max': 1, 'base_max': None, 'base_reps': None, 'cycle': None}
    # ]
    for lift in lifts:
        lift["rep_str"] = lift["reps"] or f"({lift['base_reps']}+)"

    return render_template('blog/index.html', lifts=lifts)

@bp.route('/graphs')
@login_required
def graphs():

    lifts = list(db.all_sets(athlete=g.user))

    to_rec = lambda d: {"x": str(d["date"].isoformat()), "y":d["reps"]*d["weight"]}
    return render_template('blog/graphs.html', data = list(map(to_rec, lifts)))


@bp.route('/workset/<wsid>')
@login_required
def workset(wsid):

    lifts = list(db.all_sets(athlete=g.user))

    to_rec = lambda d: {"x": str(d["date"].isoformat()), "y":d["reps"]*d["weight"]}
    return render_template('blog/graphs.html', data = list(map(to_rec, lifts)))
