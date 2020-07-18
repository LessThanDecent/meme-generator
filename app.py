import os
import requests

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd, get_image

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///memegen.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

memes = [meme for meme in requests.get("https://api.imgflip.com/get_memes").json()["data"]["memes"] if meme["box_count"] == 2]
# Load list of meme formats once

for meme in memes:
    meme["url"] = get_image(meme["id"], "Text 1", "Text 2")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Generate meme"""
    if request.method == "POST":
        meme_id, text0, text1 = request.form.get("format"), request.form.get("text0"), request.form.get("text1")

        if not meme_id:
            return apology("incomplete form", 403)

        url = get_image(meme_id.split(',')[0], text0, text1)

        db.execute("INSERT INTO memes ('memeID', 'text0', 'text1', 'userID', 'timestamp') VALUES (:memeID, :text0, :text1, :userID, datetime('now', 'localtime'))", memeID=meme_id.split(',')[0], text0=text0, text1=text1, userID=session["user_id"])

        return render_template("meme.html", url=url)

    else:
        return render_template("index.html", memes=memes)

@app.route("/history")
@login_required
def history():
    """ Show a table of user's memes """
    rows = db.execute("SELECT * FROM memes WHERE userID=:id", id=session["user_id"])
    memes = []

    for row in rows:
        row_dict = {}
        row_dict["description"] = f"{row['text0']} | {row['text1']}"
        row_dict["timestamp"] = row["timestamp"]
        row_dict["link"] = get_image(row["memeID"], row["text0"], row["text1"])

        memes.append(row_dict)
    
    return render_template("history.html", memes=memes)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username, password, confirmation = request.form.get("username"), request.form.get("password"), request.form.get("confirmation")

        # Ensure username is not taken and that username is not blank
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if len(rows) != 0 or not username:
            return apology("invalid username", 403)
        
        # Ensure both passwords are not blank
        if not password or not confirmation:
            return apology("password is empty", 403)
        
        # Ensure that passwords match
        if password != confirmation:
            return apology("passwords do not match", 403)
        
        # Insert the new login information into the database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=generate_password_hash(password))

        return redirect("/login")

    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
