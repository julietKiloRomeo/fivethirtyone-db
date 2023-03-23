import pandas as pd
import fivethirtyone_db

from fivethirtyone_db import db, analysis


def test_connection(capsys):

    with capsys.disabled():
        print("")
        print("- "*50)
        print(fivethirtyone_db._credentials)
        print("- "*50)

def test_worksets_fetch():
    """get all lifts"""

    records = db.all_sets()


def test_get_user(capsys):
    """get all lifts"""
    
    user = db.get_user("camilla")

    with capsys.disabled():
        print("- "*50)
        print(user)
        print("- "*50)
