from flask import Flask
from flask import g
import MySQLdb
from functools import wraps

app = Flask(__name__)


@app.before_request
def before_request():
    g.db = MySQLdb.connect(host="localhost")
    g.cur = g.db.cursor()


@app.after_request
def after_request(response):
    g.db.close()
    return response
            
@app.route("/")
def hello():
    return "Hello World!"


@app.route("/jobs")
def list_jobs():
    g.cur.execute("show databases")
    jobs = g.cur.fetchall()
    outstring = ""
    for j in jobs:
        j = str(j[0])
        if j != "information_schema":
            outstring += j + "\n"
    return outstring

@app.route("/<job>/builds/")
def list_builds(job):
    g.cur.execute("use " + job)
    g.cur.execute("select * from build")
    builds = g.cur.fetchall()
    outstring = ""
    for build in builds:
        (bid, name) = build
        outstring += str(name) + "\n"
    return outstring

@app.route("/<job>/builds/<build_id>/fails")
def list_fails(job, build_id):
    g.cur.execute("use " + job)
    g.cur.execute("select test_name, status from result join test using (test_id) where (status=\"fail\" and build_id={}) order by test_name".format(build_id))
    fails = g.cur.fetchall()
    return str(fails)
    outstring = ""
    for build in builds:
        (bid, name) = build
        outstring += str(name) + "\n"
    return outstring
