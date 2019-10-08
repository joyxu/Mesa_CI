#!/usr/bin/python
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from builders import MesonBuilder
from options import Options


def main():
    if Options().arch != "m64":
        print("Unsupported arch (%s), not building sim-drm!"
              % Options().arch)
        sys.exit(1)
    b = MesonBuilder(install=True)
    build(b)


if __name__ == '__main__':
    main()
