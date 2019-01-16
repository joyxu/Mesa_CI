#!/usr/bin/python

import os
import sys
import subprocess

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs


class SlowTimeout:
    def __init__(self):
        self.hardware = bs.Options().hardware

    def GetDuration(self):
        return 500

class DeqpLister(object):
    def __init__(self, binary):
        self.binary = binary
        self.o = bs.Options()
        self.pm = bs.ProjectMap()
        self.version = None

    def tests(self, env):
        # don't execute tests that are part of the other suite
        whitelist_txt = None
        cases_xml = None
        if "gles2" in self.binary:
            whitelist_txt = self.pm.project_source_dir("deqp") + "/android/cts/master/gles2-master.txt"
            cases_xml = "dEQP-GLES2-cases.xml"
        if "gles3" in self.binary:
            whitelist_txt = self.pm.project_source_dir("deqp") + "/android/cts/master/gles3-master.txt"
            cases_xml = "dEQP-GLES3-cases.xml"
        if "gles31" in self.binary:
            whitelist_txt = self.pm.project_source_dir("deqp") + "/android/cts/master/gles31-master.txt"
            cases_xml = "dEQP-GLES31-cases.xml"
        if "egl" in self.binary:
            whitelist_txt = self.pm.project_source_dir("deqp") + "/android/cts/master/egl-master.txt"
            cases_xml = "dEQP-EGL-cases.xml"
        deqp_dir = os.path.dirname(self.binary)
        os.chdir(deqp_dir)
        cmd = [self.binary,
               "--deqp-runmode=xml-caselist"]
        bs.run_batch_command(cmd, env=env)
        all_tests = bs.DeqpTrie()
        all_tests.add_xml(cases_xml)
        whitelist = bs.DeqpTrie()
        whitelist.add_txt(whitelist_txt)
        all_tests.filter_whitelist(whitelist)
        os.chdir(self.pm.project_build_dir())
        return all_tests

    def blacklist(self, all_tests):
        bd = self.pm.project_build_dir()
        # to match "skl" instead of "sklgt2"
        hw_prefix = self.o.hardware[:3]
        for a_blacklist in [self.o.hardware + "_blacklist.txt",
                            hw_prefix + "_blacklist.txt",
                            "blacklist.txt"]:
            blacklist_txt = bd + a_blacklist
            if blacklist_txt:
                blacklist_trie = bs.DeqpTrie()
                blacklist_trie.add_txt(blacklist_txt)
                all_tests.filter(blacklist_trie)
            
        if not self.version:
            self.version = bs.mesa_version()

        # filter immediately, since any unsupported tests under these
        # top-level categories will prevent them from being filtered.
        if "gles2" not in self.binary:
            all_tests.filter(["dEQP-GLES2"])
        if "gles31" not in self.binary:
            all_tests.filter(["dEQP-GLES31"])
        if "gles3" not in self.binary:
            all_tests.filter(["dEQP-GLES3"])
        if "egl" not in self.binary:
            all_tests.filter(["dEQP-EGL"])

        if "daily" != self.o.type and not self.o.retest_path:
            # these tests triple the run-time
            all_tests.filter(["dEQP-GLES31.functional.copy_image"])
        
class DeqpBuilder(object):
    def __init__(self):
        self.pm = bs.ProjectMap()
        self.o = bs.Options()
        self.env = {}
        self.version = None
    def build(self):
        pass
    def clean(self):
        pass

    def supports_gles_3(self):
        if ("g33" in self.o.hardware or
            "g45" in self.o.hardware or
            "g965" in self.o.hardware or
            "ilk" in self.o.hardware):
            return False
        return True

    def supports_gles_31(self):
        if not self.supports_gles_3():
            return False
        if "snb" in self.o.hardware:
            return False
        return True

    def test(self):
        if "hsw" in self.o.hardware or "byt" in self.o.hardware or "ivb" in self.o.hardware:
            self.env["MESA_GLES_VERSION_OVERRIDE"] = "3.1"
        t = bs.DeqpTester()
        all_results = bs.DeqpTrie()

        modules = ["gles2", "egl"]
        if self.supports_gles_3():
            modules += ["gles3"]
        if self.supports_gles_31():
            modules += ["gles31"]

        for module in modules:
            binary = self.pm.build_root() + "/opt/deqp/modules/" + module + "/deqp-" + module
            results = t.test(binary,
                             DeqpLister(binary),
                             [],
                             self.env)
            all_results.merge(results)

        config = bs.get_conf_file(self.o.hardware, self.o.arch, project=self.pm.current_project())
        t.generate_results(all_results, bs.ConfigFilter(config, self.o))
        
bs.build(DeqpBuilder(), time_limit=SlowTimeout())
        
