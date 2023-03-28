from fivethirtyone_db import create_app

# run with gunicorn --bind 0.0.0.0:5000 -w 2 wsgi:app 
app = create_app()