import pandas as pd
from io import StringIO
import os
from dotenv import load_dotenv
import pathlib


print(pathlib.Path(__file__).parent.parent / "vars.env")
load_dotenv(pathlib.Path(__file__).parent.parent / "vars.env")

_credentials = dict(
    host=os.getenv("HOST"),
    user=os.getenv("USERNAME"),
    password=os.getenv("PASSWORD"),
    database=os.getenv("DATABASE"),
)

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
