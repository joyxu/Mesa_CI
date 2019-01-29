#!/usr/bin/python

import sys, os, argparse
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs


class SlowTimeout:
    def __init__(self):
        self.hardware = bs.Options().hardware

    def GetDuration(self):
        if self.hardware == "bsw":
            return 120
        if self.hardware == "byt":
            return 120
        if self.hardware == "glk":
            return 120
        if self.hardware == "bxt":
            return 120
        if self.hardware == "kbl":
            return 120
        if self.hardware == "g33":
            return 120
        if self.hardware == "icl":
            return 120
        if self.hardware == "g965":
            return 50
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

excludes = None
if bs.Options().hardware == "icl":
    excludes = ["dvec3", "dvec4", "dmat"]

env = {}
# Override extensions on icl to enable additional tests
if bs.Options().hardware == 'icl':
    env['MESA_EXTENSION_OVERRIDE'] = ('+GL_ARB_gpu_shader_fp64 '
                                      '+GL_ARB_vertex_attrib_64bit '
                                      '+GL_ARB_gpu_shader_int64 '
                                      '+GL_ARB_shader_ballot')

bs.build(bs.PiglitTester(env=env, piglit_test=piglit_test,
                         excludes=excludes), time_limit=SlowTimeout())
