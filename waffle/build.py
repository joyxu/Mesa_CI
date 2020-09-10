#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from builders import CMakeBuilder

if __name__ == '__main__':
    build(CMakeBuilder(extra_definitions=["-Dwaffle_has_x11_egl=1",
                                          "-Dwaffle_has_glx=1",
                                          "-Dwaffle_has_gbm=1",
                                          "-Dwaffle_has_wayland=0",
                                          ]))
