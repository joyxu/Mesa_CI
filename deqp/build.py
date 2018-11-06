#!/usr/bin/python

import sys, os, importlib, git
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

def get_external_revisions(revisions_dict=None):
    return bs.deqp_external_revisions(project="deqp",
                                      revisions_dict=revisions_dict)

class DeqpBuilder(bs.CMakeBuilder):
    def __init__(self, extra_definitions=None, compiler="gcc"):
        bs.CMakeBuilder.__init__(self,
                                 extra_definitions=extra_definitions, 
                                 compiler=compiler, install=False)
        self._o = bs.Options()
        self._pm = bs.ProjectMap()

    def build(self):
        # set the externals to the required commits
        revisions = get_external_revisions()
        bs.deqp_checkout_externals(project="deqp", revisions=revisions)

        bs.CMakeBuilder.build(self)
        dest = self._pm.build_root() + "/opt/deqp/"
        if not os.path.exists(dest):
            os.makedirs(dest)
        bs.run_batch_command(["rsync", "-rlptD",
                              self._pm.project_source_dir() + "/build_" + self._o.arch + "/modules",
                              dest])
        bs.Export().export()

if __name__ == '__main__':
    bs.build(DeqpBuilder(extra_definitions=["-DDEQP_TARGET=x11_egl",
                                            "-DPYTHON_EXECUTABLE=/usr/bin/python2",
                                            "-DDEQP_GLES1_LIBRARIES=/tmp/build_root/"
                                            + bs.Options().arch + "/lib/libGL.so"]))

