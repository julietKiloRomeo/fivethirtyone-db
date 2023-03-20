#!/usr/bin/python
import fivethirtyone_db
from fivethirtyone_db import db, analysis
import click
from datetime import date

@click.group()
def cli():
  pass

@cli.command(name='reset', help="delete all rows and insert new from csv")
def reset():
    db.import_csv_into_db(csv_path="lifts.csv")

@cli.command(name='list', help="print all worksets")
@click.option('-a', '--athlete')
def list(athlete):
    for record in db.all_sets(athlete=athlete):
#        print(record)
        if record['reps']:
            print(f"{record['id']:5.0f} {record['date']:%d %b} {record['athlete_name']:>10s} {record['lift_name']:10s} {record['reps']:2.0f} x {record['weight']:4.1f} kg")
        else:
            print(f"{record['id']:5.0f}        {record['athlete_name']:>10s} {record['lift_name']:10s} {record['base_reps']}+ x {record['weight']:4.1f} kg")


@cli.command(name='delete', help="delete a specific workset from DB")
@click.option('--id', required=True)
def delete_workset_by_id(id):
    db.delete_workset_by_id(id)

@cli.command(name='add', help="insert new workset in DB")
@click.option('--lift', required=True, prompt=True, type=click.Choice(['bench', 'military', 'squat', 'deadlift'], case_sensitive=False))
@click.option('--athlete', required=True, prompt=True, type=click.Choice(['camilla', 'irfan', 'jimmy', 'christina'], case_sensitive=False))
@click.option('--date', type=click.DateTime(formats=["%Y-%m-%d"]),  default=str(date.today()))
@click.option('--reps', required=True, prompt=True, type=int)
@click.option('--weight', required=True, prompt=True, type=float)
def insert_record(lift, athlete, date, reps, weight):
    db.insert_record(lift, athlete, date, reps, weight)


@cli.command(name='test')
def test():

    change = f"""
        UPDATE workset
        SET cycle=2
        where id=292
    """

    with db.db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(change)
        conn.commit()

@cli.command(name='add_cycle')
@click.option('--athlete', required=True, prompt=True, type=click.Choice(['camilla', 'irfan', 'jimmy', 'christina'], case_sensitive=False))
@click.option('--cycle', type=int)
@click.option('--rep-base', type=click.Choice(['five', 'three', 'one', 'off']))
def add_cycle(athlete, cycle, rep_base):
    """ add a new cycle for an athlete
    """
    get_latest_cycle = cycle is None
    if get_latest_cycle:
        latest = db.latest_cycle(athlete)
        if latest:
            cycle = latest + 1
            print(f"incrementing cycle from {latest} to {cycle} (use --cycle n to override)")

    LIFTS = ["military", "deadlift", "bench", "squat"]
    program = fivethirtyone_db.programs[rep_base]

    for lift in LIFTS:
        repmax = db.latest_max(lift, athlete)[0]
        one_rm_max = analysis.one_rm_fusion(repmax['weight'], repmax['reps'])
        train_max = 0.9*one_rm_max
        to_lift = analysis.compile(athlete, lift, train_max, program, cycle=0)
        base_reps = to_lift[4]["reps"]
        weight = to_lift[5]["weight"]
        db.insert_record(lift, athlete, weight, one_rm_max, base_reps, cycle)
        



if __name__ == "__main__":
    cli()
    