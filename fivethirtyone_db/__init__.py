import pandas as pd
from io import StringIO
import os
import pathlib
import yaml

with pathlib.Path("/home/jkr/projects/fivethirtyone-db/vars.yaml").open("r") as f:
    _credentials = yaml.load(f, Loader=yaml.FullLoader)

if _credentials["host"] == "localhost":
    print(_credentials)
    raise Exception("DB not configured!")
if _credentials["host"] is None:
    print(_credentials)
    raise Exception("DB not configured!")

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
    five = pd.read_csv(StringIO(csv_program_5)),
    three = pd.read_csv(StringIO(csv_program_3)),
    one = pd.read_csv(StringIO(csv_program_1)),
    off = pd.read_csv(StringIO(csv_program_off)),
)

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



def create_app(test_config=None):
    from . import db
    from . import auth

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import blog, api
    app.register_blueprint(blog.bp)
    app.register_blueprint(api.bp)
    app.add_url_rule('/', endpoint='index')

    app.register_blueprint(auth.bp)

    return app