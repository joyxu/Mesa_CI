from flask import Flask
from flask import Markup
from flask import g
from flask import render_template
import MySQLdb
import datetime
import os
from functools import wraps

app = Flask(__name__)


@app.before_request
def before_request():
    host = "localhost"
    if "SQL_DATABASE_HOST" in os.environ:
        host = os.environ["SQL_DATABASE_HOST"]
    g.db = MySQLdb.connect(host=host)
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
    return render_template('main.html',
                           jobs=job_names,
                           top_links=[{"text": "i965 Mesa CI",
                                       "href": "."}])

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
    return render_template('builds.html', job=job, builds=builds,
                           top_links=[{"text": "i965 Mesa CI",
                                       "href": "../.."},
                                      {"text": job,
                                       "href": "."}])

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
                  """where (filtered_status="fail" and build_id=%s) """
                  "limit 1000", [build_id])
    fail_list = g.cur.fetchall()
    fails = []
    for f in fail_list:
        fail = {}
        (fail["result_id"],
         test_name,
         fail["hardware"],
         fail["arch"],
         fail["status"],
         fail["filtered_status"],
         fail["time"]) = f
        fail["test_name"] = Markup(test_name.replace('.', '.&shy'))
        if test_name.startswith(group_name) or group_name=="root":
            fails.append(fail)

    g.cur.execute("select test_name, test_id from parent "
                  "join test using(test_id) "
                  "where parent_id=%s "
                  "order by test_name", [group_id])
    subgroups = g.cur.fetchall()

    statistics = []
    subgroup_dicts = []
    for subgroup in subgroups:
        g.cur.execute("select pass_count, fail_count, filtered_pass_count, time from group_ "
                      """where build_id=%s and test_id=%s""",
                      [build_id, subgroup[1]])
        statistics = g.cur.fetchone()
        if not statistics:
            continue
        (pass_count, fail_count, filtered_pass_count, t_time) = statistics
        subgroup_dicts.append({"subgroup_name" : Markup(subgroup[0].replace('.', '.&shy')),
                               "subgroup_id" : subgroup[1],
                               "pass_count" : pass_count,
                               "fail_count" : fail_count,
                               "filtered_pass_count" : filtered_pass_count,
                               "time" : str(datetime.timedelta(seconds=float(t_time)))})
        
    g.cur.execute("select result_id, test_name, hardware, arch, "
                  "status, filtered_status "
                  "from result join test using (test_id) "
                  "where (test_id=%s and build_id=%s) ", [group_id, build_id])
    test_results = g.cur.fetchall()
    test_dicts = [{"result_id" : result[0],
                   "test_name" : Markup(result[1].replace('.', '.&shy')),
                   "hardware" : result[2],
                   "arch" : result[3],
                   "status": result[4],
                   "filtered_status" : result[5] } for result in test_results]

    top_links = [{"text": "i965 Mesa CI",
                  "href": "../../../.."},
                 {"text": job,
                  "href": "../../../builds/"},
                 {"text": build_name,
                  "href": "63a9f0ea7bb98050796b649e85481845"}]
    uplink = ""
    if group_name != "root":
        for group in group_name.split("."):
            uplink += group
            g.cur.execute("select test_id from test where test_name=%s", [uplink])
            top_links.append({"text": group, "href": g.cur.fetchone()[0]})
            uplink += "."

    return render_template('results.html', top_links=top_links,
                           job=job, build_name=build_name,
                           group_name=Markup(group_name.replace('.', '.&shy')),
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
    result_list = g.cur.fetchone()
    top_links = [{"text": "i965 Mesa CI",
                  "href": "../../../.."},
                 {"text": job,
                  "href": "../../../builds/"},
                 {"text": build_name,
                  "href": "../group/63a9f0ea7bb98050796b649e85481845"}]
    test_name = result_list[1]
    result = {"test_id" : result_list[0],
              "test_name" : Markup(result_list[1].replace('.', '.&shy')),
              "hardware" : result_list[2],
              "arch" : result_list[3],
              "status" : result_list[4],
              "filtered_status" : result_list[5],
              "time" : result_list[6],
              "stdout" : result_list[7],
              "stderr" : result_list[8]}
    uplink = ""
    for group in test_name.split("."):
        uplink += group
        g.cur.execute("select test_id from test where test_name=%s", [uplink])
        top_links.append({"text": group, "href": "../group/" + g.cur.fetchone()[0]})
        uplink += "."
    return render_template('test.html', job=job, build_name=build_name, result=result,
                           top_links=top_links)

@app.route("/<job>/test/<test_id>/history")
def history(job, test_id):
    g.cur.execute("use " + job)
    g.cur.execute("""select test_name from test where test_id="{}" """.format(test_id))
    test_name = Markup(g.cur.fetchone()[0].replace('.', '.&shy'))
    g.cur.execute("""select build_id, build_name, result_id, """
                  """hardware, arch, status, filtered_status, time """
                  """from result join build using (build_id) """
                  """where (test_id="{}") """
                  """order by build_id""".format(test_id))
    results = []
    for result in g.cur.fetchall():
        results.append({"build_id" : result[0],
                        "build_name" : result[1],
                        "result_id" : result[2],
                        "hardware" : result[3],
                        "arch" : result[4],
                        "status" : result[5],
                        "filtered_status" : result[6],
                        "time" : result[7]})
    top_links = [{"text": "i965 Mesa CI",
                  "href": "../../../.."},
                 {"text": job,
                  "href": "../../builds/"}]
    return render_template("history.html", job=job, test_name=test_name, results=results,
                           top_links=top_links)
