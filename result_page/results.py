from flask import Flask
from flask import g
from flask import render_template
import MySQLdb
from functools import wraps
import time

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
    g.cur.execute("select build_id, build_name, pass_count, filtered_pass_count, fail_count from build")
    builds = []
    for b in g.cur.fetchall():
        builds.append( { "build_id" : b[0],
                         "build_name" : b[1],
                         "pass_count" : b[2],
                         "filtered_pass_count" : b[3],
                         "fail_count" : b[4] } )
    return render_template('builds.html', job=job, builds=builds)

@app.route("/<job>/builds/<build_id>/group/<group_id>")
def list_fails(job, build_id, group_id):
    g.cur.execute("use " + job)
    g.cur.execute("select build_name from build where build_id=%s", [build_id])
    build_name = g.cur.fetchone()[0]
    g.cur.execute("select test_name from test where test_id=%s", [group_id])
    group_name = g.cur.fetchone()[0]
    
    g.cur.execute("select result_id, test_name, hardware, arch, "
                  "status, filtered_status, time "
                  "from result join test using (test_id) "
                  "join ancestor using (test_id)"
                  """where (filtered_status="fail" and build_id=%s and ancestor_id=%s) """
                  "order by test_name", [build_id, group_id])
    fail_list = g.cur.fetchall()
    fails = []
    for f in fail_list:
        fail = {}
        (fail["result_id"],
         fail["test_name"],
         fail["hardware"],
         fail["arch"],
         fail["status"],
         fail["filtered_status"],
         fail["time"]) = f
        fails.append(fail)

    g.cur.execute("select test_name, test_id from parent "
                  "join test using(test_id) "
                  "where parent_id=%s "
                  "order by test_name", [group_id])
    subgroups = g.cur.fetchall()

    statistics = []
    subgroup_dicts = []
    for subgroup in subgroups:
        g.cur.execute("select count(*) from result "
                      "join test using (test_id) "
                      "join ancestor using(test_id) "
                      """where build_id=%s and ancestor_id=%s and status="pass" """,
                      [build_id, subgroup[1]])
        pass_count = g.cur.fetchone()[0]
        g.cur.execute("select count(*) from result "
                      "join test using (test_id) "
                      """where build_id=%s and test_id=%s and status="pass" """,
                      [build_id, subgroup[1]])
        pass_count += g.cur.fetchone()[0]
        g.cur.execute("select count(*) from result "
                      "join test using (test_id) "
                      "join ancestor using(test_id) "
                      """where build_id=%s and filtered_status="fail" and ancestor_id=%s""",
                      [build_id, subgroup[1]])
        filtered_fail_count = g.cur.fetchone()[0]
        g.cur.execute("select count(*) from result "
                      "join test using (test_id) "
                      """where build_id=%s and test_id=%s and filtered_status="fail" """,
                      [build_id, subgroup[1]])
        filtered_fail_count += g.cur.fetchone()[0]
        g.cur.execute("select count(*) from result "
                      "join test using (test_id) "
                      "join ancestor using(test_id) "
                      """where build_id=%s and status="fail" and ancestor_id=%s""",
                      [build_id, subgroup[1]])
        fail_count = g.cur.fetchone()[0]
        g.cur.execute("select count(*) from result "
                      "join test using (test_id) "
                      """where build_id=%s and test_id=%s and status="fail" """,
                      [build_id, subgroup[1]])
        fail_count += g.cur.fetchone()[0]
        subgroup_dicts.append({"subgroup_name" : subgroup[0],
                               "subgroup_id" : subgroup[1],
                               "pass_count" : pass_count,
                               "fail_count" : fail_count,
                               "filtered_fail_count" : filtered_fail_count})
        
    g.cur.execute("select result_id, test_name, hardware, arch, "
                  "status, filtered_status "
                  "from result join test using (test_id) "
                  "where (test_id=%s and build_id=%s) ", [group_id, build_id])
    test_results = g.cur.fetchall()
    test_dicts = [{"result_id" : result[0],
                   "test_name" : result[1],
                   "hardware" : result[2],
                   "arch" : result[3],
                   "status": result[4],
                   "filtered_status" : result[5] } for result in test_results]
    
    return render_template('results.html', job=job, build_name=build_name,
                           group_name=group_name,
                           fails=fails, subgroups=subgroup_dicts,
                           test_results=test_dicts)


@app.route("/<job>/builds/<build_id>/results/<result_id>")
def result(job, build_id, result_id):
    g.cur.execute("use " + job)
    g.cur.execute("select build_name from build where build_id={}".format(build_id))
    build_name = g.cur.fetchone()[0]
    g.cur.execute("""select test_id, test_name, hardware, arch, """
                  """status, filtered_status, time, stdout, stderr """
                  """from result join test using (test_id) """
                  """where (result_id={})""".format(result_id))
    result = g.cur.fetchone()
    return render_template('test.html', job=job, build_name=build_name, result=result)

@app.route("/<job>/test/<test_id>/history")
def history(job, test_id):
    g.cur.execute("use " + job)
    g.cur.execute("""select test_name from test where test_id="{}" """.format(test_id))
    test_name = g.cur.fetchone()[0]
    g.cur.execute("""select build_id, build_name, result_id, """
                  """hardware, arch, status, filtered_status, time """
                  """from result join build using (build_id) """
                  """where (test_id="{}") """
                  """order by build_id""".format(test_id))
    results = g.cur.fetchall()
    return render_template("history.html", job=job, test_name=test_name, results=results)
