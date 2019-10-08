#!/usr/bin/python

import os
import sys
import urllib
try:
    from urllib2 import urlopen, urlencode, URLError, HTTPError, quote
except:
    from urllib.request import urlopen, URLError, HTTPError, quote
    from urllib.parse import urlencode
import ast
import time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from project_map import ProjectMap

server = ProjectMap().build_spec().find("build_master").attrib["host"]

url = "http://" + server + "/computer/api/python"
f = urlopen(url)
host_dict = ast.literal_eval(f.read().decode('utf-8'))

def is_excluded():
    if ("builder" in host or host == "master" or "simdrm" in host):
        return True

for a_host in host_dict['computer']:
    host = a_host['displayName']
    if is_excluded():
        continue
    f = { 'token' : 'noauth', 'label' : host}
    url = "http://" + server + "/job/reboot_single/buildWithParameters?" + urlencode(f)
    print("triggering " + url)
    urlopen(url)
    time.sleep(1)
