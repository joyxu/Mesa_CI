#!/usr/bin/python

import sys, os, argparse
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

if not os.path.exists(bs.ProjectMap().project_source_dir("mesa") +
                      "/src/gallium/drivers/iris/meson.build"):
    # iris not supported
    sys.exit(0)

bs.build(bs.PiglitTester(env={ "MESA_LOADER_DRIVER_OVERRIDE" : "iris" }))
