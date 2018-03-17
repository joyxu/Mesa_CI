#!/usr/bin/python

import os
import sys
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci"))
import build_support as bs


def main():
    # Do not run on older Mesa versions
    if "17" in bs.mesa_version():
        return
    bs.build(bs.AndroidBuilder(src_location="~/android-ia",
                               module="libGLES_mesa"))


if __name__ == '__main__':
    main()
