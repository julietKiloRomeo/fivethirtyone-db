import pandas as pd
from io import StringIO
import os
import pathlib
import yaml
from flask import Flask, g

DB_FILE = pathlib.Path(__file__).parent / "531.sqlite"

def load_config(filename):
    with open(filename, "r") as file:
        return yaml.safe_load(file)

config_path = os.environ.get("PROGRAM_CONFIG", pathlib.Path(__file__).parent.parent / "program-config.yaml")
config = load_config(config_path)

SMALLEST_W_INC = config["smallest_w_inc"]

programs = {key: pd.DataFrame(value) for key, value in config["programs"].items()}
programs.update({key: value for key, value in zip([5, 3, 1, 0], programs.values())})
programs.update({key: value for key, value in zip(["5", "3", "1", "0"], programs.values())})

comments = config["comments"]
assistance = config["assistance"]
to_add_pr_cycle = config["to_add_pr_cycle"]



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
