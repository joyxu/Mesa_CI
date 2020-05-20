#!/usr/bin/python

import multiprocessing
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from options import Options
from project_map import ProjectMap
from testers import DeqpTester, DeqpTrie, ConfigFilter
from utils.command import run_batch_command
from utils.utils import (is_soft_fp64, mesa_version, get_libdir,
                         get_libgl_drivers, get_conf_file, get_blacklists)


# needed to preserve case in the options
# class CaseConfig(ConfigParser.SafeConfigParser):
#     def optionxform(self, optionstr):
#         return optionstr


class GLCTSLister(object):
    def __init__(self):
        self.pm = ProjectMap()
        self.o = Options()

    def tests(self, env=None):
        br = self.pm.build_root()
        env = {"MESA_GLES_VERSION_OVERRIDE" : "3.2",
               "LD_LIBRARY_PATH" : get_libdir(),
               "LIBGL_DRIVERS_PATH" : get_libgl_drivers(),
               "MESA_GL_VERSION_OVERRIDE" : "4.6",
               "MESA_GLSL_VERSION_OVERRIDE" : "460"}
        self.o.update_env(env)

        savedir = os.getcwd()
        os.chdir(self.pm.build_root() + "/bin/gl/modules")
        run_batch_command(["./glcts", "--deqp-runmode=xml-caselist"],
                          env=env)
        all_tests = DeqpTrie()
        # Enable GL33 tests for supporting hw
        # Note: ilk, g45, etc are all < GL30 and not supported in glcts
        if self.o.hardware in ['snb', 'ivb', 'byt']:
            all_tests.add_xml("KHR-GL33-cases.xml")
            all_tests.add_xml("GTF-GL33-cases.xml")
        else:
            all_tests.add_xml("KHR-GL46-cases.xml")
            all_tests.add_xml("GTF-GL46-cases.xml")
            all_tests.add_xml("KHR-NoContext-cases.xml")
        os.chdir(savedir)
        return all_tests

    def blacklist(self, all_tests):
        blacklist_files = get_blacklists()
        for file in blacklist_files:
            blacklist = DeqpTrie()
            blacklist.add_txt(file)
            all_tests.filter(blacklist)

        return all_tests


class GLCTSTester(object):
    def __init__(self):
        self.o = Options()
        self.pm = ProjectMap()

    def test(self):
        cpus = multiprocessing.cpu_count()
        t = DeqpTester()
        env = {"MESA_GL_VERSION_OVERRIDE" : "4.6",
               "MESA_GLSL_VERSION_OVERRIDE" : "460"}
        if "iris" in self.o.hardware:
            env["MESA_LOADER_DRIVER_OVERRIDE"] = "iris"
        results = t.test(self.pm.build_root() + "/bin/gl/modules/glcts",
                         GLCTSLister(),
                         env=env, cpus=cpus)

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
        if "icl" in self.hardware:
            return 180
        return 120

if __name__ == '__main__':
    if not os.path.exists(ProjectMap().project_source_dir("mesa") +
                          "/src/gallium/drivers/iris/meson.build"):
        # iris not supported
        if "iris" in Options().hardware:
            sys.exit(0)

    build(GLCTSTester(), time_limit=SlowTimeout())
