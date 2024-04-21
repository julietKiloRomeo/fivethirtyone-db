#!/usr/bin/python
from fivethirtyone_db import db
import click
import json
import datetime
import pathlib


@click.group()
def cli():
    pass


@cli.command(name="list", help="print all worksets")
@click.option("-a", "--athlete")
@click.option(
    "-r",
    "--raw",
    is_flag=True,
    show_default=True,
    default=False,
    help="show raw record",
)
def list(athlete, raw):
    athlete = db.Athlete(name=athlete)

    for record in athlete.worksets:
        if raw:
            print(record)
            continue
        if record["reps"]:
            print(
                f"{record['id']:5.0f} {record['date']:%d %b} {record['athlete_name']:>10s} {record['lift_name']:10s} {record['reps']:2.0f} x {record['weight']:4.1f} kg"
            )
        else:
            print(
                f"{record['id']:5.0f}        {record['athlete_name']:>10s} {record['lift_name']:10s} {record['base_reps']}+ x {record['weight']:4.1f} kg"
            )


@cli.command(name="delete", help="delete a specific workset from DB")
@click.option("--id", required=True)
def delete_workset_by_id(id):
    db.Workset.delete_by_id(id)


@cli.command(name="test")
def test():

    print("hello!")


@cli.command(name="add-reps")
@click.option(
    "--athlete",
    required=True,
    prompt=True,
    type=click.Choice(["camilla", "irfan", "jimmy", "christina"], case_sensitive=False),
)
@click.option(
    "--lift",
    required=True,
    prompt=True,
    type=click.Choice(["bench", "military", "squat", "deadlift"], case_sensitive=False),
)
def add_reps(athlete, lift):
    """update reps and date on a planned workset"""

    query = f"""SELECT id, weight, reps, date, athlete_name, lift_name FROM workset
    where athlete_name='{athlete}' and
    lift_name='{lift}' and reps IS NULL"""

    with db.db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        ws_id, weight, *_ = cursor.fetchall()[0]
        print(f"How many reps at {weight:.1f} kg?")


@cli.command(name="set-pwd", help="set password for user")
@click.option("--athlete", required=True)
@click.option("--password", required=True)
def set_pwd(athlete, password):
    db.Athlete(athlete)._set_password(password)


@cli.command(name="check-pwd", help="set password for user")
@click.option("--athlete", required=True)
@click.option("--password", required=True)
def check_pwd(athlete, password):
    from werkzeug.security import check_password_hash, generate_password_hash

    athlete = db.Athlete(athlete)

    if check_password_hash(athlete.pwd_hsh, password):
        print("OK")
    else:
        print("NO!")


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


@cli.command(name="export", help="dump db to records")
def export():

    export_folder = pathlib.Path("db-dump") / f"{datetime.date.today()}"
    export_folder.mkdir(exist_ok=True)

    with db.db_connection() as conn:
        cursor = conn.cursor()

        # Getting all the table names
        cursor.execute("SHOW TABLES;")
        table_names = [tname for tname, in cursor.fetchall()]

        for tname in table_names:
            sql = f"select * from {tname}"
            cursor.execute(sql)
            records = [
                {key: val for key, val in zip(cursor.column_names, record)}
                for record in cursor.fetchall()
            ]

            with (export_folder / f"{tname}.json").open("w") as f:
                json.dump(records, f, default=default)


@cli.command(name="import", help="init db from records")
@click.option("--backupdate", required=True)
def import_records(backupdate):

    # first load all data
    export_folder = pathlib.Path("db-dump") / backupdate

    to_insert = {}
    for pth in export_folder.glob("*.json"):
        table_name = pth.stem
        with pth.open("r") as f:
            to_insert[table_name] = json.load(f)

    # now delete all db rows and insert the new ones
    with db.db_connection() as conn:
        cursor = conn.cursor()

        for table_name, records in to_insert.items():
            if not records:
                continue  # Skip if there are no records to insert for this table
            
            col_names = ", ".join(records[0].keys())
            placeholders = ", ".join("?" * len(records[0]))  # Use '?' for each column value

            # delete everything from the table
            cursor.execute(f"DELETE FROM {table_name}")
            conn.commit()

            # prepare the SQL statement for inserting new records
            sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
            
            # convert each dictionary to a tuple of values
            values = [tuple(record[col] for col in record) for record in records]
            
            # execute the SQL command to insert all records
            cursor.executemany(sql, values)
            conn.commit()



if __name__ == "__main__":
    cli()
