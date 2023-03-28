import pandas as pd
from mysql.connector import connect, Error
from . import _credentials
from contextlib import contextmanager
from werkzeug.security import check_password_hash, generate_password_hash


CREATE_LIFT = """CREATE TABLE lift (
  name varchar(31) NOT NULL PRIMARY KEY,
);"""

CREATE_ATHLETE = """CREATE TABLE athlete (
  name varchar(31) NOT NULL PRIMARY KEY,
  password varchar(120),
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


class Table:

    CREATE = ""
    __tablename__ = ""

    @classmethod
    def create(cls):
        with db_connection() as conn:
            cursor = conn.cursor()
            # delete everything
            cursor.execute(cls.CREATE)
            conn.commit()

    @staticmethod
    def _execute(sql):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()

    @staticmethod
    def _fetchall(sql):
        """fetch as records"""
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return [
                {key: val for key, val in zip(cursor.column_names, record)}
                for record in cursor.fetchall()
            ]

    @staticmethod
    def _fetchone(sql):
        """fetch as records"""
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            record = cursor.fetchone()
            return {key: val for key, val in zip(cursor.column_names, record)}


class Athlete(Table):

    __tablename__ = "athlete"

    CREATE = """CREATE TABLE athlete (
    name varchar(31) NOT NULL PRIMARY KEY,
    password varchar(120),
    );"""

    def __init__(self, name, password=None):
        self.name = name
        self.password = password

    def add(self):
        insert_athlete = f"""
    INSERT INTO athlete
    (name)
    VALUES ( '{self.name}')
    """
        self._execute(insert_athlete)
        self._set_password(self.password)

    def _set_password(self, pwd):

        hsh = generate_password_hash(pwd)
        change = f"""
            UPDATE {self.__tablename__}
            SET password='{hsh}'
            where name='{self.name}'
        """
        self._execute(change)

    def worksets_to_do(self):

        query = f"""SELECT * FROM workset
        where athlete_name='{self.name}'
        and date IS NULL"""
        return self._fetchall(query)


class Workset(Table):

    __tablename__ = "workset"

    CREATE = """CREATE TABLE workset (
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

    def __init__(
        self,
        base_max,
        base_reps,
        cycle,
        weight,
        lift_name,
        athlete_name,
        date=None,
        is_max=False,
        reps=None,
    ):
        self.wsid = None
        self.base_max = base_max
        self.base_reps = base_reps
        self.cycle = cycle
        self.weight = weight
        self.lift_name = lift_name
        self.athlete_name = athlete_name
        self.date = date
        self.is_max = is_max
        self.reps = reps

    @staticmethod
    def fetch(wsid):

        record = Workset._fetchone(f"select * from workset where id={wsid}")
        return record

    def add(self):
        insert_workset = f"""
    INSERT INTO workset
    (lift_name, athlete_name, weight, base_max, base_reps, cycle, date, is_max, reps)
    VALUES ( '{self.lift_name}', '{self.athlete_name}', {self.weight}, {self.base_max}, {self.base_reps}, {self.cycle}, {self.date}, {self.is_max}, {self.reps})
    """
        self._execute(insert_workset)

    @staticmethod
    def update_row(wsid, date, lift_name, reps, weight):
        """update key-value pairs - keys must be in columns!"""
        change = f"""
            UPDATE workset
            SET date = '{date}', lift_name = '{lift_name}', reps = {reps if reps else "NULL"}, weight = {weight if weight else "NULL"}
            where id={wsid}
        """.replace(
            "''", "NULL"
        )
        Workset._execute(change)


def all_sets(athlete=None):
    """return all rows in the workset table

    Args:
        athlete (str): optional name of athlete

    Returns:
        list[dict] : rows in workset table as records
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
            {key: val for key, val in zip(cursor.column_names, record)}
            for record in cursor.fetchall()
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


def insert_record(lift, athlete, weight, base_max, base_reps, cycle, is_max="false"):
    """
    lift (str): in ["deadlift", "bench", "military", "squat"]
    athlete (str): name of athlete
    weight (float):
    base_max (float):
    base_reps (int):
    cycle (int):
    is_max (bool=False):
    """

    insert_workset = f"""
  INSERT INTO workset
  (lift_name, athlete_name, weight, base_max, base_reps, cycle, is_max)
  VALUES ( '{lift}', '{athlete}', {weight}, {base_max}, {base_reps}, {cycle}, {is_max})
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
        return {key: val for key, val in zip(cursor.column_names, cursor.fetchone())}


def latest_cycle(athlete):
    """
    athlete (str): name of athlete

    Returns:
        dict : with keys cycle, base_reps and base_max
    """

    query = f"""SELECT cycle, base_reps, base_max FROM workset
    where athlete_name='{athlete}'
    and cycle IS NOT NULL
    order by date desc limit 1"""

    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return {key: val for key, val in zip(cursor.column_names, cursor.fetchone())}


def set_password(athlete, pwd):
    change = f"""
        UPDATE athlete
        SET password='{generate_password_hash(pwd)}'
        where name='{athlete}'
    """
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(change)
        conn.commit()


def get_user(athlete):
    """
    Returns:
        str, str : name, hashed-password
    """

    query = f"""
        SELECT name, password from athlete
        where name='{athlete}'
    """
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchone()
