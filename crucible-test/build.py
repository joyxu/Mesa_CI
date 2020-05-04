#!/usr/bin/env python3
import multiprocessing
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from export import Export
from options import Options
from testers import CrucibleTester
from utils.fulsim import Fulsim
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "repos", "mesa_ci_internal"))
try:
    import internal_build_support.vars as internal_vars
except ModuleNotFoundError:
    internal_vars = None


class SlowTimeout:
    def __init__(self):
        self.hardware = Options().hardware

    def GetDuration(self):
        if "_sim" in self.hardware:
            return 45
        return 25


fs = Fulsim()

if __name__ == "__main__":
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
        else:
            print("Unable to run simulated hardware in this environment!")
            sys.exit(1)
    build(CrucibleTester(env=env, jobs=str(jobs)), time_limit=SlowTimeout())
