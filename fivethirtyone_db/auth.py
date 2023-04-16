import functools
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
        athlete = db.Athlete(username)

        if not check_password_hash(athlete.pwd_hash, password):
            error = f"Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = username
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
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = user_id


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
