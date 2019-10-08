#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from testers import CrucibleTester


if __name__ == "__main__":
    build(CrucibleTester())
