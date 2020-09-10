#!/usr/bin/python

import glob
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from builders import CMakeBuilder
from build_support import build
from export import Export
from options import Options
from project_map import ProjectMap
from repo_set import checkout_externals
from testers import deqp_external_revisions
from utils.command import run_batch_command


def get_external_revisions(revisions_dict=None):
    return deqp_external_revisions(project="deqp",
                                   revisions_dict=revisions_dict)


class DeqpBuilder(CMakeBuilder):
    def __init__(self, extra_definitions=None, compiler="gcc"):
        CMakeBuilder.__init__(self,
                              extra_definitions=extra_definitions, 
                              compiler=compiler, install=False)
        self._o = Options()
        self._pm = ProjectMap()

    def build(self):
        # set the externals to the required commits
        revisions = get_external_revisions()
        external_dir = (self._pm.project_source_dir('deqp')
                        + "/external/{}/src")
        checkout_externals(project='deqp', revisions=revisions,
                           external_dir_format=external_dir)

        # apply patches if they exist
        for patch in sorted(glob.glob(self._pm.project_build_dir()
                                      + "/*.patch")):
            os.chdir(self._src_dir)
            try:
                run_batch_command(["git", "am", patch])
            except:
                print("WARN: failed to apply patch: " + patch)
                run_batch_command(["git", "am", "--abort"])

        CMakeBuilder.build(self)
        dest = self._pm.build_root() + "/opt/deqp/"
        if not os.path.exists(dest):
            os.makedirs(dest)
        run_batch_command(["rsync", "-rlptD",
                           self._pm.project_source_dir() + "/build_" + self._o.arch + "/modules",
                           dest])
        Export().export()

if __name__ == '__main__':
    build(DeqpBuilder(extra_definitions=["-DDEQP_TARGET=x11_egl",
                                            "-DDEQP_GLES1_LIBRARIES=/tmp/build_root/"
                                            + Options().arch + "/lib/libGL.so"]))

