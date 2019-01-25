#!/usr/bin/python
import sys, os, argparse
import multiprocessing
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci"))
import build_support as bs

fs = bs.Fulsim()


class SlowTimeout:
    def __init__(self):
        self.hardware = bs.Options().hardware

    def GetDuration(self):
        # Simulated platforms need more time
        if self.hardware in fs.platform_keyfile:
            return 120
        # all other test suites finish in 10 minutes or less.
        # TODO: put back to 25 when curro's regression is fixed
        return 40


# add the --piglit_test option to the standard options.  Parse the
# options, and strip the piglit_test so the options will work as usual
# for subsequent objects.
o = bs.CustomOptions("piglit args allow a specific test")
o.add_argument(arg='--piglit_test', type=str, default="",
               help="single piglit test to run.")
o.parse_args()

piglit_test = ""
if o.piglit_test:
    piglit_test = o.piglit_test

piglit_timeout = None
if bs.Options().hardware in fs.platform_keyfile:
    if fs.is_supported():
        piglit_timeout = 150
    else:
        print("Unable to run simulated hardware in this environment!")
        sys.exit(1)

jobs = multiprocessing.cpu_count() / 2

excludes = None
if bs.Options().hardware == "tgl":
    excludes = ["dvec3", "dvec4", "dmat"]

# sim-drm.py is invoked by bs.Fulsim.get_env, and requires build_root to be
# populated. To work around this, import build_root now and call bs.build with
# import_build=False so that the build_root is only imported once
bs.Export().import_build_root()

bs.build(bs.PiglitTester(_suite="gpu", env=fs.get_env(),
                         timeout=piglit_timeout, piglit_test=piglit_test,
                         jobs=jobs, excludes=excludes),
         time_limit=SlowTimeout(), import_build=False)
