#!/usr/bin/python

import os
import sys
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci"))
import build_support as bs


def main():
    # Disable test if using < Mesa 18.0
    pm = bs.ProjectMap()
    sd = pm.project_source_dir("mesa")
    if not os.path.exists(os.path.join(sd,
                                       'src/mesa/drivers/osmesa/meson.build')):
        return 0
    # The android source tree used does not support Mesa <19.1
    if not os.path.exists(os.path.join(sd,
                                       'docs/relnotes/19.1.0.html')):
        print("Android build test does not support this version of Mesa. No "
              "build test will be performed.")
        return 0

    bs.build(bs.AndroidBuilder(src_location="~/android-ia",
                               module="libGLES_mesa"))


if __name__ == '__main__':
    main()
