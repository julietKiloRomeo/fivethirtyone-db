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
    return 1
    # gett all lifts
    cols, ws = db.all_sets()

    lifts = pd.DataFrame( ws, columns=cols)
    lifts['date']= pd.to_datetime(lifts['date'])
    lifts = lifts.assign(one_rep_max = analysis.one_rm_fusion(lifts.weight, lifts.reps))
    lifts = lifts.assign(
        train_max = lifts.one_rep_max*0.9,
    )
    lifts["is_max"] = True