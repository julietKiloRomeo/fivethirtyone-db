import ipywidgets
import datetime
import pandas as pd
import re

from io import StringIO

from IPython.display import HTML

import plotly.graph_objects as go

from ipywidgets import Dropdown


def plot_progression(lift):
    fig = go.Figure()

    for lifter, df_slice in lifts.query(f"lift == '{lift}'").groupby("lifter"):
        x = df_slice.date
        y = df_slice.one_rep_max

        text = [
            f"{n:.0f} X {w:.1f} kg"
            for n, w in zip(df_slice["reps"], df_slice["weight"])
        ]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                name=lifter,
                line_shape="hvh",
                text=text,
            )
        )

    fig.show()


class MyWidgets:
    def __init__(self):
        self.reps = ipywidgets.IntSlider(min=1, max=25)

        self.weight = ipywidgets.FloatSlider(min=10, max=150, step=2.5)

        self.lift = ipywidgets.Dropdown(options=LIFTS)
        self.cycle = ipywidgets.Dropdown(
            options=[0, 1, 2, 3, 4, 5],
        )

        self.lifter = ipywidgets.Dropdown(options=LIFTERS)

        self.program = ipywidgets.Dropdown(
            options={
                "off": csv_program_off,
                "1": csv_program_1,
                "3": csv_program_3,
                "5": csv_program_5,
            }
        )

        self.is_max = ipywidgets.Checkbox()

        self.date = ipywidgets.DatePicker()
        self.date.value = datetime.date.today()


def repstr(lifter, lift, weight, reps, date, is_max):
    print("")
    print(f"{lifter},{date:%Y-%m-%d},{lift},{weight:.0f},{reps:.0f},{is_max}")


def display_day(lift, program=program, lifters=["irka", "jikr", "cam"]):
    comment = comments.get(lift, "")
    ass = assistance.get(lift, "")
    display(
        HTML(
            f"""
    <div >
        <div style="width: 200px;">
          <h2>{lift}</h2>
          <p style="color:#999999";>{comment}</p>
        </div>
        <div style="flex-grow: 1;">
          <p style="color:#BBBBBB";>cycle {CYCLE}</p>
          <p style="color:#555555";>{ass}</p>
        </div>
    </div>
    """
        )
    )
    for lifter in lifters:

        s = (
            compile(
                lifter=lifter, exercise=lift, lifts=lifts, program=program, cycle=CYCLE
            )
            .style.set_table_styles(
                [
                    {"selector": "thead", "props": [("display", "none")]},
                    {
                        "selector": "td",
                        "props": [("padding", "12px 35px"), ("font-size", "18px")],
                    },
                ]
            )
            .set_caption(f"<h2>{lifter}</h2>")
        )

        display(s)


def make_program(lifter, program, cycle=0):

    PROGRAM = StringIO(program)

    m = re.search(",(\d+)\+", program)
    if m:
        N = int(m.groups(0)[0])
    else:
        N = "off"

    program = pd.read_csv(PROGRAM)

    days = f"<h2>{lifter} cycle {cycle}</h2>"

    for lift in ["military", "deadlift", "bench", "squat"]:

        s = (
            compile(
                lifter=lifter, exercise=lift, lifts=lifts, program=program, cycle=cycle
            )
            .style.set_table_styles(
                [
                    {"selector": "thead", "props": [("display", "none")]},
                    {
                        "selector": "td",
                        "props": [("padding", "12px 35px"), ("font-size", "18px")],
                    },
                ]
            )
            .set_caption(f"<h2>{lift}</h2>")
        )

        days += s.to_html()

    html_s = f"<html> {days} </html>"

    fname = f"{lifter}-{N}.html"
    with open(fname, "w") as f:
        f.write(html_s)

    files.download(fname)


def plot_progression(lift, lifter):
    fig = go.Figure()

    train_slice = lifts.query(
        f"lift == '{lift}' and lifter == '{lifter}' and not is_max"
    )
    (latest_max,) = (
        lifts.query(f"lift == '{lift}' and lifter == '{lifter}' and is_max")
        .sort_values("date")
        .tail(1)["one_rep_max"]
    )

    x = train_slice.date
    y = train_slice.one_rep_max
    text = [
        f"{n:.0f} X {w:.1f} kg"
        for n, w in zip(train_slice["reps"], train_slice["weight"])
    ]

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            name=lifter,
            line_shape="hvh",
            line_width=5,
            opacity=0.8,
            text=text,
            marker_size=24,
            marker_line_width=6,
        )
    )

    fig.add_hline(
        y=latest_max, line_width=6, line_dash="dash", line_color="green", opacity=0.5
    )

    fig.update_layout(
        width=1000,
        title_text=f"{lifter} - {lift}",
        title_x=0.5,
        title_xanchor="center",
        title_font_color="crimson",
        title_font_size=28,
    ).show()


def make_program_ui():
    widgets = MyWidgets()

    def on_button_clicked(b):
        make_program(widgets.lifter.value, widgets.program.value, widgets.cycle.value)

    button = ipywidgets.Button(description="Download")
    button.on_click(on_button_clicked)

    who = ipywidgets.HBox([widgets.lifter, widgets.program, widgets.cycle])

    return ipywidgets.VBox([who, button])
