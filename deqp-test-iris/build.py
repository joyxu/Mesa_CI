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

        
class DeqpBuilder(object):
    def __init__(self):
        self.pm = bs.ProjectMap()
        self.o = bs.Options()
        self.env = { "MESA_LOADER_DRIVER_OVERRIDE" : "iris" }
        self.version = None
    def build(self):
        pass
    def clean(self):
        pass

    def test(self):
        t = bs.DeqpTester()
        all_results = bs.DeqpTrie()

        for module in ["egl", "gles2", "gles3", "gles31"]:
            binary = self.pm.build_root() + "/opt/deqp/modules/" + module + "/deqp-" + module
            results = t.test(binary,
                             bs.DeqpSuiteLister(binary),
                             [],
                             self.env)
            all_results.merge(results)

        config = bs.get_conf_file(self.o.hardware, self.o.arch, project=self.pm.current_project())
        t.generate_results(all_results, bs.ConfigFilter(config, self.o))
        
if not os.path.exists(bs.ProjectMap().project_source_dir("mesa") +
                      "/src/gallium/drivers/iris/meson.build"):
    # iris not supported
    sys.exit(0)

bs.build(DeqpBuilder(), time_limit=SlowTimeout())
        
