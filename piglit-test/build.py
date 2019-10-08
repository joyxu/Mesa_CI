#!/usr/bin/python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from project_map import ProjectMap
from options import Options, CustomOptions
from testers import PiglitTester
from utils.utils import is_soft_fp64


class SlowTimeout:
    def __init__(self):
        self.hardware = Options().hardware

    def GetDuration(self):
        if self.hardware == "bsw":
            return 120
        if self.hardware == "byt":
            return 120
        if self.hardware == "gen9atom":
            return 120
        if self.hardware == "gen9atom_iris":
            return 120
        if self.hardware == "kbl":
            return 120
        if self.hardware == "g33":
            return 120
        if "icl" in self.hardware:
            return 120
        if self.hardware == "g965":
            return 50
        # all other test suites finish in 10 minutes or less.
        # TODO: put back to 25 when curro's regression is fixed
        return 40

def main():
    # add the --piglit_test option to the standard options.  Parse the
    # options, and strip the piglit_test so the options will work as usual
    # for subsequent objects.
    o = CustomOptions("piglit args allow a specific test")
    o.add_argument(arg='--piglit_test', type=str, default="",
                   help="single piglit test to run.")
    o.parse_args()
    test_timeout = None
    hardware = Options().hardware

    piglit_test = ""
    if o.piglit_test:
        piglit_test = o.piglit_test

    excludes = None
    # disable tests fp64-related tests on platforms with soft fp64 when not
    # daily
    if (Options().type != 'daily' and is_soft_fp64(hardware) and not
            Options().retest_path):
        excludes = ["fp64", "dvec", "dmat"]
        test_timeout = 120

    env = {}

    if "iris" in hardware:
        env["MESA_LOADER_DRIVER_OVERRIDE"] = "iris"
        if not test_timeout:
            test_timeout = 600
        if not os.path.exists(ProjectMap().project_source_dir("mesa") +
                              "/src/gallium/drivers/iris/meson.build"):
            # iris not supported
            sys.exit(0)

    build(PiglitTester(env=env, piglit_test=piglit_test,
                       excludes=excludes, timeout=test_timeout),
          time_limit=SlowTimeout())


if __name__ == '__main__':
    main()
