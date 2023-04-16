import pandas as pd
import fivethirtyone_db

from fivethirtyone_db import db, analysis, blog



def test_connection(capsys):

    with capsys.disabled():
        print("")
        print("- " * 50)
        print(fivethirtyone_db._credentials)
        print("- " * 50)


def test_worksets_fetch():
    """get all lifts"""

    records = db.Workset.all()


def test_Athlete(capsys):
    """get all lifts"""

    user = db.Athlete("camilla")

    with capsys.disabled():
        print("- " * 50)
        print(user)
        print("- " * 50)


def test_blog_next_lifts(capsys):

    new_cycle = {
        "cycle-index":"0",
        "rep-base":"5",
        "squat-max":"1",
        "bench-max":"10",
        "deadlift-max":"100",
        "military-max":"1000",
    }
    athlete = "test-athlete"

    for lift, athlete, weight, one_rm_max, base_reps, cycle in blog.next_lifts(new_cycle, athlete):
        with capsys.disabled():
            print(lift, athlete, weight, one_rm_max, base_reps, cycle)


def test_blog_make_pdf(capsys):
    ws = {'weight': 55.0, 'lift_name': 'deadlift', 'base_max': 68.99, 'base_reps': 3, 'cycle': 0}
    program = blog.worksets_to_program([ws], "test-athlete")
    with capsys.disabled():
        print(program)

    # (athlete, lift, train_max, program, cycle=cycle)


