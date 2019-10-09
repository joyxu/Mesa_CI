 #!/usr/bin/python3
 
import multiprocessing
import os
import os.path as path
import re
import sys
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402
from selenium.common.exceptions import TimeoutException  # noqa: E402
from selenium.webdriver.support.select import Select  # noqa: E402
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import http.server
import socketserver
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from bisect_test import TestLister
from build_support import build
from dependency_graph import DependencyGraph
from export import Export
from options import Options
from project_map import ProjectMap
from repo_set import RepoSet
from testers import ConfigFilter
from utils.check_gpu_hang import check_gpu_hang
from utils.command import run_batch_command
from utils.utils import (get_libdir, get_libgl_drivers, mesa_version,
                         get_conf_file)


class QuietServer(http.server.SimpleHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        pass
    def log_error(self, *arg):
        pass

def serve_webgl_cts(webgl_repo):
    os.chdir(webgl_repo)
    httpd = socketserver.TCPServer(("", 0), QuietServer)
    threading.Thread(target=socketserver.TCPServer.serve_forever, args=(httpd,)).start()
    return httpd
    
class TestExecutor:
    def __init__(self, lister, port):
        self._lister = lister 
        self._elements = {}
        self._driver = None
        self._port = port

    def list_tests(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = "/usr/bin/chromium"
        while True:
            try:
                self._driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", chrome_options=chrome_options)
                break
            except:
                print("Failed to launch Chrome")
        url = "http://localhost:" + str(self._port) + "/webgl-conformance-tests.html"
        self._driver.get(url)
        retry = 5
        while retry > 0:
            try:
                element = WebDriverWait(self._driver, 60).until(lambda driver: driver.find_element_by_id('page0'))
                folder_name_element = self._driver.find_element_by_class_name('folderName')
                case_elements = folder_name_element.find_elements_by_xpath('../..//*[@class="testpage"]')
                break
            except:
                retry -= 1
        for case_element in case_elements:
            test_name = case_element.text
            test_name = test_name.replace("/", ".")

            # remove ".html"
            test_components = test_name.split(".")
            test_components.pop()
            test_name = ".".join(test_components)

            # group tests together for the results page
            test_name = "webgl." + test_name
            self._elements[test_name] = case_element
                
    def tests(self):
        t = list(self._elements.keys())
        t.sort()
        return t

    def execute(self):
        while True:
            test = self._lister.pop_test()
            if not test:
                self._driver = None
                return

            element = self._elements[test]
            button = element.find_element_by_css_selector("input[type='button']")
            button.send_keys(Keys.ENTER)
            try:
                WebDriverWait(self._driver,
                              # 5min timeout, 100ms poll
                              300).until(lambda driver:
                                         re.search('(passed|skipped|failed|timeout)',
                                                   element.find_element_by_xpath('./div').text,
                                                   re.I))
            except:
                print("Timeout: " + test)
                self._lister.record_timeout(test)
                continue
            result_frame = self._driver.find_element_by_xpath(".//iframe")
            self._driver.switch_to_frame(result_frame)
            test_out = ""
            try:
                console = self._driver.find_element_by_id("console")
                test_out = console.text
            except:
                pass
            if not test_out:
                try:
                    console = self._driver.find_element_by_id("test-log")
                    test_out = console.text
                except:
                    print("no console for test: " + test)
                    pass
            self._driver.switch_to_default_content()
            
            self._lister.record_result(test,
                                       element.find_element_by_xpath('./div').text,
                                       test_out)

        
class WebGLTestLister(object):
    def __init__(self, options, project_map):
        self._test_count = 0
        self._percentage = 0
        self._tests = []
        self._opts = options
        self._workers = []
        self._mutex = threading.Lock()
        conf_filename = get_conf_file(options.hardware, options.arch, project="webgl")
        self._conf_file = ConfigFilter(conf_filename, self._opts)
        self._blacklist_file = path.splitext(conf_filename)[0] + "_blacklist.conf"
        test_dir = project_map.build_root() + "/../test"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        self._result_file = (test_dir + "/piglit-webgl_" + \
                             self._opts.hardware + "_" + self._opts.arch + "_" +
                             self._opts.shard + ".xml")
        self._suites = {}

    def list_tests(self):
        threads = []

        print("executors listing tests")
        # each worker process will have individual elements to find
        # and click to start tests.  They must all list the full
        # webpage.
        for w in self._workers:
            threads.append(threading.Thread(target=TestExecutor.list_tests, args=(w,)))
            threads[-1].start()

        for t in threads:
            t.join()

        if self._opts.retest_path:
            self._tests = TestLister(self._opts.retest_path + "/test/").RetestIncludes("webgl")
        else:
            self._tests = self._workers[0].tests()
        self._test_count = len(self._tests)

    def execute(self):
        threads = []
        for w in self._workers:
            threads.append(threading.Thread(target=TestExecutor.execute, args=(w,)))
            threads[-1].start()
        for t in threads:
            t.join()
            
    def pop_test(self):
        self._mutex.acquire()
        if not self._tests:
            self._mutex.release()
            return None
        
        t = self._tests.pop(0)
        new_percentage = 100 - (100 * len(self._tests) / self._test_count)
        if new_percentage > self._percentage + 1:
            self._percentage = int(new_percentage)
            print(str(self._percentage) + "% - " + t)
        
        self._mutex.release()
        return t
        
    def blacklist(self):
        blacklist_hash = {line.rstrip() : 1 for line in open(self._blacklist_file)}
        to_execute = []
        for test in self._tests:
            if test not in blacklist_hash:
                to_execute.append(test)
            else:
                print("blacklisted: " + test)
        to_execute.sort()
        self._tests = to_execute
        self._test_count = len(self._tests)

    def spawn_worker(self, port):
        self._workers.append(TestExecutor(self, port))
        
    def shard(self):
        if self._opts.shard == "0":
            return
        
        (shard, shards) = self._opts.shard.split(":")
        shard = int(shard)
        shards = int(shards)
        current_shard = 1
        shard_tests = []
        for t in self._tests:
            if current_shard == shard:
                shard_tests.append(t)
            current_shard += 1
            if current_shard > shards:
                current_shard = 1
        self._tests = shard_tests
        self._tests.sort()
        self._test_count = len(self._tests)

    def record_result(self, test, result_txt, test_output):
        match = re.search('(\w+): (\d+)/(\d+) in (\d+)', result_txt)
        if not match:
            print("failed to parse result: " + test + " : " + test_output)
            return
        status = match.group(1)
        if status == "Passed":
            status = "pass"
        elif status == "Skipped":
            status = "skip"
        else:
            status = "fail"
        duration = float(match.group(4)) / 1000.0 # convert ms to sec
        self._record_result(test, duration, status, test_output)
        
    def record_timeout(self, test):
        self._record_result(test, 300, "fail", "ERROR: test timed out")

    def _record_result(self, test, duration, status, output):
        test_components = test.split(".")
        suite = ".".join(test_components[0:-1])
        test_name = test_components[-1]
        self._mutex.acquire()
        if suite not in self._suites:
            self._suites[suite] = []
        self._suites[suite].append({"full_test_name" : test,
                                    "test_name" : test_name,
                                    "duration" : duration,
                                    "status" : status,
                                    "stdout" : output})
        self._mutex.release()
            
    def write_junit(self):
        deps = DependencyGraph("webgl",
                                  Options(args=[sys.argv[0]]),
                                  repo_set=None)
        missing_commits = RepoSet().branch_missing_revisions(deps)
        with open(self._result_file, "w") as out_xml:
            out_xml.write(' <testsuites>\n')
            for suite, tests in self._suites.items():
                out_xml.write(
                     """ <testsuite name="{}" tests="{}">\n""".format(suite, len(tests))
                     )
                for test in tests:
                    self._conf_file.write_junit(out_xml,
                                                suite,
                                                test["test_name"],
                                                test["status"],
                                                test["duration"],
                                                test["stdout"],
                                                "",
                                                missing_commits)
                out_xml.write(" </testsuite>\n")
            out_xml.write("</testsuites>")

class WebGLTester(object):
    """tests webgl via chromium/selenium"""
    def __init__(self):
        self._driver = None
        self._opts = Options()
        self.pm = ProjectMap()
        self._lister = WebGLTestLister(self._opts, self.pm)
        build_root = self.pm.build_root()
        libdir = get_libdir()
        env = { "LD_LIBRARY_PATH" : ':'.join([libdir, libdir + "/dri"]),
                      "LIBGL_DRIVERS_PATH": get_libgl_drivers()}
        if "iris" in self._opts.hardware:
            env["MESA_LOADER_DRIVER_OVERRIDE"] = "iris"

        self._opts.update_env(env)
        self._env = env

    def build(self):
        pass
    def clean(self):
        pass
    def test(self):
        version = mesa_version()
        if "19.2" in version or "19.1" in version:
            if "iris" in Options().hardware:
                return
        for k,v in self._env.items():
            os.environ[k] = v
        server = serve_webgl_cts(self.pm.project_source_dir("webgl") + "/conformance-suites/2.0.0")
        port = server.server_address[1]

        for _ in range(multiprocessing.cpu_count()):
            self._lister.spawn_worker(port)

        self._lister.list_tests()
        self._lister.blacklist()
        self._lister.shard()

        self._lister.execute()

        # wait for worker
        server.shutdown()
        server.server_close()
        
        self._lister.write_junit()
        
        # create a copy of the test xml in the source root, where
        # jenkins can access it.
        cmd = ["cp", "-a",
               self.pm.build_root() + "/../test", self.pm.source_root()]
        run_batch_command(cmd)

        check_gpu_hang()
        Export().export_tests()

class Timeout:
    def __init__(self):
        pass
    def GetDuration(self):
        return 90
    
def main():
    build(WebGLTester(),time_limit=Timeout())

if __name__ == '__main__':
    main()

