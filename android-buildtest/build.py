#!/usr/bin/env python3

import sys
import os
import multiprocessing
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from builders import AndroidBuilder
from project_map import ProjectMap


def main():
    # Disable test if using < Mesa 18.0
    pm = ProjectMap()
    sd = pm.project_source_dir("mesa")
    if not os.path.exists(os.path.join(sd,
                                       'src/mesa/drivers/osmesa/meson.build')):
        return 0

    build(AndroidBuilder(src_location="~/android-ia",
                         modules=["libGLES_mesa",
                                  "vulkan.broxton"]))


if __name__ == '__main__':
    main()
