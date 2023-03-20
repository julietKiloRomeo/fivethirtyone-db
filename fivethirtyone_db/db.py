import pandas as pd
from mysql.connector import connect, Error
from . import _credentials
from contextlib import contextmanager



CREATE_LIFT = """CREATE TABLE lift (
  name varchar(31) NOT NULL PRIMARY KEY,
);"""

CREATE_ATHLETE = """CREATE TABLE athlete (
  name varchar(31) NOT NULL PRIMARY KEY,
);"""

CREATE_WORKSET = """CREATE TABLE workset (
  id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
  base_max float,
  base_reps int,
  cycle int,
  weight float,
  reps int,
  lift_name varchar(31),
  athlete_name varchar(31),
  date date,
  is_max boolean,
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
        with connect(**_credentials) as connection:
            yield connection
    except Error as e:
#        print(e)
        raise

# csv into DB
def import_csv_into_db(csv_path="lifts.csv"):
    """import csv directly into worksets

        csv must be in the following format:
    lifter	date	lift	weight	reps	is_max
    irka	2022-09-13	deadlift	80	3	TRUE
    irka	2022-09-13	military	50	5	TRUE
    jikr	2022-09-13	deadlift	100	6	TRUE
    jikr	2022-09-13	military	40	5	TRUE

        existing data are deleted!

    """
    print(_credentials)
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
    recs = [(*prec, int(reps), bool(is_max), name) for _, _, *prec, reps, is_max, name in df.to_records()]

    insert_worksets = """
      INSERT INTO workset
      (date, lift_name, weight, reps, is_max, athlete_name)
      VALUES ( %s, %s, %s, %s, %s, %s )"""

    with db_connection() as conn:
        cursor = conn.cursor()
        # delete everything
        cursor.execute("delete from workset")
        conn.commit()
        # add csv records instead
        cursor.executemany(insert_worksets, recs)
        conn.commit()


def all_sets(athlete=None):
    """return all rows in the workset table

    Args:
        athlete (str): optional name of athlete

    Returns:
        (tuple[str]), list[tuple]): column names, row-records (ws_id, weight, reps, lift, name, date, is_max)
    """
    if athlete:
        show_table_query = f"SELECT * FROM workset where athlete_name='{athlete}'"
    else:
        show_table_query = f"SELECT * FROM workset"

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(show_table_query)
        # Fetch rows from last executed query
        return [
          {key:val for key, val in zip(cursor.column_names, record)} for record in cursor.fetchall()
        ]

def delete_workset_by_id(ws_id):
    """delete a row in the workset table

    Args:
        ws_id (int): row id for the workset table
    """
    with db_connection() as conn:
        cursor = conn.cursor()
        # delete everything
        cursor.execute(f"delete from workset where id={ws_id}")
        conn.commit()


def insert_record(lift, athlete, weight, base_max, base_reps, cycle):
    """
    lift (str): in ["deadlift", "bench", "military", "squat"]
    athlete (str): name of athlete
    weight (float):
    base_max (float):
    base_reps (int):
    cycle (int):
    """


    insert_workset = f"""
  INSERT INTO workset
  (lift_name, athlete_name, weight, base_max, base_reps, cycle)
  VALUES ( '{lift}', '{athlete}', {weight}, {base_max}, {base_reps}, {cycle})
  """

    with db_connection() as conn:
        cursor = conn.cursor()
        # add csv records instead
        cursor.execute(insert_workset)
        conn.commit()


def latest_max(lift, athlete):
    """
    lift (str): in ["deadlift", "bench", "military", "squat"]
    athlete (str): name of athlete

    Returns:
        list[dict] : [{'weight': 32.5, 'reps': 5, 'date': datetime.date(2023, 3, 6), 'athlete_name': 'camilla', 'lift_name': 'bench'}]
    """

    query = f"""SELECT weight, reps, date, athlete_name, lift_name FROM workset
    where athlete_name='{athlete}' and
    lift_name='{lift}' and is_max
    order by date desc limit 1"""

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return [
          {key:val for key, val in zip(cursor.column_names, record)} for record in cursor.fetchall()
        ]

def latest_cycle(athlete):
    """
    athlete (str): name of athlete

    Returns:
        int or None
    """

    query = f"""SELECT cycle, date, athlete_name FROM workset
    where athlete_name='{athlete}'
    and cycle IS NOT NULL
    order by date desc limit 1"""

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        records = [
          {key:val for key, val in zip(cursor.column_names, record)} for record in cursor.fetchall()
        ]
      
    if len(records):
      return records[0]["cycle"]
    return None
