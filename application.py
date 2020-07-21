import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

message = {"buy":"", "sold":""}


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
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    username = str(db.execute("select username from users where id = :user_id", user_id = session["user_id"])[0]["username"])
    list1 = db.execute("select symbol, company, shares from buy where username = :username", username= username)
    total = 0
    for i in range(len(list1)):
        price = lookup(list1[i]["symbol"])["price"]
        list1[i]["price"] = price
        list1[i]["total"] = price * list1[i]["shares"]
        total += list1[i]["total"]
    cash = db.execute("select cash from users where username = :username", username=username)[0]["cash"]


    return render_template("index.html", list = list1, cash=cash, total=total)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("share"))
        user_id = session["user_id"]
        user = db.execute("select username from users where id = :user_id", user_id=user_id)
        username = str(user[0]["username"])
        print("username", username)
        dict = lookup(symbol)
        if dict:
            cash = db.execute("select cash from users where id = :user_id", user_id=user_id)
            cash = float(cash[0]["cash"])
            price = shares * dict["price"]
            symbol = dict["symbol"]

            userid = symbol+username
            if price <= cash:
                cash -= price
                # check if the company shares have already been bought
                bought_shares = db.execute("select shares from buy where id = :userid", userid = userid)

                if bought_shares:
                    # if shares have already been bought, just update the number of shares
                    bought_shares=int(bought_shares[0]["shares"])
                    db.execute ("update buy set shares = :shares where id = :userid", shares=shares+bought_shares, userid=userid)
                else:

                    # insert a new column with the shares and all details
                    db.execute ("insert into buy values (:id, :username, :company, :symbol, :shares)",id=userid,
                    username=username, company=dict["name"], symbol=symbol, shares=shares)

                # update the user cash in users table
                db.execute ("update users set cash = :cash where username = :username", cash=cash, username=username)
                # update the transaction history
                db.execute("insert into history ('username', 'symbol', 'shares', 'price', 'total') values (:username, :symbol, :shares, :price, :total )", username= username,
                symbol=symbol, shares=shares, price=dict["price"], total=price)
                flash("Bought")
                return redirect("/")
            else:
                flash("You do not have enough Cash")

                return redirect("/buy")
        else:
            flash("no such Symbol")
            return redirect("/buy")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():

    """Show history of transactions"""
    username = str(db.execute("select username from users where id = :user_id", user_id = session["user_id"])[0]["username"])
    list1 = db.execute("select symbol, shares, price, total, transacted from history where username = :username ", username=username)



    return render_template("history.html", list = list1 )


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""


    if request.method == "POST":
        # get the symbol from the user
        symbol = request.form.get("symbol")
        # lookup the symbol and store the returned dict
        dict = lookup(symbol)
        if dict:
                str = " A share of {company} {symbol} costs {price}".format(company=dict["name"], symbol=dict["symbol"], price=usd(dict["price"]))
                return render_template("quoted.html", quoted = str)
        else:
            flash("Sorry no such company")
        return redirect("/quote")

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""



    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        name = request.form.get("username")
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) >= 1:
            return render_template("register.html", message="username already exists")
        elif (password != confirm_password):
            return render_template("register.html", pass_message="passwords do not match")

        db.execute("INSERT into users(username, hash) values(:username, :password)", username = name.lower(), password=generate_password_hash(password))



        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""





    # if the form is submitted with number of shares
    if request.method == "POST":
         # get the username for the user
        username = str(db.execute("select username from users where id = :user_id", user_id = session["user_id"])[0]["username"])
        symbol = request.form.get("selected-symbol")
        shares = int(request.form.get("shares"))

        # get the current price for the shares to be sold
        # lookup the symbol and store the price
        price = lookup(symbol)["price"]
        # calculate the overall price taht will be added to the cash
        total = shares * price
        # get the number of shares already held for the particular symbol that was submitted via post
        shares_held = db.execute("select shares from buy where symbol=:symbol ", symbol=symbol)[0]["shares"]
        updated_shares = shares_held - shares
        # update the cash in the users database
        if updated_shares <0:
            flash("You do not have enough shares to sell")
            return redirect("/sell")
        db.execute("update users set cash = cash + :total where username = :username", total=total, username=username)
        # add the transaction to the history
        db.execute("insert into history ('username' , 'symbol', 'shares', 'price', 'total') values(:username , :symbol, :shares, :price, :total)",
        username=username, symbol=symbol, shares=-shares, price=price, total=total)


        # if all the shares are sold, remove the corresponding entry from the buy
        if updated_shares == 0:

            # if the number of shares=0, remove it from "buy" table
            db.execute("delete from buy where id=:userid", userid=symbol+username)
        else:
            # update the entry in buy with the reduced number of shares
            db.execute("update buy set shares=:updated_shares where id=:userid",updated_shares=updated_shares, userid=symbol+username)
        message["sold"] = "sold"
        flash("Sold")
        return redirect("/")
    else:
        # means that the method is "GET" so send the symbols and the shares for each
        username = str(db.execute("select username from users where id = :user_id", user_id = session["user_id"])[0]["username"])
        # get the purchased company symbol and shares, these will be sent to the "GET" form
        list2 = db.execute("select symbol, shares from buy where username = :username", username=username)
        return render_template("sell.html", list = list2)




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
