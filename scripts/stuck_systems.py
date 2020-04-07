import json
import os
import sys
from urllib.request import urlopen, URLError, HTTPError
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from project_map import ProjectMap

offline_causes = ["hudson.node_monitors.ResponseTimeMonitor$Data",
                  "hudson.slaves.OfflineCause$LaunchFailed"]


def list_stuck_systems():
    spec = ProjectMap().build_spec()
    jenkins_server = spec.find("build_master").attrib["host"]
    resp = urlopen('http://' + jenkins_server + '/computer/api/json').read()
    nodes = json.loads(resp)['computer']

    stuck_systems = {}
    for node in nodes:
        if node['_class'] != 'hudson.slaves.SlaveComputer':
            continue
        if not node['offlineCause']:
            continue
        if node['offline'] and node['offlineCause']['_class'] in offline_causes:
            try:
                node_name = node['displayName']
            except (IndexError, KeyError) as e:
                print('ERR: Unable to parse computer name: ')
                print(e)
                continue
            stuck_systems[node_name] = ('http://' + jenkins_server +
                                        '/computer/' + node_name + '/')
    sorted_systems = sorted(stuck_systems)
    for n in sorted_systems:
        print('{:<15}{}'.format(n, stuck_systems[n]))
    print('total: ' + str(len(sorted_systems)))


if __name__ == "__main__":
    list_stuck_systems()

