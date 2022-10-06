from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
import datetime

db = SQL("sqlite:///database.db")

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():

    id = session.get("user_id")

    q = db.execute("SELECT match_id, team1, score1, team2, score2, groupname, date, realscore1, realscore2 FROM matches WHERE user_id = ? GROUP BY match_id", id)
    if not q:
        db.execute("INSERT INTO matches(user_id, team1, score1, team2, score2, groupname, date) SELECT 999999, team1, score1, team2, score2, groupname, date FROM matches WHERE user_id = 3")
        db.execute("UPDATE matches SET user_id = ? WHERE user_id = 999999", id)
        q = db.execute("SELECT match_id, team1, score1, team2, score2, groupname, date FROM matches WHERE user_id = ? GROUP BY match_id", id)
    q2 = db.execute("SELECT winner, fase, scorer FROM users WHERE id = ?", id)
    q3 = db.execute("SELECT id, scorerpoints, winnerpoints, netherlandspoints, valsum FROM users INNER JOIN(SELECT user_id, SUM(points) valsum FROM matches GROUP BY user_id) matches ON users.id = matches.user_id WHERE user_id = ?", id)

    return render_template("index.html", query = q, query2 = q2, query3 = q3)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("wrong.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("wrong.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("wrong.html")

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

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("wrong.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("wrong.html")

        # Ensure confirmation password was submitted
        elif not request.form.get("confirmation"):
            return render_template("wrong.html")

        # Check if password = confirmation
        if (request.form.get("password") != request.form.get("confirmation")):
            return render_template("wrong.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Check if username taken
        if len(rows) > 0:
            return render_template("wrong.html")

        # Insert into database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get(
            "username"), generate_password_hash(request.form.get("password")))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/voorspellingen", methods=["GET", "POST"])
@login_required
def voorspellingen():

    if request.method == "POST":
        id = session.get("user_id")

        try:
            matchid = int(request.form.get("matchid"))
            pscore1 = request.form.get("score1")
            pscore2  = request.form.get("score2")

            db.execute("UPDATE matches SET score1 = ? WHERE (match_id % 48) = ? AND user_id = ?", pscore1, matchid, id)
            db.execute("UPDATE matches SET score2 = ? WHERE (match_id % 48) = ? AND user_id = ?", pscore2, matchid, id)

        except:
            winner  = request.form.get("teams")
            fase  = request.form.get("fase")
            scorer  = request.form.get("topscorer")

            if winner is not None:
                db.execute("UPDATE users SET winner = ? WHERE id = ?", winner, id)
            if fase is not None:
                db.execute("UPDATE users SET fase = ? WHERE id = ?", fase, id)
            if scorer is not None:
                db.execute("UPDATE users SET scorer = ? WHERE id = ?", scorer, id)

        return redirect("/voorspellingen")

    else:
        id = session.get("user_id")

        q = db.execute("SELECT match_id, team1, score1, team2, score2, groupname, date FROM matches WHERE user_id = ? AND score1 NOT BETWEEN 0 AND 10", id)

        return render_template("voorspellingen.html", query = q)

@app.route("/aanpassen", methods=["GET", "POST"])
@login_required
def aanpassen():

    if request.method == "POST":
        id = session.get("user_id")

        matchid = int(request.form.get("matchid"))
        pscore1 = request.form.get("score1")
        pscore2  = request.form.get("score2")

        db.execute("UPDATE matches SET score1 = ? WHERE (match_id % 48) = ? AND user_id = ?", pscore1, matchid, id)
        db.execute("UPDATE matches SET score2 = ? WHERE (match_id % 48) = ? AND user_id = ?", pscore2, matchid, id)

        return redirect("/aanpassen")

    else:
        id = session.get("user_id")

        q = db.execute("SELECT match_id, team1, score1, team2, score2, groupname, date FROM matches WHERE user_id = ?", id)

        return render_template("aanpassen.html", query = q)

@app.route("/stand")
def stand():

    id = session.get("user_id")

    # WHERE id > 5
    q = db.execute("SELECT id, username, scorerpoints, winnerpoints, netherlandspoints, valsum, valcount FROM users INNER JOIN(SELECT user_id, SUM(points) valsum, SUM(points=3) valcount FROM matches GROUP BY user_id) matches ON users.id = matches.user_id WHERE id > 5 ORDER BY (scorerpoints + winnerpoints + netherlandspoints + valsum) DESC, valcount, scorerpoints")

    return render_template("stand.html", query=q, id=id)

@app.route("/volgende", methods=["GET", "POST"])
def volgende():
    if request.method == "POST":
        y = request.form.get("dateselector") + " 2022"
        z = y.lower()
        q = db.execute("SELECT username, match_id, team1, score1, team2, score2, groupname, date FROM matches JOIN users ON matches.user_id = users.id WHERE matches.date = ? AND users.id > 5 ORDER BY team1", z)
        return render_template("volgende.html", query=q)

    else:
        x = datetime.datetime.now()
        xtest = datetime.datetime(2022, 11, 20)
        if x > xtest:
            y = (x.strftime("%d %B %Y"))
            z = y.lower()
            q = db.execute("SELECT username, match_id, team1, score1, team2, score2, groupname, date FROM matches JOIN users ON matches.user_id = users.id WHERE matches.date = ? AND users.id > 5 ORDER BY team1", z)
        else:
            q = db.execute("SELECT username, match_id, team1, score1, team2, score2, groupname, date FROM matches JOIN users ON matches.user_id = users.id WHERE matches.date = '20 november 2022' AND users.id > 5 ORDER BY team1")

        return render_template("volgende.html", query=q)


@app.route("/realscoresenter", methods=["GET", "POST"])
@login_required
def realscoresenter():

    if request.method == "POST":
        id = session.get("user_id")

        matchid = int(request.form.get("matchid"))
        pscore1 = int(request.form.get("realscore1"))
        pscore2  = int(request.form.get("realscore2"))
        pscorem = pscore1 - pscore2

        # set real scores
        db.execute("UPDATE matches SET realscore1 = ? WHERE (match_id % 48) = ?", pscore1, matchid)
        db.execute("UPDATE matches SET realscore2 = ? WHERE (match_id % 48) = ?", pscore2, matchid)

        # update stand en users.scores
        db.execute("UPDATE matches SET points = 0 WHERE (match_id % 48) = ?", matchid)
        if pscorem < 0:
            db.execute("UPDATE matches SET points = 1 WHERE (match_id % 48) = ? AND (score1 - score2) < 0", matchid)
        if pscorem == 0:
            db.execute("UPDATE matches SET points = 1 WHERE (match_id % 48) = ? AND (score1 - score2) = 0", matchid)
        if pscorem > 0:
            db.execute("UPDATE matches SET points = 1 WHERE (match_id % 48) = ? AND (score1 - score2) > 0", matchid)
        db.execute("UPDATE matches SET points = 3 WHERE (match_id % 48) = ? AND score1 = ? AND score2 = ? AND realscore1 = ? AND realscore2 = ?", matchid, pscore1, pscore2, pscore1, pscore2)

        return redirect("/realscoresenter")

    else:
        id = session.get("user_id")

        q = db.execute("SELECT match_id, team1, score1, team2, score2, realscore1, realscore2, groupname, date FROM matches WHERE user_id = ?", id)

        return render_template("realscoresenter.html", query = q)