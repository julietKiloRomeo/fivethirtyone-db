# fivethirtyone-db

```
 > poetry install
 > fto ls -a camilla
 > nox -s tests
```

poetry run flask --app fivethirtyone_db run --debug

We got to https://flask.palletsprojects.com/en/2.2.x/tutorial/views/
https://docs.digitalocean.com/tutorials/app-deploy-flask-app/

```
 > poetry shell
 > flask --app fivethirtyone_db run --debug
```

```
 > fto set-pwd --athlete jimmy --password xxxx
```


then go to `http://127.0.0.1:5000`

To run with production DB and gunicorn do:

```
DBHOST=eu-central.connect.psdb.cloud DBUSERNAME=xxx DBPASSWORD=xxx DATABASE=hobby-app-data gunicorn --bind 0.0.0.0:5000 -w 2 wsgi:app
```
look in vars.env for credentials