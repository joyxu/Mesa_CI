#!/usr/bin/python

import multiprocessing
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from export import Export
from project_map import ProjectMap
from options import Options, CustomOptions
from testers import PiglitTester
from utils.fulsim import Fulsim
from utils.utils import is_soft_fp64
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "repos", "mesa_ci_internal"))
try:
    import internal_build_support.vars as internal_vars
except ModuleNotFoundError:
    internal_vars = None

fs = Fulsim()


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
        # Simulated platforms need more time
        if self.hardware in fs.platform_keyfile:
            return 120
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
    env = {}
    hardware = Options().hardware
    jobs = multiprocessing.cpu_count()
    import_build = True
    internal_hardware = ['tgl', 'tgl_sim']
    if internal_vars:
        internal_hardware += internal_vars.internal_hardware
    if "_sim" in hardware and hardware in fs.platform_keyfile:
        if fs.is_supported():
            # sim-drm.py is invoked by Fulsim.get_env, and requires build_root
            # to be populated. To work around this, import build_root now and
            # call build with import_build=False so that the build_root is only
            # imported once
            import_build = False
            Export().import_build_root()
            env.update(fs.get_env())
            jobs = int(multiprocessing.cpu_count() / 2)
            # Limit # of jobs running piglit/simdrm based on system RAM size.
            ram_size = ((os.sysconf('SC_PAGE_SIZE') *
                         os.sysconf('SC_PHYS_PAGES'))/1024**3)
            # ratio of RAM size to job count is taken from stable simdrm
            # servers
            max_jobs = int(ram_size * (3/8))
            if jobs > max_jobs:
                jobs = max_jobs

        else:
            print("Unable to run simulated hardware in this environment!")
            sys.exit(1)
    elif '_sim' not in hardware:
        test_timeout = 300

    piglit_test = ""
    if o.piglit_test:
        piglit_test = o.piglit_test

    excludes = None
    # disable tests fp64-related tests on platforms with soft fp64 when not
    # daily
    if (Options().type != 'daily' and is_soft_fp64(hardware.split('_sim')[0])
            and not Options().retest_path):
        excludes = ["fp64", "dvec", "dmat"]
        test_timeout = 120

    if "iris" in hardware:
        env["MESA_LOADER_DRIVER_OVERRIDE"] = "iris"
        if not test_timeout:
            test_timeout = 600
        if not os.path.exists(ProjectMap().project_source_dir("mesa") +
                              "/src/gallium/drivers/iris/meson.build"):
            # iris not supported
            sys.exit(0)

    build(PiglitTester(env=env, jobs=jobs, timeout=test_timeout,
                       piglit_test=piglit_test, excludes=excludes),
          time_limit=SlowTimeout(), import_build=import_build)


if __name__ == '__main__':
    main()
