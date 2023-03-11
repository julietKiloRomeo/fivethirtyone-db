import ipywidgets
import datetime
import datetime as dt
import numpy as np
import pandas as pd
import panel as pn
import re

import pandas as pd
from io import StringIO
import plotly.express as px

from jinja2 import Environment, BaseLoader
from itertools import product
from IPython.display import HTML

import plotly.graph_objects as go
import numpy as np

from ipywidgets import interactive, Dropdown
import numpy as np
import plotly.graph_objects as go

from google.colab import files
from bokeh.models.widgets.tables import NumberFormatter, BooleanFormatter


pn.extension("tabulator")


# from google.colab import drive
# drive.mount('/content/drive')


#!pip install python-dotenv mysql-connector-python

# from dotenv import load_dotenv
# load_dotenv("drive/MyDrive/vars.env")
import os

from mysql.connector import connect, Error

from contextlib import contextmanager


def one_rm_brzycki(weight, reps):
    """calculate 1rm max from several reps
    of a submaximal weight

    https://www.athlegan.com/calculate-1rm

    """
    return weight * 36 / (37 - reps)


def one_rm_lombardi(weight, reps):
    """calculate 1rm max from several reps
    of a submaximal weight

    https://www.athlegan.com/calculate-1rm

    """
    return weight * reps**0.1


def one_rm_fusion(weight, reps):
    """calculate 1rm max from several reps
    of a submaximal weight

    https://www.athlegan.com/calculate-1rm

    """
    return 0.5 * (one_rm_lombardi(weight, reps) + one_rm_brzycki(weight, reps))


def iso_brzycki(w_1):
    """
    return reps and weights for a specific 1rm max

    """
    n = np.linspace(1, 15, 100)

    return n, (37 - n) * w_1 / 36


def iso_fusion(w_1):
    """
    return reps and weights for a specific 1rm max

    """
    n = np.linspace(1, 15, 100)

    return n, 2 * w_1 / (n**0.1 + 36 / (37 - n))


def compile(lifter, exercise, lifts, program, cycle=0):
    """given previous lifts and a base-program
    calculate a program for a specific lifter and
    exercise
    """
    train_max = (
        lifts.query(f'lifter == "{lifter}" and lift == "{exercise}" and is_max')
        .sort_values("date")
        .iloc[-1]["train_max"]
    )
    train_max += to_add_pr_cycle[exercise] * cycle

    weight = (
        ((program["pct"] / 100 * train_max) // SMALLEST_W_INC) * SMALLEST_W_INC
    ).astype(int)
    to_lift = program.assign(weight=weight)[["reps", "weight"]].T
    to_lift.name = lifter
    
    return to_lift


