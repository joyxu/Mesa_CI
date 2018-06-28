from flask import Flask
from flask import g
from flask import render_template
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
def main():
    g.cur.execute("show databases")
    jobs = g.cur.fetchall()
    job_names = []
    for j in jobs:
        j = str(j[0])
        if j not in ["performance_schema", "information_schema", "mysql"]:
            job_names.append(j)
    return render_template('main.html', jobs=job_names)


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
    build_names = []
    for build in builds:
        (bid, name) = build
        build_names.append((bid, name))
    return render_template('builds.html', job=job, builds=build_names)

@app.route("/<job>/builds/<build_id>/fails")
def list_fails(job, build_id):
    g.cur.execute("use " + job)
    g.cur.execute("select build_name from build where build_id={}".format(build_id))
    build_name = g.cur.fetchone()[0]
    print("build_name: " + str(build_name))
    g.cur.execute("select test_name, status, filtered_status, time from result join test using (test_id) where (filtered_status=\"fail\" and build_id={}) order by test_name".format(build_id))
    results = g.cur.fetchall()
    return render_template('results.html', job=job, build_name=build_name, results=results)
    outstring = ""
    for build in builds:
        (bid, name) = build
        outstring += str(name) + "\n"
    return outstring
