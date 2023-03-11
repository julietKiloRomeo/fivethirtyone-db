import pandas as pd
from mysql.connector import connect
from contextlib import contextmanager


CREATE_LIFT = """CREATE TABLE lift (
  name varchar(31) NOT NULL PRIMARY KEY,
);"""

CREATE_ATHLETE = """CREATE TABLE athlete (
  name varchar(31) NOT NULL PRIMARY KEY,
);"""

CREATE_WORKSET = """CREATE TABLE workset (
  id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  weight float,
  reps int,
  lift_name varchar(31),
  athlete_name varchar(31),
  date date,
	UNIQUE KEY `uc_set` (`lift_name`, `athlete_name`, `date`),
  KEY lift_name_idx (lift_name),
  KEY athlete_name_idx (athlete_name)
);"""


@contextmanager
def db_connection():
    """
    Examples:

      with db_connection() ass conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lift;")
        result = cursor.fetchall()
        for row in result:
          print(row)

      with db_connection() ass conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO lift (name) VALUES ('curl');")
        conn.commit()
    """
    try:
        with connect(
            host=os.getenv("HOST"),
            user=os.getenv("USERNAME"),
            password=os.getenv("PASSWORD"),
            database=os.getenv("DATABASE"),
        ) as connection:
            yield connection
    except Error as e:
        print(e)


# csv into DB
def import_csv_into_db(csv_path="drive/MyDrive/lifts.csv"):
    """import csv directly into worksets

        csv must be in the following format:
    lifter	date	lift	weight	reps	is_max
    irka	2022-09-13	deadlift	80	3	TRUE
    irka	2022-09-13	military	50	5	TRUE
    jikr	2022-09-13	deadlift	100	6	TRUE
    jikr	2022-09-13	military	40	5	TRUE

        existing data are deleted!

    """

    df = pd.read_csv(csv_path)

    name_map = {
        "irka": "irfan",
        "cam": "camilla",
        "jikr": "jimmy",
        "alvi": "alvilde",
    }

    df = df.assign(db_name=[name_map[n] for n in df["lifter"]]).query(
        "not lifter=='alvi'"
    )
    recs = [(*prec, int(reps), name) for _, _, *prec, reps, _, name in df.to_records()]

    insert_worksets = """
      INSERT INTO workset
      (date, lift_name, weight, reps, athlete_name)
      VALUES ( %s, %s, %s, %s, %s )"""

    with db_connection() as conn:
        cursor = conn.cursor()
        # delete everything
        cursor.execute("delete from workset")
        conn.commit()
        # add csv records instead
        cursor.executemany(insert_worksets, recs)
        conn.commit()


def all_sets(athlete):
    show_table_query = f"SELECT * FROM workset where athlete_name='{athlete}'"
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(show_table_query)
        # Fetch rows from last executed query
        result = cursor.fetchall()
        for row in result:
            print(row)

def delete_workset_by_id(ws_id):
    with db_connection() as conn:
        cursor = conn.cursor()
        # delete everything
        cursor.execute(f"delete from workset where id={ws_id}")
        conn.commit()


def insert_record(lift, athlete, date, reps, weight):
    """
    lift (str): in ["deadlift", "bench", "military", "squat"]
    athlete (str): name of athlete
    date (str): (YYYY-MM-DD)
    reps (int):
    weight (float):
    """

    insert_workset = f"""
  INSERT INTO workset
  (lift_name, athlete_name, date, reps, weight)
  VALUES ( '{lift}', '{athlete}', '{date}', {reps}, {weight} )
  """

    with db_connection() as conn:
        cursor = conn.cursor()
        # add csv records instead
        cursor.execute(insert_workset)
        conn.commit()
