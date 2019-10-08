#!/usr/bin/python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from builders import CMakeBuilder


def main():
    opts = [
        '-DPIGLIT_BUILD_DMA_BUF_TESTS=1',
        '-DPIGLIT_BUILD_GLES1_TESTS=1',
        '-DPIGLIT_BUILD_GLES2_TESTS=1',
        '-DPIGLIT_BUILD_GLES3_TESTS=1',
        '-DPIGLIT_BUILD_GL_TESTS=1',
        '-DPIGLIT_BUILD_GLX_TESTS=1',
        '-DPIGLIT_BUILD_CL_TESTS=0',
    ]

    builder = CMakeBuilder(extra_definitions=opts)

    build(builder)

if __name__ == '__main__':
    main()
