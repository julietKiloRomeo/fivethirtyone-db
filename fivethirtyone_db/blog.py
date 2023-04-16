from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
    make_response,
    send_file,
)
from werkzeug.exceptions import abort

from .auth import login_required
from . import db, analysis, programs
import datetime
from xhtml2pdf import pisa
import tempfile


LIFTS = ["military", "deadlift", "bench", "squat"]

INCREMENTS = {
    5: {"next_base_reps": 3, "cycle_increment": 0},
    3: {"next_base_reps": 1, "cycle_increment": 0},
    1: {"next_base_reps": 0, "cycle_increment": 0},
    0: {"next_base_reps": 5, "cycle_increment": 1},
    None: {"next_base_reps": 5, "cycle_increment": 0},
}


bp = Blueprint("blog", __name__)


@bp.route("/")
@login_required
def index():

    way_in_the_future = datetime.date(2100, 1, 1)
    athlete = db.Athlete(name=g.user)
    lifts = sorted(
        athlete.worksets,
        key=lambda lift: lift["date"] or way_in_the_future,
        reverse=True,
    )
    # [
    #    {'id': 321, 'weight': 27.5, 'reps': 5, 'lift_name': 'bench', 'athlete_name': 'camilla', 'date': datetime.date(2022, 11, 8), 'is_max': 1, 'base_max': None, 'base_reps': None, 'cycle': None},
    #    {'id': 321, 'weight': 27.5, 'reps': 5, 'lift_name': 'bench', 'athlete_name': 'camilla', 'date': datetime.date(2022, 11, 8), 'is_max': 1, 'base_max': None, 'base_reps': None, 'cycle': None}
    # ]
    next_cycle = estimate_next_cycle(g.user)

    return render_template("blog/index.html", lifts=lifts, next_cycle=next_cycle)


@bp.route("/graphs")
@login_required
def graphs():
    athlete = db.Athlete(name=g.user)
    completed_lifts = filter(lambda d: d["date"], athlete.worksets)

    def new_plotly_js_trace(lift):
        return [
            dict(
                x=[],
                y=[],
                text=[],
                type="scatter",
                mode="lines+markers",
                line={"shape": "hvh", "width": 3},
                marker={"size": 10},
                name=lift,
                hovertemplate="""
<b>%{x}</b><br><br>
%{text}""",
            )
        ]

    LIFTS = ["deadlift", "squat", "bench", "military"]
    data = {lift: new_plotly_js_trace(lift) for lift in LIFTS}

    for record in completed_lifts:
        # add x and y data
        w, r = record["weight"], record["reps"]
        w_1rm = analysis.one_rm_fusion(record["weight"], record["reps"])
        txt = f"{r} x {w} kg → {w_1rm:.1f} kg"
        plot_to_expand = data[record["lift_name"]][0]
        plot_to_expand["x"].append(f"{record['date']}")
        plot_to_expand["y"].append(w_1rm)
        plot_to_expand["text"].append(txt)

    return render_template("blog/graphs.html", data=data)


@bp.route("/workset/add", methods=("POST",))
@login_required
def new_workset():
    new_set = dict(request.form)
    db.Workset(
        base_max="null",
        base_reps="null",
        cycle="null",
        weight=new_set["weight"],
        lift_name=new_set["lift"],
        athlete_name=g.user
    ).add()

    return redirect(request.referrer)


@bp.route("/workset/<wsid>", methods=("GET", "POST"))
@login_required
def workset(wsid):

    if request.method == "GET":
        # what should we do here?
        return redirect(request.referrer)

    updates = dict(request.form)

    if updates["send"] == "delete":
        db.Workset.delete_by_id(updates["wsid"])
        return redirect(request.referrer)

    db.Workset.update_row(
        wsid=updates["wsid"],
        date=updates["date"],
        lift_name=updates["lift"],
        reps=updates["reps"],
        weight=updates["weight"],
    )

    return redirect(request.referrer)


@bp.route("/pdf")
@login_required
def make_pdf():
    name = g.user

    athlete = db.Athlete(name)
    worksets_to_do = athlete.worksets_to_do()
    # each workset is:
    # {'id': 379, 'weight': 35.0, 'reps': None, 'lift_name': 'squat', 'athlete_name': 'camilla', 'date': None, 'is_max': None,
    # 'base_max': 44.7921, 'base_reps': 3, 'cycle': 0}
    #
    # convert to a program:

    program = worksets_to_program(worksets_to_do, athlete=name)

    html = render_template(
        "blog/program.html",
        name=name,
        worksets_to_do=program,
        cycle=worksets_to_do[0]["cycle"],
        base_reps=worksets_to_do[0]["base_reps"],
    )

    with tempfile.NamedTemporaryFile() as f:
        # pdfkit.from_string(html, f.name)

        # convert HTML to PDF
        pisa_status = pisa.CreatePDF(
            html, dest=f  # the HTML to convert
        )  # file handle to recieve result

        return send_file(f.name, as_attachment=True, download_name=f"{g.user}.pdf")

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "inline; filename=output.pdf"
    return response

def worksets_to_program(worksets_to_do, athlete):
    compile = lambda ws: analysis.compile(
        athlete,
        ws["lift_name"],
        ws["base_max"] * 0.9,
        programs[ws["base_reps"]],
        cycle=ws["cycle"],
    )
    program = {ws["lift_name"]: compile(ws) for ws in worksets_to_do}
    return [
        {
            "lift": lift,
            "reps": df.loc["reps"].to_list(),
            "weight": df.loc["weight"].to_list(),
        }
        for lift, df in program.items()
    ]

@bp.route("/cycle/new", methods=("GET", "POST"))
@login_required
def add_cycle():
    """add a new cycle for an athlete"""

    if request.method == "POST":
        # {'cycle-index': '0', 'rep-base': '1', 'bench-max': '35.0', 'deadlift-max': '67.5', 'military-max': '25.0', 'squat-max': '42.5'}
        new_cycle = dict(request.form)
        athlete = g.user

        for lift, athlete, weight, one_rm_max, base_reps, cycle in next_lifts(new_cycle, athlete):
            db.Workset(
                base_max=one_rm_max,
                base_reps=base_reps,
                cycle=cycle,
                weight=weight,
                lift_name=lift,
                athlete_name=athlete,
            ).add()

    return redirect(request.referrer)

def next_lifts(new_cycle, athlete):
    """

    Arguments:
        new_cycle (dict[str, str]) : with keys cycle-index, rep-base, bench-max, deadlift-max, military-max, squat-max
        athlete (str) : 
    
    Returns:
        (str, str, float, float, int, int) : same format as the input to add_cycle()
    """
    cycle = int(new_cycle["cycle-index"])
    base_reps = int(new_cycle["rep-base"])
    program = programs[base_reps]

    for lift in LIFTS:
        one_rm_max = float(new_cycle[lift + "-max"])
        train_max = 0.9 * one_rm_max
        to_lift = analysis.compile(athlete, lift, train_max, program, cycle=cycle)
        weight = to_lift[5]["weight"]
        yield (lift, athlete, weight, one_rm_max, base_reps, cycle)



def estimate_next_cycle(athlete):
    """add a new cycle for an athlete"""

    athlete = db.Athlete(athlete)
    latest_workset = athlete.latest_cycle()

    latest_max_set = {lift: athlete.latest_max(lift) for lift in LIFTS}
    latest_max_1rm = {
        lift: analysis.one_rm_fusion(ws["weight"], ws["reps"])
        for lift, ws in latest_max_set.items()
    }

    current_cycle = latest_workset.get("cycle", -1)
    current_base_reps = latest_workset.get("base_reps", 0)

    next_cycle = current_cycle + INCREMENTS[current_base_reps]["cycle_increment"]
    next_base_reps = INCREMENTS[current_base_reps]["next_base_reps"]

    return dict(
        next_cycle=next_cycle,
        next_base_reps=next_base_reps,
        **latest_max_1rm,
    )
