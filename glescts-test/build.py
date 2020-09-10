#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from testers import DeqpTester, DeqpTrie, ConfigFilter
from options import Options
from project_map import ProjectMap
from utils.command import run_batch_command
from utils.utils import (get_libdir, get_libgl_drivers, get_conf_file,
                         get_blacklists)


# needed to preserve case in the options
# class CaseConfig(ConfigParser.SafeConfigParser):
#     def optionxform(self, optionstr):
#         return optionstr

class GLESCTSList(object):
    def __init__(self):
        self.pm = ProjectMap()
        self.o = Options()

    def supports_gles_31(self):
        if ("g33" in self.o.hardware or
            "g45" in self.o.hardware or
            "g965" in self.o.hardware or
            "ilk" in self.o.hardware or
            "snb" in self.o.hardware):
            return False
        return True

    def supports_gles_32(self):
        if not self.supports_gles_31():
            return False

        if ("hsw" in self.o.hardware or
            "bdw" in self.o.hardware or
            "bsw" in self.o.hardware or
            "byt" in self.o.hardware or
            "ivb" in self.o.hardware):
            return False

        # all newer platforms support 3.2
        return True

    def tests(self, env=None):
        br = self.pm.build_root()
        env = {"MESA_GLES_VERSION_OVERRIDE" : "3.2",
               "LD_LIBRARY_PATH" : get_libdir(),
               "MESA_GL_VERSION_OVERRIDE" : "4.6",
               "MESA_GLSL_VERSION_OVERRIDE" : "460",
               "LIBGL_DRIVERS_PATH" : get_libgl_drivers()}
        self.o.update_env(env)

        savedir = os.getcwd()
        os.chdir(self.pm.build_root() + "/bin/es/modules")
        run_batch_command(["./glcts", "--deqp-runmode=xml-caselist"],
                          env=env)

        suites = ["KHR-GLES2-cases.xml", "KHR-GLES3-cases.xml"]

        if self.supports_gles_31():
            suites.append("KHR-GLES31-cases.xml")

        if self.supports_gles_32():
            suites.append("KHR-GLES32-cases.xml")
            suites.append("KHR-GLESEXT-cases.xml")

        all_tests = DeqpTrie()
        for a_list in suites:
            tmp_trie = DeqpTrie()
            tmp_trie.add_xml(a_list)
            all_tests.merge(tmp_trie)

        os.chdir(savedir)
        return all_tests

    def blacklist(self, all_tests):
        blacklist_files = get_blacklists()
        for file in blacklist_files:
            blacklist = DeqpTrie()
            blacklist.add_txt(file)
            all_tests.filter(blacklist)

        return all_tests


class GLESCTSTester(object):
    def __init__(self):
        self.o = Options()
        self.pm = ProjectMap()

    def test(self):
        t = DeqpTester()
        env = {"MESA_GLES_VERSION_OVERRIDE" : "3.2"}
        if "iris" in self.o.hardware:
            env["MESA_LOADER_DRIVER_OVERRIDE"] = "iris"
        results = t.test(self.pm.build_root() + "/bin/es/modules/glcts",
                         GLESCTSList(), env=env)
        o = Options()
        config = get_conf_file(self.o.hardware, self.o.arch,
                               project=self.pm.current_project())
        t.generate_results(results, ConfigFilter(config, o))

    def build(self):
        pass
    def clean(self):
        pass

class SlowTimeout:
    def __init__(self):
        self.hardware = Options().hardware

    def GetDuration(self):
        return 120

if __name__ == '__main__':
    build(GLESCTSTester(), time_limit=SlowTimeout())
