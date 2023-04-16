"""
This module provides functionality for interacting with the database that stores athletes, lifts, and worksets.

It provides functions to add and update data, as well as fetch information about the athletes and their workout progress.

The module includes the following classes:
    - Athlete
    - Workset
    - Table

"""

import pandas as pd
from mysql.connector import connect, Error
from . import _credentials
from contextlib import contextmanager
from werkzeug.security import check_password_hash, generate_password_hash


# SQL table creation queries
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
    Context manager for database connection.

    This function returns a context manager that can be used to manage connections to the database.
    It yields the connection object and takes care of closing the connection when exiting the context.

    Examples:

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lift;")
            result = cursor.fetchall()
            for row in result:
                print(row)

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO lift (name) VALUES ('curl');")
            conn.commit()
    """
    try:
        with connect(**_credentials) as connection:
            yield connection
    except Error as e:
        raise


class Table:
    """
    Base class for the Athlete and Workset classes.

    This class provides common functionality for working with tables in the database.
    """

    CREATE = ""
    __tablename__ = ""

    @classmethod
    def create(cls):
        """
        Create the table in the database.

        This method creates a table in the database using the CREATE statement defined in the class.
        """
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(cls.CREATE)
            conn.commit()

    @staticmethod
    def _execute(sql):
        """
        Execute a SQL query.

        Args:
            sql (str): The SQL query to execute.
        """
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()

    @staticmethod
    def _fetchall(sql):
        """
        Fetch all records from a SQL query.

        Args:
            sql (str): The SQL query to execute.

        Returns:
            list[dict]: A list of records returned by the query.
        """
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return [
                {key: val for key, val in zip(cursor.column_names, record)}
                for record in cursor.fetchall()
            ]

    @staticmethod
    def _fetchone(sql):
        """
        Fetch one record from a SQL query.

        Args:
            sql (str): The SQL query to execute.

        Returns:
            dict: A dictionary representing the record returned by the query.
        """
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            record = cursor.fetchone()
            return {key: val for key, val in zip(cursor.column_names, record)}


class Athlete(Table):
    """
    Class representing an athlete in the database.

    This class provides methods for adding an athlete to the database, setting their password, and fetching their worksets.
    """

    __tablename__ = "athlete"

    CREATE = """CREATE TABLE athlete (
    name varchar(31) NOT NULL PRIMARY KEY,
    password varchar(120),
    );"""

    def __init__(self, name, password=None):
        """
        Initialize an Athlete object.

        Args:
            name (str): The name of the athlete.
            password (str, optional): The athlete's password. Defaults to None.
        """
        self.name = name
        self.password = password
        self.worksets = []
        self._load_worksets()
        self.pwd_hash = self._get_login()

    def _get_login(self):
        """
        Get the user details for a given athlete.

        Args:
            athlete (str): The name of the athlete.

        Returns:
            tuple: A tuple containing the name and hashed password of the athlete.
        """
        query = f"""
            SELECT password from athlete
            where name='{self.name}'
        """
        return self._fetchone(query)["password"]

    def add(self):
        """
        Add the athlete to the database.

        This method inserts the athlete's name and password into the athlete table.
        """
        insert_athlete = f"""
    INSERT INTO athlete
    (name)
    VALUES ( '{self.name}')
    """
        self._execute(insert_athlete)
        self._set_password(self.password)

    def _set_password(self, pwd):
        """
        Set the athlete's password in the database.

        Args:
            pwd (str): The athlete's password.
        """
        hsh = generate_password_hash(pwd)
        change = f"""
            UPDATE {self.__tablename__}
            SET password='{hsh}'
            where name='{self.name}'
        """
        self._execute(change)

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


    def _load_worksets(self):
        self.worksets = self._fetchall(f"SELECT * FROM workset where athlete_name='{self.name}'")


class Workset(Table):
    """
    Class representing a workset in the database.

    This class provides methods for adding and updating worksets in the database.
    """

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
        """
        Initialize a Workset object.

        Args:
            base_max (float): The base maximum weight for the workset.
            base_reps (int): The base number of repetitions for the workset.
            cycle (int): The cycle number for the workset.
            weight (float): The weight for the workset.
            lift_name (str): The name of the lift for the workset.
            athlete_name (str): The name of the athlete performing the workset.
            date (date, optional): The date of the workset. Defaults to None.
            is_max (bool, optional): Whether the workset is a max attempt. Defaults to False.
            reps (int, optional): The number of repetitions for the workset. Defaults to None.
        """
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
        """
        Fetch a workset from the database by its ID.

        Args:
            wsid (int): The ID of the workset.

        Returns:
            dict: A dictionary representing the workset.
        """
        record = Workset._fetchone(f"select * from workset where id={wsid}")
        return record

    def add(self):
        """
        Add the workset to the database.

        This method inserts the workset's data into the workset table.
        """
        insert_workset = f"""
    INSERT INTO workset
    (lift_name, athlete_name, weight, base_max, base_reps, cycle, date, is_max, reps)
    VALUES ( '{self.lift_name}', '{self.athlete_name}', {self.weight}, {self.base_max}, {self.base_reps}, {self.cycle}, {self.date}, {self.is_max}, {self.reps})
    """
        self._execute(insert_workset)

    @staticmethod
    def update_row(wsid, date, lift_name, reps, weight):
        """
        Update a row in the workset table.

        Args:
            wsid (int): The ID of the workset to update.
            date (date): The new date for the workset.
            lift_name (str): The new lift name for the workset.
            reps (int, optional): The new number of repetitions for the workset. Defaults to None.
            weight (float, optional): The new weight for the workset. Defaults to None.
        """
        change = f"""
            UPDATE workset
            SET date = '{date}', lift_name = '{lift_name}', reps = {reps if reps else "NULL"}, weight = {weight if weight else "NULL"}
            where id={wsid}
        """.replace(
            "''", "NULL"
        )
        Workset._execute(change)
    
    @staticmethod
    def all():
        return Workset._fetchall("SELECT * FROM workset")

    @classmethod
    def delete_by_id(cls, ws_id):
        """
        Delete a row in the workset table.

        Args:
            ws_id (int): The row ID for the workset table.
        """
        cls._execute(f"delete from workset where id={ws_id}")









