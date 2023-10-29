from flask import (
    Blueprint,
    flash,
    g,
    session,
    redirect,
    render_template,
    request,
    url_for,
    make_response,
    send_file,
)
from werkzeug.exceptions import abort

from .auth import login_required
from . import db, analysis, programs, config
import datetime
from xhtml2pdf import pisa
import tempfile
import plotly.express as px




bp = Blueprint("blog", __name__)


@bp.route("/")
@login_required
def index():

    way_in_the_future = datetime.date(2100, 1, 1)
    athlete = g.user
    lifts = sorted(
        athlete.worksets,
        key=lambda lift: lift["date"] or way_in_the_future,
        reverse=True,
    )
    # [
    #    {'id': 321, 'weight': 27.5, 'reps': 5, 'lift_name': 'bench', 'athlete_name': 'camilla', 'date': datetime.date(2022, 11, 8), 'is_max': 1, 'base_max': None, 'base_reps': None, 'cycle': None},
    #    {'id': 321, 'weight': 27.5, 'reps': 5, 'lift_name': 'bench', 'athlete_name': 'camilla', 'date': datetime.date(2022, 11, 8), 'is_max': 1, 'base_max': None, 'base_reps': None, 'cycle': None}
    # ]
    next_cycle = athlete.estimate_next_cycle()

    return render_template("blog/index.html", lifts=lifts, next_cycle=next_cycle)

def data_for_index_render():
    pass


def reload_session():
    g.user._load_worksets()
    session["user_dict"] = g.user.to_dict()


@bp.route("/graphs")
@login_required
def graphs():
    athlete = g.user
    completed_lifts = filter(lambda d: d["date"], athlete.worksets)
    completed_lifts = sorted(completed_lifts, key=lambda d: d['date'])


    def new_plotly_js_trace(lift, color):
        legend_group = lift
        return [
            dict(
                x=[],
                y=[],
                type="scatter",
                mode="lines",
                line={"shape": "hvh", "width": 3, "color": color},
                name=f"{lift} (line)",
                legendgroup=legend_group,
                showlegend=False,
            ),
            dict(
                x=[],
                y=[],
                text=[],
                type="scatter",
                mode="markers",
                marker={
                    "size": 12, 
                    "color": 'white',  # Set face color to white
                    "line": {'width': 4, 'color': color}  # Set edge color to the cycle color
                },
                name=lift,
                hovertemplate="""
    <b>%{x}</b><br><br>
    %{text}""",
                legendgroup=legend_group,
                showlegend=True,
            ),
        ]


    # Get the default Plotly color cycle
    color_cycle = px.colors.qualitative.Plotly
    data = {lift: new_plotly_js_trace(lift, color) for lift, color in zip(config["lifts"], color_cycle)}

    for record in completed_lifts:
        w, r = record["weight"], record["reps"]
        w_1rm = analysis.one_rm_fusion(record["weight"], record["reps"])
        txt = f"{r} x {w} kg → {w_1rm:.1f} kg"
        
        line_trace, marker_trace = data[record["lift_name"]]
        
        # Add data to marker trace
        marker_trace["x"].append(f"{record['date']}")
        marker_trace["y"].append(w_1rm)
        marker_trace["text"].append(txt)
        
        # Add data to line trace with filtering
        last_valid_value = next((y for y in reversed(line_trace["y"]) if y is not None), None)
        if last_valid_value is None or w_1rm >= 0.8 * last_valid_value:
            line_trace["x"].append(f"{record['date']}")
            line_trace["y"].append(w_1rm)


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
        athlete_name=g.user.name
    ).add()

    # reload cached worksets
    reload_session()
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
        reload_session()
        return redirect(request.referrer)

    db.Workset.update_row(
        wsid=updates["wsid"],
        date=updates["date"],
        lift_name=updates["lift"],
        reps=updates["reps"],
        weight=updates["weight"],
        is_max=updates.get("is_max", "") == "on",
    )
    # reload cached worksets
    reload_session()
    return redirect(request.referrer)


@bp.route("/pdf")
@login_required
def make_pdf():
    athlete = g.user
    first_set, *_ = worksets_to_do = athlete.worksets_to_do()
    # each workset is:
    # {'id': 379, 'weight': 35.0, 'reps': None, 'lift_name': 'squat', 'athlete_name': 'camilla', 'date': None, 'is_max': None,
    # 'base_max': 44.7921, 'base_reps': 3, 'cycle': 0}
    #
    # convert to a program:

    program = worksets_to_program(worksets_to_do, athlete=athlete.name)

    html = render_template(
        "blog/program.html",
        name=athlete.name,
        worksets_to_do=program,
        cycle=first_set["cycle"],
        base_reps=first_set["base_reps"],
    )

    with tempfile.NamedTemporaryFile() as f:
        # pdfkit.from_string(html, f.name)

        # convert HTML to PDF
        pisa_status = pisa.CreatePDF(
            html, dest=f  # the HTML to convert
        )  # file handle to recieve result

        return send_file(f.name, as_attachment=True, download_name=f"{athlete.name}.pdf")

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
        athlete = g.user.name

        for lift, athlete, weight, one_rm_max, base_reps, cycle in next_lifts(new_cycle, athlete):
            db.Workset(
                base_max=one_rm_max,
                base_reps=base_reps,
                cycle=cycle,
                weight=weight,
                lift_name=lift,
                athlete_name=athlete,
            ).add()

    reload_session()
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

    for lift in config["lifts"]:
        one_rm_max = float(new_cycle[lift + "-max"])
        train_max = 0.9 * one_rm_max
        to_lift = analysis.compile(athlete, lift, train_max, program, cycle=cycle)
        *_, last_set = to_lift.columns
        weight = to_lift[last_set]["weight"]
        yield (lift, athlete, weight, one_rm_max, base_reps, cycle)

