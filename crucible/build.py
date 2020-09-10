#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from builders import CrucibleBuilder
from build_support import build


if __name__ == '__main__':
    build(CrucibleBuilder())
