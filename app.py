"""Main app"""

import os
import datetime
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app, ssl_cert_reqs="CERT_NONE")


@app.route("/")
@app.route("/get_books")
def get_books():
    """Get books from Mongo"""
    books = list(mongo.db.books.find())
    return render_template("books.html", books=books)


@app.route("/book_add", methods=["GET", "POST"])
def book_add():
    """book_add"""
    user_id = mongo.db.users.find_one({"username": session["user"]})["_id"]
    if request.method == "POST":
        book = {
            "book_title": request.form.get("book_title"),
            "book_author": request.form.get("book_author"),
            "book_description": request.form.get("book_description"),
            "added_date": datetime.datetime.now(),
            "added_by": ObjectId(user_id)
        }
        mongo.db.books.insert_one(book)
        flash("Book Successfully Added")
        return redirect(url_for("get_books"))
    return render_template("book_add.html")


@app.route("/book_edit/<book_title>", methods=["GET", "POST"])
def book_edit(book_title):
    """Edit book information"""
    book_id = mongo.db.books.find_one({"book_title": book_title})["_id"]
    book_author = mongo.db.books.find_one({"book_title": book_title})["book_author"]
    book_descripition = mongo.db.books.find_one({"book_title": book_title})["book_description"]
    user_id = mongo.db.users.find_one({"username": session["user"]})["_id"]
    if request.method == "POST":
        register_update = {
            "book_title": request.form.get("book_title"),
            "book_author": request.form.get("book_author"),
            "book_description": request.form.get("book_description"),
            "added_date": datetime.datetime.now(),
            "added_by": ObjectId(user_id)
        }
        mongo.db.books.update({"_id": ObjectId(book_id)}, register_update)
        flash("Update Successful!")
        return redirect(url_for("get_books"))
    return render_template("book_edit.html", book_title=book_title, book_author=book_author,)


@app.route("/book_delete/<book_id>")
def book_delete(book_id):
    """Delete a book"""
    mongo.db.books.remove({"_id": ObjectId(book_id)})
    flash("Book Successfully Deleted")
    return redirect(url_for("get_books"))


@app.route("/about")
def about():
    """Call about page"""
    return render_template("about.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    """Search function for books"""
    query = request.form.get("query")
    books = list(mongo.db.books.find({"$text": {"$search": query}}))
    return render_template("books.html", books=books)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registration function"""
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in function"""
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for("get_books"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """grab the session user's username from db"""
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    return render_template("profile.html", username=username)


@app.route("/profile_edit/<username>", methods=["GET", "POST"])
def profile_edit(username):
    """Edit profile"""
    user_id = mongo.db.users.find_one({"username": session["user"]})["_id"]
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user and session["user"] != existing_user["username"]:
            flash("Username already exists, choose another")
            return redirect(url_for("profile_edit", username=username))

        register_update = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.update({"_id": ObjectId(user_id)}, register_update)
        #remove user from 'session' cookie
        session.pop("user")
        flash("Update Successful!")
        return redirect(url_for("login"))

    return render_template("profile_edit.html", username=username)


@app.route("/profile_delete")
def profile_delete():
    """Delete profile"""
    user_id = mongo.db.users.find_one({"username": session["user"]})["_id"]
    mongo.db.users.remove({"_id": ObjectId(user_id)})
    flash("Profile Successfully Deleted")
    session.pop("user")
    return redirect(url_for("get_books"))


@app.route("/logout")
def logout():
    """remove user from session cookie"""
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False) ##### True for dev work#.
