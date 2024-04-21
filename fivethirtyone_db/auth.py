import functools
from datetime import datetime
from . import db

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """render login form on GET or validate form
    on POST
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        if not check_password_hash(db.Athlete._get_login(username), password):
            error = f"Incorrect password."

        if error is None:
            session.clear()
            athlete = db.Athlete(username)
            session["user_dict"] = athlete.to_dict()
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    """checks if a user id is stored in the session and
    gets that user’s data from the database, storing it
    on g.user, which lasts for the length of the
    request. If there is no user id, or if the id
    doesn’t exist, g.user will be None.

    bp.before_app_request() registers a function that runs
    before the view function, no matter what URL is requested.
    """
    user_dict = session.get("user_dict")
    g.user = None

    if user_dict is None:
        return

    for ws in user_dict.get("worksets"):
        date_str = ws["date"]
        if date_str is None:
            continue
        
        mysql_format = '%a, %d %b %Y %H:%M:%S %Z'
        sqlite_format = "%Y-%m-%d"
        if ":" in date_str:
            format_to_use = mysql_format
        else:
            format_to_use = sqlite_format

        ws["date"] = datetime.strptime(date_str, format_to_use).date() if date_str else None

    g.user = db.Athlete.from_dict(user_dict)


@bp.route("/logout")
def logout():
    """remove the user id from the session"""
    session.clear()
    return redirect(url_for("index"))


def login_required(view):
    """returns a new view function that wraps the original
    view it’s applied to. The new function checks if a
    user is loaded and redirects to the login page
    otherwise. If a user is loaded the original view is
    called and continues normally.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
