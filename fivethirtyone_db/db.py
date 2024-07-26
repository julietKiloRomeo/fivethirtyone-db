"""
This module provides functionality for interacting with the database that stores athletes, lifts, and worksets.

It provides functions to add and update data, as well as fetch information about the athletes and their workout progress.

The module includes the following classes:
    - Athlete
    - Workset
    - Table

"""

import sqlite3
from contextlib import contextmanager
from werkzeug.security import generate_password_hash
from . import DB_FILE, config, analysis


@contextmanager
def db_connection():
    """
    Context manager for database connection.
    """
    try:
        connection = sqlite3.connect(DB_FILE)
        connection.row_factory = sqlite3.Row  # This allows us to access columns by name
        yield connection
    finally:
        connection.close()


def create_database():
    """
    Create a SQLite database and initialize tables.
    """
    Lift.create()
    Athlete.create()
    Workset.create()
        

class Table:
    """
    Base class for the Athlete and Workset classes.
    """
    __tablename__ = ""

    @classmethod
    def create(cls):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(cls.CREATE)
            conn.commit()

    @classmethod
    def list(cls):
        return [dict(row) for row in cls._fetchall(f"SELECT * FROM {cls.__tablename__}")]

    @staticmethod
    def _execute(sql):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()

    @staticmethod
    def _fetchall(sql):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def _fetchone(sql):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.fetchone()


class Lift(Table):
    __tablename__ = "lift"
    CREATE = """
CREATE TABLE IF NOT EXISTS lift (
  name TEXT NOT NULL PRIMARY KEY
);"""

    def __init__(self, name):
        self.name = name

    def add(self):
        insert_lift = f"INSERT INTO lift (name) VALUES ('{self.name}')"
        self._execute(insert_lift)


class Athlete(Table):
    __tablename__ = "athlete"
    CREATE = """
CREATE TABLE IF NOT EXISTS athlete (
  name TEXT NOT NULL PRIMARY KEY,
  password TEXT
);"""


    def __init__(self, name, worksets=None):
        self.name = name
        self.worksets = worksets if worksets is not None else self._load_worksets()

    def to_dict(self):
        return {
            "name":self.name,
            "worksets":self.worksets,
        }

    @classmethod
    def from_dict(cls, record):
        if record is None:
            return None
        return cls(**record)

    def _load_worksets(self):
        return [ dict(ws) for ws in self._fetchall(f"SELECT * FROM workset WHERE athlete_name='{self.name}'")]

    def add(self, password):
        insert_athlete = f"INSERT INTO athlete (name) VALUES ('{self.name}')"
        self._execute(insert_athlete)
        self._set_password(password)

    def _set_password(self, pwd):
        hsh = generate_password_hash(pwd)
        change = f"UPDATE {self.__tablename__} SET password='{hsh}' WHERE name='{self.name}'"
        self._execute(change)

    @staticmethod
    def _get_login(name):
        """
        Get the user details for a given athlete.

        Args:
            athlete (str): The name of the athlete.

        Returns:
            tuple: A tuple containing the name and hashed password of the athlete.
        """
        query = f"""
            SELECT password from athlete
            where name='{name}'
        """
        return Athlete._fetchone(query)["password"]


    def worksets_to_do(self):
        """
        Fetch the athlete's worksets that have not yet been completed.

        Returns:
            list[dict]: A list of worksets that have not yet been completed by the athlete.
        """
        return [ws for ws in self.worksets if ws["date"] is None]

    def latest_max(self, lift):
        """
        Get the latest max workset for a given lift and athlete.

        Args:
            lift (str): The name of the lift, e.g., "deadlift", "bench", "military", "squat".
            athlete (str): The name of the athlete.

        Returns:
            dict: A dictionary representing the latest max workset.
        """
        max_lifts = filter(lambda ws: ws["is_max"] and ws["lift_name"]==lift, self.worksets )
        try:
            return max(max_lifts, key=lambda ws: ws["date"])
        except ValueError:
            return {}


    def latest_cycle(self):
        """
        Get the latest cycle for a given athlete.

        Args:
            athlete (str): The name of the athlete.

        Returns:
            dict: A dictionary with keys cycle, base_reps, and base_max.
        """

        lifts = filter(lambda ws: ws["cycle"], self.worksets )
        lifts = filter(lambda ws: ws["date"], lifts )
        try:
            return max(lifts, key=lambda ws: ws["date"])
        except ValueError:
            return {}


    def estimate_next_cycle(self):
        """add a new cycle for an athlete"""

        # TODO: FIX THIS!
        # what is missing and who uses the old signature (blog.estimate_next_cycle)?

        latest_workset = self.latest_cycle()

        latest_max_set = {lift: self.latest_max(lift) for lift in config["lifts"]}
        latest_max_1rm = {
            lift: analysis.one_rm_fusion(ws["weight"], ws["reps"])
            for lift, ws in latest_max_set.items()
        }

        current_cycle = latest_workset.get("cycle", -1)
        current_base_reps = latest_workset.get("base_reps", 0)

        next_cycle = current_cycle + config["increments"][current_base_reps]["cycle_increment"]
        next_base_reps = config["increments"][current_base_reps]["next_base_reps"]

        return dict(
            next_cycle=next_cycle,
            next_base_reps=next_base_reps,
            **latest_max_1rm,
        )



class Workset(Table):
    __tablename__ = "workset"
    CREATE = """
CREATE TABLE IF NOT EXISTS workset (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  base_max REAL,
  base_reps INTEGER,
  cycle INTEGER,
  weight REAL,
  reps INTEGER,
  lift_name TEXT,
  athlete_name TEXT,
  date TEXT,
  is_max BOOLEAN,
  UNIQUE (lift_name, athlete_name, date)
);"""

    def __init__(self, base_max, base_reps, cycle, weight, lift_name, athlete_name, date=None, is_max=False, reps=None):
        self.base_max = base_max
        self.base_reps = base_reps
        self.cycle = cycle
        self.weight = weight
        self.lift_name = lift_name
        self.athlete_name = athlete_name
        self.date = date
        self.is_max = is_max
        self.reps = reps

    def add(self):
        # Handle None values correctly
        date_value = 'NULL' if self.date is None else f"'{self.date}'"
        reps_value = 'NULL' if self.reps is None else str(self.reps)

        insert_query = f"""
            INSERT INTO workset
            (lift_name, athlete_name, weight, base_max, base_reps, cycle, date, is_max, reps)
            VALUES ('{self.lift_name}', '{self.athlete_name}', {self.weight}, {self.base_max}, {self.base_reps}, {self.cycle}, {date_value}, {self.is_max}, {reps_value})
        """
        self._execute(insert_query)


    @staticmethod
    def update_row(wsid, date, lift_name, reps, weight, is_max):
        """
        Update a row in the workset table.

        Args:
            wsid (int): The ID of the workset to update.
            date (date): The new date for the workset.
            lift_name (str): The new lift name for the workset.
            reps (int, optional): The new number of repetitions for the workset. Defaults to None.
            weight (float, optional): The new weight for the workset. Defaults to None.
            is_max (bool)
        """
        change = f"""
            UPDATE workset
            SET date = '{date}', lift_name = '{lift_name}', reps = {reps if reps else "NULL"}, weight = {weight if weight else "NULL"}, is_max = {is_max}
            where id={wsid}
        """.replace(
            "''", "NULL"
        )
        Workset._execute(change)
    

    @classmethod
    def delete_by_id(cls, ws_id):
        """
        Delete a row in the workset table.

        Args:
            ws_id (int): The row ID for the workset table.
        """
        cls._execute(f"delete from workset where id={ws_id}")