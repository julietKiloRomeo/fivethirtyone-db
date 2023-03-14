import fivethirtyone_db
from fivethirtyone_db import db
#!/usr/bin/python

import click


@click.group()
def cli():
  pass

@cli.command(name='rm')
def rm():
    db.import_csv_into_db(csv_path="lifts.csv")

@cli.command(name='ls')
@click.option('-a', '--athlete')
def ls(athlete):

    _, ws = db.all_sets(athlete=athlete)
    for w in ws:
        print(w)

if __name__ == "__main__":
    cli()
    