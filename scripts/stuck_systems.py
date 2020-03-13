import json
import os
import sys
from urllib.request import urlopen, URLError, HTTPError
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from project_map import ProjectMap

offline_causes = ["hudson.node_monitors.ResponseTimeMonitor$Data",
                  "hudson.slaves.OfflineCause$LaunchFailed"]


def get_offline_reason(jenkins_server, computer):
    try:
        resp = urlopen('http://' + jenkins_server + '/computer/' + computer
                       + '/api/json').read()
    except HTTPError as e:
        print('ERR: Unable to reach url: http://' + jenkins_server +
              '/computer/' + computer + 'api/json')
        print(e)
        return None
    cause = json.loads(resp).get('offlineCause')
    if cause:
        return cause.get('_class')
    return None


def list_stuck_systems():
    spec = ProjectMap().build_spec()
    jenkins_server = spec.find("build_master").attrib["host"]
    resp = urlopen('http://' + jenkins_server + '/queue/api/json').read()
    queued_builds = json.loads(resp)['items']

    stuck_systems = {}
    for build in queued_builds:
        if build['task']['name'] == 'reboot_single':
            try:
                computer = build['actions'][0]['parameters'][0]['value']
            except (IndexError, KeyError) as e:
                print('ERR: Unable to parse computer name: ')
                print(e)
                continue
            cause = get_offline_reason(jenkins_server, computer)
            if not cause:
                continue
            if cause in offline_causes and computer not in stuck_systems:
                stuck_systems[computer] = ('http://' + jenkins_server +
                                           '/computer/' + computer + '/')
    for c, u in stuck_systems.items():
        print('{:<15}{}'.format(c, u))


if __name__ == "__main__":
    list_stuck_systems()

