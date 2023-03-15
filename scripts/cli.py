#!/usr/bin/python
import fivethirtyone_db
from fivethirtyone_db import db
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

    _, ws = db.all_sets(athlete=athlete)
    for ws_id, weight, reps, lift, name, date, is_max in ws:
        print(f"{ws_id:5.0f} {date:%d %b} {name:>10s} {lift:10s} {reps:2.0f} x {weight:4.1f} kg")



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


if __name__ == "__main__":
    cli()
    