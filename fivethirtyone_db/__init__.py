import pandas as pd
from io import StringIO
import os
import pathlib
import yaml


csv_program_5 = """
pct,reps
40,5
50,5
60,3
65,5
75,5
85,5+
"""

csv_program_3 = """
pct,reps
40,5
50,5
60,3
70,3
80,3
90,3+
"""

csv_program_1 = """
pct,reps
40,5
50,5
60,3
75,5
85,3
95,1+
"""

csv_program_off = """
pct,reps
40,5
50,5
40,5
"""

SMALLEST_W_INC = 2.5

programs = dict(
    five=pd.read_csv(StringIO(csv_program_5)),
    three=pd.read_csv(StringIO(csv_program_3)),
    one=pd.read_csv(StringIO(csv_program_1)),
    off=pd.read_csv(StringIO(csv_program_off)),
)
programs[5] = programs["five"]
programs[3] = programs["three"]
programs[1] = programs["one"]
programs[0] = programs["off"]
programs["5"] = programs["five"]
programs["3"] = programs["three"]
programs["1"] = programs["one"]
programs["0"] = programs["off"]


comments = dict(
    squat="rack @ 17, safetybar @ 3",
    military="rack @ 16, dips @ 9",
)

assistance = dict(
    bench="dips / chins",
    squat="one-leg-squat / ab-wheel",
    military="dips / chins",
    deadlift="ham raise / leg raise",
)


to_add_pr_cycle = dict(
    deadlift=5,
    squat=5,
    bench=2.5,
    military=2.5,
)


import os
from flask import Flask, g

try:
    with pathlib.Path("vars.yaml").open("r") as f:
        _credentials = yaml.load(f, Loader=yaml.FullLoader)
except:
    _credentials = {}


def create_app(db_credentials=None):

    if not db_credentials is None:
        _credentials.update(**db_credentials)

    from . import db
    from . import auth

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import blog, api

    app.register_blueprint(blog.bp)
    app.register_blueprint(api.bp)
    app.add_url_rule("/", endpoint="index")

    app.register_blueprint(auth.bp)

    return app
