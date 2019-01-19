#!/usr/bin/python

#import ConfigParser
import multiprocessing
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

# needed to preserve case in the options
# class CaseConfig(ConfigParser.SafeConfigParser):
#     def optionxform(self, optionstr):
#         return optionstr


class GLCTSTester(object):
    def __init__(self):
        self.o = bs.Options()
        self.pm = bs.ProjectMap()

    def test(self):
        t = bs.DeqpTester()
        results = t.test(self.pm.build_root() + "/bin/gl/modules/glcts",
                         bs.GLCTSLister(),
                         env = {"MESA_GL_VERSION_OVERRIDE" : "4.6",
                                "MESA_GLSL_VERSION_OVERRIDE" : "460"})

        o = bs.Options()
        config = bs.get_conf_file(self.o.hardware, self.o.arch, project=self.pm.current_project())
        t.generate_results(results, bs.ConfigFilter(config, o))

    def build(self):
        pass
    def clean(self):
        pass

bs.build(GLCTSTester())