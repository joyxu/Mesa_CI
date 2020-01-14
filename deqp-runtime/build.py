#!/usr/bin/python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from testers import DeqpTester, DeqpTrie, ConfigFilter
from build_support import build
from options import Options
from project_map import ProjectMap
from utils.command import run_batch_command
from utils.utils import get_conf_file, mesa_version


class SlowTimeout:
    def __init__(self):
        self.hardware = Options().hardware

    def GetDuration(self):
        return 500


class DeqpRuntimeLister():
    def __init__(self, binary):
        self.binary = binary
        self.o = Options()
        self.pm = ProjectMap()
        self.blacklist_txt = None
        self.version = None
        bd = self.pm.project_build_dir()
        hw_prefix = self.o.hardware
        # Note: bsw has known failures that need to be resolved
        # first: https://bugs.freedesktop.org/show_bug.cgi?id=104981
        if hw_prefix in ['g33', 'g45', 'ilk', 'g965', 'hsw', 'byt', 'bsw']:
            raise Exception(("ERROR: This platform is not supported by "
                             "this test"))
        if "gles2" in self.binary:
            self.blacklist_txt = (bd + hw_prefix +
                                  "_expectations/gles2_unstable_tests.txt")
        if "gles3" in self.binary:
            self.blacklist_txt = (bd + hw_prefix +
                                  "_expectations/gles3_unstable_tests.txt")
        if "gles31" in self.binary:
            self.blacklist_txt = (bd + hw_prefix +
                                  "_expectations/gles31_unstable_tests.txt")
        if "egl" in self.binary:
            self.blacklist_txt = (bd + hw_prefix +
                                  "_expectations/egl_unstable_tests.txt")


    def tests(self, env):
        # don't execute tests that are part of the other suite
        whitelist_txt = None
        cases_xml = None
        if "gles2" in self.binary:
            whitelist_txt = (self.pm.project_source_dir("deqp") +
                             "/android/cts/master/gles2-master.txt")
            cases_xml = "dEQP-GLES2-cases.xml"
        if "gles3" in self.binary:
            whitelist_txt = (self.pm.project_source_dir("deqp") +
                             "/android/cts/master/gles3-master.txt")
            cases_xml = "dEQP-GLES3-cases.xml"
        if "gles31" in self.binary:
            whitelist_txt = (self.pm.project_source_dir("deqp") +
                             "/android/cts/master/gles31-master.txt")
            cases_xml = "dEQP-GLES31-cases.xml"
        if "egl" in self.binary:
            whitelist_txt = (self.pm.project_source_dir("deqp") +
                             "/android/cts/master/egl-master.txt")
            cases_xml = "dEQP-EGL-cases.xml"
        deqp_dir = os.path.dirname(self.binary)
        os.chdir(deqp_dir)
        cmd = [self.binary,
               "--deqp-runmode=xml-caselist"]
        run_batch_command(cmd, env=env)
        all_tests = DeqpTrie()
        all_tests.add_xml(cases_xml)
        whitelist = DeqpTrie()
        whitelist.add_txt(whitelist_txt)
        all_tests.filter_whitelist(whitelist)
        os.chdir(self.pm.project_build_dir())
        return all_tests

    def blacklist(self, all_tests):
        if self.blacklist_txt:
            blacklist = DeqpTrie()
            blacklist.add_txt(self.blacklist_txt)
            all_tests.filter(blacklist)
        # The following test exceeds 30 seconds on all platforms, so
        # we ignore it
        unsupported = ["dEQP-GLES2.functional.flush_finish.wait"]
        all_tests.filter(unsupported)


class DeqpRuntimeBuilder(object):
    def __init__(self):
        self.pm = ProjectMap()
        self.o = Options()
        self.env = {}
        self.version = None

    def build(self):
        pass

    def clean(self):
        pass

    def test(self):
        t = DeqpTester(runtime=30)
        all_results = DeqpTrie()

        if not self.version:
            self.version = mesa_version()

        modules = ["gles2", "gles3", "gles31"]

        for module in modules:
            binary = os.path.join(self.pm.build_root(), "opt/deqp/modules",
                                  module, "deqp-" + module)
            results = t.test(binary,
                             DeqpRuntimeLister(binary),
                             [],
                             self.env)
            all_results.merge(results)

        config = get_conf_file(self.o.hardware, self.o.arch,
                                  project=self.pm.current_project())
        t.generate_results(all_results, ConfigFilter(config, self.o))


build(DeqpRuntimeBuilder(), time_limit=SlowTimeout())
