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
        self.env = {}
        if "iris" in self.o.hardware:
            self.env = { "MESA_LOADER_DRIVER_OVERRIDE" : "iris" }
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
                             bs.DeqpSuiteLister(binary),
                             [],
                             self.env)
            all_results.merge(results)

        config = bs.get_conf_file(self.o.hardware, self.o.arch, project=self.pm.current_project())
        t.generate_results(all_results, bs.ConfigFilter(config, self.o))
        
if not os.path.exists(bs.ProjectMap().project_source_dir("mesa") +
                      "/src/gallium/drivers/iris/meson.build"):
    # iris not supported
    if "iris" in bs.Options().hardware:
        sys.exit(0)

bs.build(DeqpBuilder(), time_limit=SlowTimeout())
        
