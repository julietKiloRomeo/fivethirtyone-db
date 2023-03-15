from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    """
    https://flask.palletsprojects.com/en/2.2.x/quickstart/
    """

    return "<p>Hello, World!</p>"